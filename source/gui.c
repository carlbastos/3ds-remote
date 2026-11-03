// citro2d GUI. Top screen: server status and request log. Bottom screen: touch settings.
// All text comes from i18n.c; long translations are scaled down to fit their box.

#include "common.h"

#include <arpa/inet.h>
#include <citro2d.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>

#define TOP_W 400
#define BOT_W 320
#define SCR_H 240

static C3D_RenderTarget *top, *bot;
static C2D_TextBuf tbuf;

// NULL = standard system font (Latin, Cyrillic, Japanese). Chinese and Korean use the
// CHN/KOR/TWN system fonts, loaded the first time they are needed.
static C2D_Font cur_font;
static C2D_Font region_fonts[CFG_REGION_TWN + 1];

static C2D_Font font_for(lang_t l) {
    int region = lang_font_region(l);
    if (region < 0) return NULL;
    if (!region_fonts[region]) region_fonts[region] = C2D_FontLoadSystem((CFG_Region)region);
    return region_fonts[region];   // NULL (standard font) if the load failed
}

// palette
#define COL_BG      C2D_Color32(0x12, 0x18, 0x2b, 0xff)
#define COL_PANEL   C2D_Color32(0x1d, 0x26, 0x40, 0xff)
#define COL_ACCENT  C2D_Color32(0x2f, 0x7d, 0xe1, 0xff)
#define COL_TEXT    C2D_Color32(0xf2, 0xf4, 0xf8, 0xff)
#define COL_MUTED   C2D_Color32(0x8d, 0x98, 0xb3, 0xff)
#define COL_OK      C2D_Color32(0x3c, 0xc4, 0x7c, 0xff)
#define COL_WARN    C2D_Color32(0xf0, 0xa9, 0x2e, 0xff)
#define COL_BAD     C2D_Color32(0xe5, 0x4b, 0x4b, 0xff)
#define COL_BTN     C2D_Color32(0x27, 0x33, 0x55, 0xff)
#define COL_BTN_ON  C2D_Color32(0x35, 0x46, 0x75, 0xff)

static bool show_token;
static char toast[128];
static u64 toast_until;
static u64 confirm_auth_off_until;

// cached system info, refreshed once a second
static u64 info_at;
static u8 batt_pct, batt_lvl, batt_chg, wifi;
static bool have_pct;
static u32 ip;

static void say(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(toast, sizeof toast, fmt, ap);
    va_end(ap);
    utf8_trim(toast);
    toast_until = osGetTime() + 3000;
}

static float text_w(const char *s, float scale) {
    C2D_Text t;
    C2D_TextFontParse(&t, cur_font, tbuf, s);
    float w = 0;
    C2D_TextGetDimensions(&t, scale, scale, &w, NULL);
    return w;
}

// Largest scale <= scale at which s fits in max_w pixels.
static float fit(const char *s, float scale, float max_w) {
    float w = text_w(s, scale);
    return w > max_w ? scale * max_w / w : scale;
}

static void text(float x, float y, float scale, u32 color, const char *fmt, ...) {
    char s[192];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(s, sizeof s, fmt, ap);
    va_end(ap);
    utf8_trim(s);
    C2D_Text t;
    C2D_TextFontParse(&t, cur_font, tbuf, s);
    C2D_TextOptimize(&t);
    C2D_DrawText(&t, C2D_WithColor, x, y, 0.5f, scale, scale, color);
}

// Draws s centred on cx, shrinking it (and nudging it down to stay centred) when wider than max_w.
static void text_center(float cx, float y, float scale, float max_w, u32 color, const char *s) {
    float sc = fit(s, scale, max_w);
    float dy = (scale - sc) * 15;   // keep the shrunken line vertically centred
    text(cx - text_w(s, sc) / 2, y + dy, sc, color, "%s", s);
}

static float pill(float right, float y, const char *label, u32 color) {
    float sc = fit(label, 0.45f, 150);
    float w = text_w(label, sc) + 14;
    C2D_DrawRectSolid(right - w, y, 0.5f, w, 16, color);
    text(right - w + 7, y + 1.5f, sc, COL_BG, "%s", label);
    return w;
}

// ---------------------------------------------------------------- buttons

typedef struct { float x, y, w, h; } rect_t;
enum { B_SHOW, B_NEW, B_SET, B_AUTH, B_PAUSE, B_EXIT, B_LANG, B_COUNT };
static const rect_t buttons[B_COUNT] = {
    {10, 34, 145, 54}, {165, 34, 145, 54},
    {10, 96, 145, 54}, {165, 96, 145, 54},
    {10, 158, 145, 54}, {165, 158, 145, 54},
    {196, 0, 124, 24},   // language chip in the header
};

static int hit(touchPosition t) {
    for (int i = 0; i < B_COUNT; i++) {
        const rect_t *r = &buttons[i];
        if (t.px >= r->x && t.px < r->x + r->w && t.py >= r->y && t.py < r->y + r->h) return i;
    }
    return -1;
}

static void button(int id, const char *l1, const char *l2, u32 l2col, bool pressed) {
    const rect_t *r = &buttons[id];
    C2D_DrawRectSolid(r->x, r->y, 0.5f, r->w, r->h, pressed ? COL_BTN_ON : COL_BTN);
    C2D_DrawRectSolid(r->x, r->y, 0.5f, 3, r->h, COL_ACCENT);
    float cx = r->x + r->w / 2 + 1, maxw = r->w - 14;
    if (l2) {
        text_center(cx, r->y + 9, 0.55f, maxw, COL_TEXT, l1);
        text_center(cx, r->y + 30, 0.45f, maxw, l2col, l2);
    } else {
        text_center(cx, r->y + 18, 0.55f, maxw, COL_TEXT, l1);
    }
}

// ---------------------------------------------------------------- actions

static bool valid_password(const char *s) {
    size_t n = strlen(s);
    if (n < 6 || n > TOKEN_MAX) return false;
    for (; *s; s++)
        if (*s <= ' ' || *s > '~') return false;   // printable ASCII, no spaces (it travels in a header)
    return true;
}

static void set_password(void) {
    SwkbdState kb;
    char buf[TOKEN_MAX + 1] = "";
    swkbdInit(&kb, SWKBD_TYPE_NORMAL, 2, TOKEN_MAX);
    swkbdSetHintText(&kb, tr(S_KB_HINT));
    swkbdSetValidation(&kb, SWKBD_NOTEMPTY_NOTBLANK, 0, 0);
    if (swkbdInputText(&kb, buf, sizeof buf) != SWKBD_BUTTON_CONFIRM) return;
    if (!valid_password(buf)) {
        say("%s", tr(S_T_INVALID_PW));
        return;
    }
    LightLock_Lock(&g.lock);
    snprintf(g.token, sizeof g.token, "%s", buf);
    g.auth_failures = 0;
    LightLock_Unlock(&g.lock);
    config_save();
    say("%s", tr(S_T_PW_CHANGED));
    log_add("%s", tr(S_LOG_PW_CHANGED));
}

static void new_random_password(void) {
    char t[TOKEN_MAX + 1];
    token_generate(t, 12);
    LightLock_Lock(&g.lock);
    snprintf(g.token, sizeof g.token, "%s", t);
    g.auth_failures = 0;
    LightLock_Unlock(&g.lock);
    config_save();
    show_token = true;
    say("%s", tr(S_T_PW_GENERATED));
    log_add("%s", tr(S_LOG_PW_GENERATED));
}

static void toggle_auth(void) {
    u64 now = osGetTime();
    if (g.auth && now > confirm_auth_off_until) {
        confirm_auth_off_until = now + 3000;
        say("%s", tr(S_T_CONFIRM_OFF));
        return;
    }
    LightLock_Lock(&g.lock);
    g.auth = !g.auth;
    LightLock_Unlock(&g.lock);
    confirm_auth_off_until = 0;
    config_save();
    say("%s", tr(g.auth ? S_T_PW_ON : S_T_PW_OFF));
    log_add("%s", tr(g.auth ? S_LOG_PW_ON : S_LOG_PW_OFF));
}

// auto -> pt -> en -> ... -> tw -> auto (dir = +1) or the reverse (dir = -1)
static void cycle_language(int dir) {
    int n = LANG_COUNT + 1;                       // slots: 0 = auto, 1.. = languages
    int slot = (g.lang == LANG_AUTO ? 0 : g.lang + 1);
    slot = (slot + dir + n) % n;
    g.lang = slot == 0 ? LANG_AUTO : (lang_t)(slot - 1);
    config_save();
    if (g.lang == LANG_AUTO) say("%s (%s)", tr(S_LANG_AUTO), LANG_NAME[lang_current()]);
    else say("%s", LANG_NAME[g.lang]);
}

// ---------------------------------------------------------------- frame

static void refresh_info(void) {
    u64 now = osGetTime();
    if (now < info_at) return;
    info_at = now + 1000;
    PTMU_GetBatteryLevel(&batt_lvl);
    PTMU_GetBatteryChargeState(&batt_chg);
    have_pct = have_mcu && R_SUCCEEDED(MCUHWC_GetBatteryLevel(&batt_pct));
    wifi = osGetWifiStrength();
    ip = gethostid();
}

static void draw_top(const state_t *s) {
    C2D_TargetClear(top, COL_BG);
    C2D_SceneBegin(top);

    C2D_DrawRectSolid(0, 0, 0.5f, TOP_W, 26, COL_PANEL);
    text(10, 4, 0.6f, COL_TEXT, "3DS Remote");
    text(10 + text_w("3DS Remote", 0.6f) + 6, 8, 0.42f, COL_MUTED, "v%s", APP_VERSION);
    u64 now = osGetTime();
    if (s->paused) pill(TOP_W - 8, 5, tr(S_PILL_PAUSED), COL_WARN);
    else if (!ip) pill(TOP_W - 8, 5, tr(S_PILL_NO_NET), COL_BAD);
    else if (s->listening) pill(TOP_W - 8, 5, tr(S_PILL_ONLINE), COL_OK);
    else pill(TOP_W - 8, 5, tr(S_PILL_WAITING), COL_WARN);

    // address
    text(14, 36, 0.45f, COL_MUTED, "%s", tr(S_ADDRESS));
    if (ip) {
        struct in_addr a = {.s_addr = ip};
        text(14, 50, 0.85f, COL_TEXT, "%s:%d", inet_ntoa(a), PORT);
    } else {
        text(14, 50, 0.85f, COL_BAD, "%s", tr(S_NO_WIFI));
    }

    // password
    text(14, 86, 0.45f, COL_MUTED, "%s", tr(S_PASSWORD));
    if (!s->auth) text(14, 100, 0.7f, COL_BAD, "%s", tr(S_PW_OFF));
    else if (show_token) text(14, 100, 0.7f, COL_TEXT, "%s", s->token);
    else text(14, 103, 0.7f, COL_TEXT, "************");
    if (s->auth && now < s->locked_until)
        pill(TOP_W - 8, 100, tr(S_PILL_LOCKED), COL_BAD);
    else if (s->auth)
        pill(TOP_W - 8, 100, tr(S_PILL_REQUIRED), COL_OK);

    // system line
    char batt[24], line[160];
    if (have_pct) snprintf(batt, sizeof batt, "%u%%", batt_pct);
    else snprintf(batt, sizeof batt, "%u/5", batt_lvl);
    snprintf(line, sizeof line, "%s %s%s    Wi-Fi %u/3    %s %lu", tr(S_BATTERY), batt,
             batt_chg ? tr(S_CHARGING) : "", wifi, tr(S_REQUESTS), (unsigned long)s->requests);
    text(14, 128, fit(line, 0.45f, TOP_W - 28), COL_MUTED, "%s", line);

    // activity
    if (s->activity[0]) text(14, 144, fit(s->activity, 0.5f, TOP_W - 28), COL_WARN, "%s", s->activity);

    // log
    C2D_DrawRectSolid(8, 164, 0.5f, TOP_W - 16, 70, COL_PANEL);
    int y = 167;
    for (int i = 0; i < 5; i++) {
        const char *entry = s->log[(s->log_next + LOG_LINES - 5 + i) % LOG_LINES];
        if (entry[0]) {
            C2D_Font ui_font = cur_font;   // each line keeps the font of the language it was logged in
            cur_font = font_for(s->log_lang[(s->log_next + LOG_LINES - 5 + i) % LOG_LINES]);
            text(14, y, fit(entry, 0.42f, TOP_W - 28), COL_MUTED, "%s", entry);
            cur_font = ui_font;
            y += 13;
        }
    }
}

static void draw_bottom(const state_t *s, int pressed) {
    C2D_TargetClear(bot, COL_BG);
    C2D_SceneBegin(bot);
    C2D_DrawRectSolid(0, 0, 0.5f, BOT_W, 24, COL_PANEL);
    text(10, 4, fit(tr(S_SETTINGS), 0.55f, 175), COL_TEXT, "%s", tr(S_SETTINGS));

    // language chip: "◀ L  Português  R ▶" reduced to the essentials
    const rect_t *lr = &buttons[B_LANG];
    char chip[48];
    if (s->lang == LANG_AUTO) snprintf(chip, sizeof chip, "L  %s  R", LANG_NAME[lang_current()]);
    else snprintf(chip, sizeof chip, "L  %s  R", LANG_NAME[s->lang]);
    C2D_DrawRectSolid(lr->x, lr->y + 3, 0.5f, lr->w - 6, lr->h - 6, pressed == B_LANG ? COL_BTN_ON : COL_BTN);
    text_center(lr->x + (lr->w - 6) / 2, lr->y + 5, 0.45f, lr->w - 14,
                s->lang == LANG_AUTO ? COL_MUTED : COL_TEXT, chip);

    button(B_SHOW, tr(show_token ? S_HIDE_PW : S_SHOW_PW), "Y", COL_MUTED, pressed == B_SHOW);
    button(B_NEW, tr(S_NEW_PW), tr(S_NEW_PW_SUB), COL_MUTED, pressed == B_NEW);
    button(B_SET, tr(S_SET_PW), tr(S_SET_PW_SUB), COL_MUTED, pressed == B_SET);
    button(B_AUTH, tr(S_REQUIRE_PW), tr(s->auth ? S_ON : S_OFF), s->auth ? COL_OK : COL_BAD, pressed == B_AUTH);
    button(B_PAUSE, tr(s->paused ? S_RESUME : S_PAUSE), tr(S_PAUSE_SUB), COL_MUTED, pressed == B_PAUSE);
    button(B_EXIT, tr(S_EXIT), tr(S_EXIT_SUB), COL_MUTED, pressed == B_EXIT);

    if (osGetTime() < toast_until) {
        C2D_DrawRectSolid(0, SCR_H - 22, 0.5f, BOT_W, 22, COL_ACCENT);
        text_center(BOT_W / 2, SCR_H - 19, 0.45f, BOT_W - 12, COL_TEXT, toast);
    }
}

void gui_init(void) {
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();
    top = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    bot = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);
    tbuf = C2D_TextBufNew(8192);
}

void gui_exit(void) {
    for (size_t i = 0; i < sizeof region_fonts / sizeof *region_fonts; i++)
        if (region_fonts[i]) C2D_FontFree(region_fonts[i]);
    C2D_TextBufDelete(tbuf);
    C2D_Fini();
    C3D_Fini();
}

bool gui_frame(u32 kDown, u32 kHeld) {
    int pressed = -1;
    touchPosition t;
    if (kHeld & KEY_TOUCH) {
        hidTouchRead(&t);
        pressed = hit(t);
    }
    int action = -1;
    if (kDown & KEY_TOUCH) action = pressed;
    if (kDown & KEY_Y) action = B_SHOW;
    if (kDown & KEY_X) action = B_NEW;
    if (kDown & KEY_SELECT) action = B_PAUSE;
    if (kDown & KEY_START) action = B_EXIT;

    switch (action) {
        case B_SHOW: show_token = !show_token; break;
        case B_NEW: new_random_password(); break;
        case B_SET: set_password(); break;
        case B_AUTH: toggle_auth(); break;
        case B_PAUSE:
            g.paused = !g.paused;
            say("%s", tr(g.paused ? S_T_PAUSED : S_T_RESUMED));
            break;
        case B_LANG: cycle_language(+1); break;
        case B_EXIT: return false;
    }
    if (kDown & KEY_R) cycle_language(+1);
    if (kDown & KEY_L) cycle_language(-1);

    refresh_info();
    state_t snap;
    LightLock_Lock(&g.lock);
    memcpy(&snap, &g, sizeof snap);
    LightLock_Unlock(&g.lock);

    cur_font = font_for(lang_current());
    C2D_TextBufClear(tbuf);
    C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
    draw_top(&snap);
    draw_bottom(&snap, pressed);
    C3D_FrameEnd(0);
    return true;
}
