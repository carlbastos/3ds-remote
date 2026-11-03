// Persistent settings (sdmc:/3ds/3ds-remote/config.ini), token generation, request log.

#include "common.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

state_t g;

// No 0/o, 1/l/i: the token is read off the 3DS screen and typed on the Mac.
static const char ALPHABET[] = "abcdefghjkmnpqrstuvwxyz23456789";

void token_generate(char *out, size_t len) {
    u8 rnd[TOKEN_MAX];
    if (len > TOKEN_MAX) len = TOKEN_MAX;
    // ssl:C is the only CSPRNG service in the app's exheader.
    bool ok = R_SUCCEEDED(sslcInit(0)) && R_SUCCEEDED(sslcGenerateRandomData(rnd, len));
    sslcExit();
    if (!ok) {  // fallback: system tick, weak but better than a fixed token
        u64 x = svcGetSystemTick() ^ osGetTime();
        for (size_t i = 0; i < len; i++) {
            x ^= x << 13; x ^= x >> 7; x ^= x << 17;
            rnd[i] = (u8)x;
        }
    }
    for (size_t i = 0; i < len; i++)
        out[i] = ALPHABET[rnd[i] % (sizeof ALPHABET - 1)];
    out[len] = 0;
}

bool token_matches(const char *candidate) {
    // constant time in the length of the stored token
    size_t n = strlen(g.token), m = strlen(candidate);
    unsigned diff = (unsigned)(n ^ m);
    for (size_t i = 0; i < n; i++)
        diff |= (unsigned char)g.token[i] ^ (unsigned char)(i < m ? candidate[i] : 0);
    return diff == 0 && n > 0;
}

void config_save(void) {
    mkdir("sdmc:/3ds", 0777);
    mkdir(CONFIG_DIR, 0777);
    FILE *f = fopen(CONFIG_PATH, "w");
    if (!f) return;
    fprintf(f, "token=%s\nauth=%d\n", g.token, g.auth ? 1 : 0);
    fclose(f);
}

void config_load(void) {
    g.auth = true;
    g.token[0] = 0;
    FILE *f = fopen(CONFIG_PATH, "r");
    if (f) {
        char line[128];
        while (fgets(line, sizeof line, f)) {
            line[strcspn(line, "\r\n")] = 0;
            if (!strncmp(line, "token=", 6) && strlen(line + 6) <= TOKEN_MAX) strcpy(g.token, line + 6);
            else if (!strncmp(line, "auth=", 5)) g.auth = line[5] != '0';
        }
        fclose(f);
    }
    if (strlen(g.token) < 6) {  // first run, or a broken file
        token_generate(g.token, 12);
        config_save();
    }
}

void log_add(const char *fmt, ...) {
    char msg[64];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    LightLock_Lock(&g.lock);
    snprintf(g.log[g.log_next], sizeof g.log[0], "%02d:%02d:%02d %.54s", tm->tm_hour, tm->tm_min, tm->tm_sec, msg);
    g.log_next = (g.log_next + 1) % LOG_LINES;
    LightLock_Unlock(&g.lock);
}

void activity_set(const char *fmt, ...) {
    char msg[64] = "";
    if (fmt) {
        va_list ap;
        va_start(ap, fmt);
        vsnprintf(msg, sizeof msg, fmt, ap);
        va_end(ap);
    }
    LightLock_Lock(&g.lock);
    snprintf(g.activity, sizeof g.activity, "%s", msg);
    LightLock_Unlock(&g.lock);
}
