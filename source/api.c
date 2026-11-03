// HTTP API: authentication gate, routing and the endpoint handlers.

#include "http.h"

#include <arpa/inet.h>
#include <dirent.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_FAILURES 5
#define LOCKOUT_MS   30000

// ---------------------------------------------------------------- helpers

static FS_MediaType media_param(const char *q) {
    char m[8] = "sd";
    get_param(q, "media", m, sizeof m);
    if (!strcmp(m, "nand")) return MEDIATYPE_NAND;
    if (!strcmp(m, "card")) return MEDIATYPE_GAME_CARD;
    return MEDIATYPE_SD;
}

static bool tid_param(const char *q, u64 *tid) {
    char t[24];
    if (!get_param(q, "tid", t, sizeof t)) return false;
    char *e;
    *tid = strtoull(t, &e, 16);
    return *e == 0 && *tid != 0;
}

static const char *title_kind(u64 tid) {
    switch ((u32)(tid >> 32)) {
        case 0x00040000: return "app";
        case 0x00040002: return "demo";
        case 0x0004000E: return "update";
        case 0x0004008C: return "dlc";
        case 0x00040010: return "system-app";
        case 0x00040030: return "applet";
        case 0x0004001B: return "system-data";
        case 0x00040130: return "system-module";
        case 0x00040138: return "firmware";
        default:         return "other";
    }
}

// Reads the English (fallback: Japanese) short title from the title's SMDH.
static bool title_name(u64 tid, FS_MediaType mt, char *out, size_t outsz, Result *err) {
    static const u32 filePath[5] = {0x0, 0x0, 0x2, 0x6E6F6369 /* "icon" */, 0x0};
    u32 archPath[4] = {(u32)tid, (u32)(tid >> 32), mt, 0};
    FS_Path ap = {PATH_BINARY, sizeof archPath, archPath};
    FS_Path fp = {PATH_BINARY, sizeof filePath, filePath};
    Handle h;
    *err = FSUSER_OpenFileDirectly(&h, ARCHIVE_SAVEDATA_AND_CONTENT, ap, fp, FS_OPEN_READ, 0);
    if (R_FAILED(*err)) return false;
    u8 *smdh = malloc(0x36C0);
    u32 rd = 0;
    Result r = FSFILE_Read(h, &rd, 0, smdh, 0x36C0);
    FSFILE_Close(h);
    bool ok = false;
    if (R_FAILED(r)) *err = r;
    else if (rd < 0x2008 || memcmp(smdh, "SMDH", 4)) *err = -2;
    if (R_SUCCEEDED(r) && rd >= 0x2008 && !memcmp(smdh, "SMDH", 4)) {
        u16 name[0x41] = {0};
        for (int lang = 1; lang >= 0 && !name[0]; lang--)  // 1 = English, 0 = Japanese
            memcpy(name, smdh + 8 + lang * 0x200, 0x80);
        ssize_t n = utf16_to_utf8((u8 *)out, name, outsz - 1);
        out[n > 0 ? n : 0] = 0;
        ok = n > 0;
    }
    free(smdh);
    return ok;
}

// Accepts absolute SD paths without ".." segments; the config file (holds the token) is off limits.
static bool sd_path(const char *q, char *out, size_t outsz) {
    char p[512];
    if (!get_param(q, "path", p, sizeof p) || p[0] != '/' || strchr(p, '\\')) return false;
    for (const char *s = p + 1; *s;) {
        size_t n = strcspn(s, "/");
        if (n == 2 && s[0] == '.' && s[1] == '.') return false;
        s += n;
        if (*s == '/') s++;
    }
    snprintf(out, outsz, "sdmc:%s", p);
    return strcasecmp(out, CONFIG_PATH) != 0 && strcasecmp(out, OLD_CONFIG_DIR "/config.ini") != 0;
}

static void mkdirs(const char *path) {  // creates every parent of path
    char tmp[600];
    snprintf(tmp, sizeof tmp, "%s", path);
    for (char *p = tmp + 6; *p; p++) {   // skip "sdmc:/"
        if (*p == '/') { *p = 0; mkdir(tmp, 0777); *p = '/'; }
    }
}

// ---------------------------------------------------------------- handlers

static void h_status(int fd) {
    static const char *models[] = {"Old 3DS", "Old 3DS XL", "New 3DS", "Old 2DS", "New 3DS XL", "New 2DS XL"};
    buf_t b = {0};
    u8 lvl = 0, chg = 0, pct = 0, model = 0xFF;
    PTMU_GetBatteryLevel(&lvl);
    PTMU_GetBatteryChargeState(&chg);
    b_printf(&b, "{\"server\":\"%s\",\"auth\":%s,\"battery\":{\"level\":%u,\"charging\":%s", APP_VERSION, g.auth ? "true" : "false", lvl, chg ? "true" : "false");
    if (have_mcu && R_SUCCEEDED(MCUHWC_GetBatteryLevel(&pct))) b_printf(&b, ",\"percent\":%u", pct);
    b_put(&b, "}", 1);

    b_printf(&b, ",\"wifi_strength\":%u", osGetWifiStrength());
    struct in_addr ip = {.s_addr = gethostid()};
    b_printf(&b, ",\"ip\":\"%s\"", inet_ntoa(ip));

    FS_ArchiveResource res;
    if (R_SUCCEEDED(FSUSER_GetArchiveResource(&res, SYSTEM_MEDIATYPE_SD)))
        b_printf(&b, ",\"sd\":{\"free\":%llu,\"total\":%llu}",
                 (u64)res.freeClusters * res.clusterSize, (u64)res.totalClusters * res.clusterSize);

    if (R_SUCCEEDED(CFGU_GetSystemModel(&model)) && model < 6)
        b_printf(&b, ",\"model\":\"%s\"", models[model]);

    OS_VersionBin nver, cver;
    char sv[64];
    if (R_SUCCEEDED(osGetSystemVersionDataString(&nver, &cver, sv, sizeof sv)))
        b_printf(&b, ",\"system_version\":\"%s\"", sv);

    s64 luma = 0;
    if (R_SUCCEEDED(svcGetSystemInfo(&luma, 0x10000, 0)) && luma)
        b_printf(&b, ",\"luma\":\"%u.%u.%u\"", (u32)(luma >> 24) & 0xFF, (u32)(luma >> 16) & 0xFF, (u32)(luma >> 8) & 0xFF);

    b_put(&b, "}", 1);
    send_json(fd, 200, &b);
    free(b.d);
}

static void h_titles(int fd, req_t *rq) {
    FS_MediaType mt = media_param(rq->query);
    u32 count = 0, got = 0;
    Result r = AM_GetTitleCount(mt, &count);
    if (R_FAILED(r)) { send_err(fd, 500, "AM_GetTitleCount failed", r); return; }
    u64 *ids = calloc(count ? count : 1, sizeof(u64));
    AM_TitleInfo *info = calloc(count ? count : 1, sizeof(AM_TitleInfo));
    r = AM_GetTitleList(&got, mt, count, ids);
    if (R_FAILED(r)) { free(ids); free(info); send_err(fd, 500, "AM_GetTitleList failed", r); return; }
    bool haveInfo = R_SUCCEEDED(AM_GetTitleInfo(mt, got, ids, info));

    buf_t b = {0};
    b_put(&b, "[", 1);
    for (u32 i = 0; i < got; i++) {
        u64 tid = ids[i];
        const char *kind = title_kind(tid);
        b_printf(&b, "%s\n{\"tid\":\"%016llX\",\"kind\":\"%s\"", i ? "," : "", tid, kind);
        char pc[16] = {0};
        if (R_SUCCEEDED(AM_GetTitleProductCode(mt, tid, pc)) && pc[0]) {
            pc[15] = 0;
            b_put(&b, ",\"product\":", 11);
            b_str(&b, pc);
        }
        if (haveInfo) b_printf(&b, ",\"size\":%llu,\"version\":%u", info[i].size, info[i].version);
        if (!strcmp(kind, "app") || !strcmp(kind, "demo") || !strcmp(kind, "system-app")) {
            char name[200];
            Result nerr = 0;
            if (title_name(tid, mt, name, sizeof name, &nerr)) {
                b_put(&b, ",\"name\":", 8);
                b_str(&b, name);
            } else {
                b_printf(&b, ",\"name_error\":\"0x%08lX\"", (unsigned long)nerr);
            }
        }
        b_put(&b, "}", 1);
    }
    b_put(&b, "]", 1);
    free(ids);
    free(info);
    send_json(fd, 200, &b);
    free(b.d);
}

static Result cia_err;
static u64 cia_err_off;

static bool cia_sink(void *ctx, u64 off, const void *data, u32 len) {
    u32 w = 0;
    Result r = FSFILE_Write(*(Handle *)ctx, &w, off, data, len, 0);
    if (R_FAILED(r) || w != len) {
        cia_err = R_FAILED(r) ? r : -1;
        cia_err_off = off;
        return false;
    }
    return true;
}

static void h_install(int fd, req_t *rq) {
    if (rq->clen <= 0) { send_err(fd, 400, "missing Content-Length", 0); return; }
    FS_MediaType mt = media_param(rq->query);
    Handle cia;
    Result r = AM_StartCiaInstall(mt, &cia);
    if (R_FAILED(r)) { send_err(fd, 500, "AM_StartCiaInstall failed", r); return; }
    log_add(tr(S_LOG_INSTALLING), rq->clen >> 20);
    cia_err = 0;
    long long got = recv_body(fd, rq, cia_sink, &cia, tr(S_ACT_INSTALLING));
    if (got != rq->clen) {
        AM_CancelCIAInstall(cia);
        char msg[96];
        if (got < 0) snprintf(msg, sizeof msg, "AM write failed at offset %llu", cia_err_off);
        else snprintf(msg, sizeof msg, "connection ended early");
        log_add(tr(S_LOG_INSTALL_FAILED), cia_err);
        send_err(fd, 500, msg, got < 0 ? cia_err : 0);
        return;
    }
    r = AM_FinishCiaInstall(cia);
    if (R_FAILED(r)) { log_add(tr(S_LOG_INSTALL_FAILED), r); send_err(fd, 500, "AM_FinishCiaInstall failed", r); return; }
    log_add("%s", tr(S_LOG_INSTALLED));
    send_ok(fd);
}

static void h_delete(int fd, req_t *rq) {
    u64 tid;
    if (!tid_param(rq->query, &tid)) { send_err(fd, 400, "tid required (hex)", 0); return; }
    Result r = AM_DeleteTitle(media_param(rq->query), tid);
    if (R_FAILED(r)) { send_err(fd, 500, "AM_DeleteTitle failed", r); return; }
    log_add(tr(S_LOG_DELETED), tid);
    send_ok(fd);
}

static void h_ls(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required: absolute, no \"..\"", 0); return; }
    DIR *d = opendir(path);
    if (!d) { send_err(fd, 404, strerror(errno), 0); return; }
    buf_t b = {0};
    b_put(&b, "[", 1);
    bool first = true;
    struct dirent *e;
    while ((e = readdir(d))) {
        if (!strcmp(e->d_name, ".") || !strcmp(e->d_name, "..")) continue;
        char full[900];
        struct stat st;
        snprintf(full, sizeof full, "%s/%s", path, e->d_name);
        bool ok = stat(full, &st) == 0;
        b_put(&b, first ? "\n{\"name\":" : ",\n{\"name\":", first ? 9 : 10);
        b_str(&b, e->d_name);
        bool isdir = e->d_type == DT_DIR || (ok && S_ISDIR(st.st_mode));
        b_printf(&b, ",\"dir\":%s,\"size\":%lld}", isdir ? "true" : "false",
                 ok ? (long long)st.st_size : 0LL);
        first = false;
    }
    closedir(d);
    b_put(&b, "]", 1);
    send_json(fd, 200, &b);
    free(b.d);
}

static void h_file_get(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required: absolute, no \"..\"", 0); return; }
    FILE *f = fopen(path, "rb");
    if (!f) { send_err(fd, 404, strerror(errno), 0); return; }
    fseek(f, 0, SEEK_END);
    long long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    send_head(fd, 200, "application/octet-stream", len);
    char *buf = malloc(CHUNK);
    size_t n;
    while ((n = fread(buf, 1, CHUNK, f)) > 0)
        if (!send_all(fd, buf, n)) break;
    free(buf);
    fclose(f);
}

static bool file_sink(void *ctx, u64 off, const void *data, u32 len) {
    return fwrite(data, 1, len, (FILE *)ctx) == len;
}

static void h_file_put(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required: absolute, no \"..\"", 0); return; }
    mkdirs(path);
    FILE *f = fopen(path, "wb");
    if (!f) { send_err(fd, 500, strerror(errno), 0); return; }
    setvbuf(f, NULL, _IOFBF, CHUNK);
    long long got = rq->clen > 0 ? recv_body(fd, rq, file_sink, f, tr(S_ACT_RECEIVING)) : 0;
    bool closed = fclose(f) == 0;
    if (got != rq->clen || !closed) { remove(path); send_err(fd, 500, "upload incomplete", 0); return; }
    send_ok(fd);
}

static void h_file_delete(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required: absolute, no \"..\"", 0); return; }
    struct stat st;
    if (stat(path, &st) != 0) { send_err(fd, 404, strerror(errno), 0); return; }
    if ((S_ISDIR(st.st_mode) ? rmdir(path) : remove(path)) != 0) { send_err(fd, 500, strerror(errno), 0); return; }
    send_ok(fd);
}

// ---------------------------------------------------------------- main

// ---------------------------------------------------------------- auth + routing

static void h_ping(int fd) {
    buf_t b = {0};
    b_printf(&b, "{\"app\":\"3ds-remote\",\"version\":\"%s\",\"auth\":%s}", APP_VERSION, g.auth ? "true" : "false");
    send_json(fd, 200, &b);
    free(b.d);
}

// Returns true when the request may proceed; otherwise the response has been sent.
static bool authorize(int fd, req_t *rq) {
    u64 now = osGetTime();
    LightLock_Lock(&g.lock);
    bool required = g.auth;
    bool locked = now < g.locked_until;
    bool ok = !required || (!locked && token_matches(rq->token));
    bool lock_now = false;
    if (required && !locked) {
        if (ok) g.auth_failures = 0;
        else if (++g.auth_failures >= MAX_FAILURES) {
            g.locked_until = now + LOCKOUT_MS;
            g.auth_failures = 0;
            lock_now = true;
        }
    }
    LightLock_Unlock(&g.lock);

    if (ok) return true;
    if (lock_now) log_add(tr(S_LOG_LOCKED), MAX_FAILURES, LOCKOUT_MS / 1000);
    if (locked || lock_now) send_err(fd, 429, "too many failed logins; try again in 30s", 0);
    else send_err(fd, 401, rq->token[0] ? "wrong token" : "token required", 0);
    return false;
}

void api_handle(int fd, u32 client_ip) {
    static char hdr[HDR_MAX];
    req_t rq = {0};
    last_status = 0;
    if (!read_request(fd, &rq, hdr)) return;

    LightLock_Lock(&g.lock);
    g.requests++;
    LightLock_Unlock(&g.lock);

    bool get = !strcmp(rq.method, "GET"), post = !strcmp(rq.method, "POST");
    const char *p = rq.path;

    if (get && !strcmp(p, "/ping")) h_ping(fd);
    else if (!authorize(fd, &rq)) { /* response already sent */ }
    else if (get && !strcmp(p, "/status")) h_status(fd);
    else if (get && !strcmp(p, "/titles")) h_titles(fd, &rq);
    else if (post && !strcmp(p, "/install")) h_install(fd, &rq);
    else if (post && !strcmp(p, "/delete")) h_delete(fd, &rq);
    else if (get && !strcmp(p, "/ls")) h_ls(fd, &rq);
    else if (!strcmp(p, "/file")) {
        if (get) h_file_get(fd, &rq);
        else if (!strcmp(rq.method, "PUT")) h_file_put(fd, &rq);
        else if (!strcmp(rq.method, "DELETE")) h_file_delete(fd, &rq);
        else send_err(fd, 400, "use GET, PUT or DELETE", 0);
    }
    else if (post && !strcmp(p, "/launch")) {
        u64 tid;
        if (!tid_param(rq.query, &tid)) send_err(fd, 400, "tid required (hex)", 0);
        else {
            g.launch_tid = tid;
            g.launch_mt = media_param(rq.query);
            send_ok(fd);
            g.pending = ACT_LAUNCH;
        }
    }
    else if (post && !strcmp(p, "/reboot"))   { send_ok(fd); g.pending = ACT_REBOOT; }
    else if (post && !strcmp(p, "/shutdown")) { send_ok(fd); g.pending = ACT_SHUTDOWN; }
    else if (post && !strcmp(p, "/exit"))     { send_ok(fd); g.pending = ACT_EXIT; }
    else send_err(fd, 404, "unknown endpoint", 0);

    struct in_addr ip = {.s_addr = client_ip};
    const char *ipstr = inet_ntoa(ip);
    const char *dot = strrchr(ipstr, '.');   // the subnet is always the same; show only the host part
    log_add(".%s %s %s %d", dot ? dot + 1 : ipstr, rq.method, rq.path, last_status);
}
