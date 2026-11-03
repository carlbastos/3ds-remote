#pragma once

#include <3ds.h>
#include <stdbool.h>
#include <stddef.h>

#include "i18n.h"

#define PORT        8080   // 8000/8001 belong to NTR remote play
#define CHUNK       0x20000
#define HDR_MAX     8192
#define TOKEN_MAX   32
#define LOG_LINES   8
#define CONFIG_DIR  "sdmc:/config/3ds-remote"
#define OLD_CONFIG_DIR "sdmc:/3ds/3ds-remote"   // used up to v0.2.0
#define CONFIG_PATH CONFIG_DIR "/config.ini"

// Requests from the network that only the main thread may carry out.
enum { ACT_NONE, ACT_EXIT, ACT_REBOOT, ACT_SHUTDOWN, ACT_LAUNCH };

typedef struct {
    LightLock lock;

    // persisted in config.ini
    char token[TOKEN_MAX + 1];
    bool auth;              // require the token on every request except /ping
    lang_t lang;            // LANG_AUTO follows the system language

    // runtime
    bool paused;            // listening socket closed on purpose
    bool listening;         // socket currently bound
    u32 requests;
    u32 auth_failures;      // consecutive failed logins
    u64 locked_until;       // osGetTime() ms; logins refused until then
    char activity[96];      // e.g. "Instalando CIA 42%"
    char log[LOG_LINES][96];
    lang_t log_lang[LOG_LINES];   // language each line was written in (picks the font)
    int log_next;

    // main-thread actions
    volatile int pending;
    u64 launch_tid;
    FS_MediaType launch_mt;
    volatile bool quit;
} state_t;

extern state_t g;
extern bool have_mcu, have_ptmsysm;

// config.c
void config_load(void);
void config_save(void);
void token_generate(char *out, size_t len);
bool token_matches(const char *candidate);
void log_add(const char *fmt, ...);
void activity_set(const char *fmt, ...);
void utf8_trim(char *s);   // drops a multibyte sequence cut off by truncation

// server.c
void server_start(void);
void server_stop(void);

// api.c
void api_handle(int fd, u32 client_ip);

// gui.c
void gui_init(void);
void gui_exit(void);
bool gui_frame(u32 kDown, u32 kHeld);   // false when the user asked to quit
