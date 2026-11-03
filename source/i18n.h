#pragma once

// UI languages. LANG_AUTO follows the console's system language.
typedef enum {
    LANG_AUTO = -1,
    LANG_PT, LANG_EN, LANG_ES, LANG_RU, LANG_JA,
    LANG_FR, LANG_DE, LANG_IT, LANG_NL, LANG_ZH, LANG_KO, LANG_TW,
    LANG_COUNT
} lang_t;

typedef enum {
    // top screen
    S_ADDRESS, S_PASSWORD, S_NO_WIFI, S_PW_OFF,
    S_PILL_PAUSED, S_PILL_NO_NET, S_PILL_ONLINE, S_PILL_WAITING, S_PILL_LOCKED, S_PILL_REQUIRED,
    S_BATTERY, S_CHARGING, S_REQUESTS,
    // bottom screen
    S_SETTINGS, S_SHOW_PW, S_HIDE_PW, S_NEW_PW, S_NEW_PW_SUB, S_SET_PW, S_SET_PW_SUB,
    S_REQUIRE_PW, S_ON, S_OFF, S_PAUSE, S_RESUME, S_PAUSE_SUB, S_EXIT, S_EXIT_SUB, S_LANG_AUTO,
    // toasts and keyboard
    S_T_INVALID_PW, S_T_PW_CHANGED, S_T_PW_GENERATED, S_T_CONFIRM_OFF, S_T_PW_ON, S_T_PW_OFF,
    S_T_PAUSED, S_T_RESUMED, S_KB_HINT,
    // activity line
    S_ACT_INSTALLING, S_ACT_RECEIVING,
    // request log (printf formats)
    S_LOG_STARTED, S_LOG_PW_CHANGED, S_LOG_PW_GENERATED, S_LOG_PW_ON, S_LOG_PW_OFF, S_LOG_LOCKED,
    S_LOG_INSTALLING, S_LOG_INSTALL_FAILED, S_LOG_INSTALLED, S_LOG_DELETED, S_LOG_REBOOTING,
    S_LOG_SHUTTING_DOWN, S_LOG_LAUNCHING, S_LOG_LAUNCH_FAILED, S_LOG_SOC_FAILED, S_LOG_THREAD_FAILED,
    S_COUNT
} str_t;

extern const char *const LANG_CODE[LANG_COUNT];   // "pt", "en", ...
extern const char *const LANG_NAME[LANG_COUNT];   // "Português", "English", ...

lang_t lang_from_system(void);
lang_t lang_parse(const char *code);   // LANG_AUTO for "auto" or anything unknown
lang_t lang_current(void);             // resolved: never LANG_AUTO
const char *tr(str_t id);
int lang_font_region(lang_t l);       // CFG_REGION_* font a language needs, or -1
