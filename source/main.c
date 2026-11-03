// 3ds-remote: small HTTP/JSON control server for a 3DS running Luma3DS.
//
// Endpoints (port 8080):
//   GET    /status                       battery, wifi, SD space, model, firmware, Luma version
//   GET    /titles?media=sd|nand|card    installed titles with name, product code, size, version
//   POST   /install?media=sd             body = raw CIA, streamed straight into AM
//   POST   /delete?tid=HEX&media=sd      uninstall a title
//   POST   /launch?tid=HEX&media=sd      jump to a title (this app exits)
//   GET    /ls?path=/dir                 list an SD directory
//   GET    /file?path=/x                 download an SD file
//   PUT    /file?path=/x                 upload an SD file (parents created)
//   DELETE /file?path=/x                 delete an SD file or empty dir
//   POST   /reboot | /shutdown | /exit

#include <3ds.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <malloc.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT        8080   // 8000/8001 belong to NTR remote play
#define SOC_BUFSIZE 0x100000
#define CHUNK       0x20000
#define HDR_MAX     8192

// ---------------------------------------------------------------- buffers

typedef struct { char *d; size_t n, cap; } buf_t;

static void b_put(buf_t *b, const char *s, size_t n) {
    if (b->n + n + 1 > b->cap) {
        size_t c = b->cap ? b->cap : 1024;
        while (c < b->n + n + 1) c *= 2;
        b->d = realloc(b->d, c);
        b->cap = c;
    }
    memcpy(b->d + b->n, s, n);
    b->n += n;
    b->d[b->n] = 0;
}

static void b_printf(buf_t *b, const char *fmt, ...) {
    char tmp[512];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if ((size_t)n < sizeof tmp) { b_put(b, tmp, n); return; }
    char *big = malloc(n + 1);
    va_start(ap, fmt);
    vsnprintf(big, n + 1, fmt, ap);
    va_end(ap);
    b_put(b, big, n);
    free(big);
}

static void b_str(buf_t *b, const char *s) {
    b_put(b, "\"", 1);
    for (; *s; s++) {
        unsigned char c = *s;
        if (c == '"' || c == '\\') { char e[2] = {'\\', c}; b_put(b, e, 2); }
        else if (c < 0x20) { char e[8]; snprintf(e, sizeof e, "\\u%04x", c); b_put(b, e, 6); }
        else b_put(b, (const char *)&c, 1);
    }
    b_put(b, "\"", 1);
}

// ---------------------------------------------------------------- http

typedef struct {
    char method[8];
    char path[256];
    char query[1024];
    long long clen;
    char *body0;        // body bytes already read together with the header
    size_t body0len;
} req_t;

static bool send_all(int fd, const void *data, size_t n) {
    const char *p = data;
    while (n) {
        ssize_t s = send(fd, p, n > CHUNK ? CHUNK : n, 0);
        if (s <= 0) return false;
        p += s;
        n -= s;
    }
    return true;
}

static void send_head(int fd, int code, const char *ctype, long long len) {
    const char *msg = code == 200 ? "OK" : code == 400 ? "Bad Request" : code == 404 ? "Not Found" : "Error";
    char h[256];
    int n = snprintf(h, sizeof h,
        "HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %lld\r\nConnection: close\r\n\r\n",
        code, msg, ctype, len);
    send_all(fd, h, n);
}

static void send_json(int fd, int code, buf_t *b) {
    b_put(b, "\n", 1);
    send_head(fd, code, "application/json", b->n);
    send_all(fd, b->d, b->n);
}

static void send_err(int fd, int code, const char *what, Result r) {
    buf_t b = {0};
    b_put(&b, "{\"error\":", 9);
    b_str(&b, what);
    if (r) b_printf(&b, ",\"result\":\"0x%08lX\"", (unsigned long)r);
    b_put(&b, "}", 1);
    send_json(fd, code, &b);
    free(b.d);
}

static void send_ok(int fd) {
    buf_t b = {0};
    b_put(&b, "{\"ok\":true}", 11);
    send_json(fd, 200, &b);
    free(b.d);
}

static int hexval(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

// Finds key in the query string and url-decodes its value into out.
static bool get_param(const char *q, const char *key, char *out, size_t outsz) {
    size_t kl = strlen(key);
    const char *p = q;
    while (p && *p) {
        if (!strncmp(p, key, kl) && p[kl] == '=') {
            p += kl + 1;
            size_t o = 0;
            while (*p && *p != '&' && o + 1 < outsz) {
                if (*p == '%' && hexval(p[1]) >= 0 && hexval(p[2]) >= 0) {
                    out[o++] = (char)(hexval(p[1]) * 16 + hexval(p[2]));
                    p += 3;
                } else {
                    out[o++] = *p == '+' ? ' ' : *p;
                    p++;
                }
            }
            out[o] = 0;
            return true;
        }
        p = strchr(p, '&');
        if (p) p++;
    }
    return false;
}

static bool read_request(int fd, req_t *rq, char *hdr) {
    size_t n = 0;
    char *end = NULL;
    while (!end) {
        if (n >= HDR_MAX - 1) return false;
        ssize_t r = recv(fd, hdr + n, HDR_MAX - 1 - n, 0);
        if (r <= 0) return false;
        n += r;
        hdr[n] = 0;
        end = strstr(hdr, "\r\n\r\n");
    }
    *end = 0;
    rq->body0 = end + 4;
    rq->body0len = n - (size_t)(rq->body0 - hdr);

    char target[1300] = {0};
    if (sscanf(hdr, "%7s %1299s", rq->method, target) != 2) return false;
    char *qm = strchr(target, '?');
    rq->query[0] = 0;
    if (qm) {
        *qm = 0;
        snprintf(rq->query, sizeof rq->query, "%s", qm + 1);
    }
    snprintf(rq->path, sizeof rq->path, "%s", target);

    rq->clen = 0;
    for (char *line = strstr(hdr, "\r\n"); line; line = strstr(line + 2, "\r\n")) {
        if (!strncasecmp(line + 2, "Content-Length:", 15))
            rq->clen = strtoll(line + 17, NULL, 10);
    }
    return true;
}

// Calls sink() for every body chunk (header leftovers first). Returns bytes received.
typedef bool (*sink_fn)(void *ctx, u64 off, const void *data, u32 len);

static long long recv_body(int fd, req_t *rq, sink_fn sink, void *ctx, const char *label) {
    u64 off = 0;
    int lastpct = -1;
    bool failed = false;
    if (rq->body0len) {
        size_t take = rq->body0len > (size_t)rq->clen ? (size_t)rq->clen : rq->body0len;
        failed = !sink(ctx, 0, rq->body0, take);
        off = take;
    }
    char *buf = memalign(0x1000, CHUNK);
    if (!buf) return -1;
    while ((long long)off < rq->clen) {
        long long want = rq->clen - off;
        ssize_t r = recv(fd, buf, want > CHUNK ? CHUNK : want, 0);
        if (r <= 0) break;
        if (!failed && !sink(ctx, off, buf, r)) failed = true;
        off += r;
        int pct = (int)(off * 100 / rq->clen);
        if (pct / 10 != lastpct / 10) {
            printf("\r  %s %3d%% (%llu MB)  ", label, pct, off >> 20);
            lastpct = pct;
        }
    }
    printf("\n");
    free(buf);
    return failed ? -1 : (long long)off;
}

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

static bool sd_path(const char *q, char *out, size_t outsz) {
    char p[512];
    if (!get_param(q, "path", p, sizeof p) || p[0] != '/') return false;
    snprintf(out, outsz, "sdmc:%s", p);
    return true;
}

static void mkdirs(const char *path) {  // creates every parent of path
    char tmp[600];
    snprintf(tmp, sizeof tmp, "%s", path);
    for (char *p = tmp + 6; *p; p++) {   // skip "sdmc:/"
        if (*p == '/') { *p = 0; mkdir(tmp, 0777); *p = '/'; }
    }
}

// ---------------------------------------------------------------- handlers

static bool have_mcu, have_ptmsysm;

static void h_status(int fd) {
    static const char *models[] = {"Old 3DS", "Old 3DS XL", "New 3DS", "Old 2DS", "New 3DS XL", "New 2DS XL"};
    buf_t b = {0};
    u8 lvl = 0, chg = 0, pct = 0, model = 0xFF;
    PTMU_GetBatteryLevel(&lvl);
    PTMU_GetBatteryChargeState(&chg);
    b_printf(&b, "{\"server\":\"%s\",\"battery\":{\"level\":%u,\"charging\":%s", APP_VERSION, lvl, chg ? "true" : "false");
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
    printf("Installing CIA (%lld MB)\n", rq->clen >> 20);
    cia_err = 0;
    long long got = recv_body(fd, rq, cia_sink, &cia, "install");
    if (got != rq->clen) {
        AM_CancelCIAInstall(cia);
        char msg[96];
        if (got < 0) snprintf(msg, sizeof msg, "AM write failed at offset %llu", cia_err_off);
        else snprintf(msg, sizeof msg, "connection ended early");
        printf("  install aborted: %s (%08lX)\n", msg, cia_err);
        send_err(fd, 500, msg, got < 0 ? cia_err : 0);
        return;
    }
    r = AM_FinishCiaInstall(cia);
    if (R_FAILED(r)) { printf("  finish failed %08lX\n", r); send_err(fd, 500, "AM_FinishCiaInstall failed", r); return; }
    printf("  installed\n");
    send_ok(fd);
}

static void h_delete(int fd, req_t *rq) {
    u64 tid;
    if (!tid_param(rq->query, &tid)) { send_err(fd, 400, "tid required (hex)", 0); return; }
    Result r = AM_DeleteTitle(media_param(rq->query), tid);
    if (R_FAILED(r)) { send_err(fd, 500, "AM_DeleteTitle failed", r); return; }
    printf("Deleted %016llX\n", tid);
    send_ok(fd);
}

static void h_ls(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required, starting with /", 0); return; }
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
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required, starting with /", 0); return; }
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
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required, starting with /", 0); return; }
    mkdirs(path);
    FILE *f = fopen(path, "wb");
    if (!f) { send_err(fd, 500, strerror(errno), 0); return; }
    setvbuf(f, NULL, _IOFBF, CHUNK);
    long long got = rq->clen > 0 ? recv_body(fd, rq, file_sink, f, "upload") : 0;
    bool closed = fclose(f) == 0;
    if (got != rq->clen || !closed) { remove(path); send_err(fd, 500, "upload incomplete", 0); return; }
    printf("Wrote %s (%lld bytes)\n", path + 5, got);
    send_ok(fd);
}

static void h_file_delete(int fd, req_t *rq) {
    char path[600];
    if (!sd_path(rq->query, path, sizeof path)) { send_err(fd, 400, "path required, starting with /", 0); return; }
    struct stat st;
    if (stat(path, &st) != 0) { send_err(fd, 404, strerror(errno), 0); return; }
    if ((S_ISDIR(st.st_mode) ? rmdir(path) : remove(path)) != 0) { send_err(fd, 500, strerror(errno), 0); return; }
    printf("Removed %s\n", path + 5);
    send_ok(fd);
}

// ---------------------------------------------------------------- main

enum { ACT_NONE, ACT_EXIT, ACT_REBOOT, ACT_SHUTDOWN, ACT_LAUNCH };
static int pending = ACT_NONE;
static u64 launch_tid;
static FS_MediaType launch_mt;

static void handle(int fd) {
    static char hdr[HDR_MAX];
    req_t rq = {0};
    if (!read_request(fd, &rq, hdr)) return;
    printf("%s %s\n", rq.method, rq.path);
    bool get = !strcmp(rq.method, "GET"), post = !strcmp(rq.method, "POST");
    const char *p = rq.path;

    if (get && !strcmp(p, "/status")) h_status(fd);
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
        if (!tid_param(rq.query, &launch_tid)) { send_err(fd, 400, "tid required (hex)", 0); return; }
        launch_mt = media_param(rq.query);
        pending = ACT_LAUNCH;
        send_ok(fd);
    }
    else if (post && !strcmp(p, "/reboot"))   { pending = ACT_REBOOT;   send_ok(fd); }
    else if (post && !strcmp(p, "/shutdown")) { pending = ACT_SHUTDOWN; send_ok(fd); }
    else if (post && !strcmp(p, "/exit"))     { pending = ACT_EXIT;     send_ok(fd); }
    else send_err(fd, 404, "unknown endpoint", 0);
}

int main(void) {
    gfxInitDefault();
    consoleInit(GFX_TOP, NULL);
    printf("3DS Remote v%s\n\n", APP_VERSION);

    amInit();
    cfguInit();
    ptmuInit();
    have_mcu = R_SUCCEEDED(mcuHwcInit());
    have_ptmsysm = R_SUCCEEDED(ptmSysmInit());
    aptSetSleepAllowed(false);   // keep serving with the lid closed

    u32 *socbuf = memalign(0x1000, SOC_BUFSIZE);
    Result r = socInit(socbuf, SOC_BUFSIZE);
    int srv = -1;
    if (R_FAILED(r)) {
        printf("socInit failed: %08lX\n", r);
    } else {
        srv = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        struct sockaddr_in a = {0};
        a.sin_family = AF_INET;
        a.sin_port = htons(PORT);
        a.sin_addr.s_addr = INADDR_ANY;
        if (srv < 0 || bind(srv, (struct sockaddr *)&a, sizeof a) < 0 || listen(srv, 4) < 0) {
            printf("socket setup failed: %d\n", errno);
            srv = -1;
        } else {
            fcntl(srv, F_SETFL, fcntl(srv, F_GETFL, 0) | O_NONBLOCK);
            struct in_addr ip = {.s_addr = gethostid()};
            printf("Listening on http://%s:%d\n", inet_ntoa(ip), PORT);
        }
    }
    printf("START: quit\n\n");

    while (aptMainLoop()) {
        hidScanInput();
        if (hidKeysDown() & KEY_START) break;

        if (srv >= 0 && pending == ACT_NONE) {
            int c = accept(srv, NULL, NULL);
            if (c >= 0) {
                fcntl(c, F_SETFL, fcntl(c, F_GETFL, 0) & ~O_NONBLOCK);
                handle(c);
                shutdown(c, SHUT_RDWR);
                close(c);
            }
        }

        if (pending == ACT_EXIT) break;
        if (pending == ACT_REBOOT || pending == ACT_SHUTDOWN) {
            bool reboot = pending == ACT_REBOOT;
            printf(reboot ? "Rebooting...\n" : "Shutting down...\n");
            if (have_ptmsysm) reboot ? PTMSYSM_RebootAsync(0) : PTMSYSM_ShutdownAsync(0);
            else if (reboot) APT_HardwareResetAsync();
            pending = ACT_NONE;
        }
        if (pending == ACT_LAUNCH) {
            static u8 param[0x300], hmac[0x20];
            printf("Launching %016llX\n", launch_tid);
            r = APT_PrepareToDoApplicationJump(0, launch_tid, launch_mt);
            if (R_SUCCEEDED(r)) r = APT_DoApplicationJump(param, sizeof param, hmac);
            if (R_FAILED(r)) printf("  launch failed: %08lX\n", r);
            pending = ACT_NONE;  // on success aptMainLoop() returns false and we exit
        }

        gspWaitForVBlank();
    }

    if (srv >= 0) close(srv);
    socExit();
    if (have_ptmsysm) ptmSysmExit();
    if (have_mcu) mcuHwcExit();
    ptmuExit();
    cfguExit();
    amExit();
    gfxExit();
    return 0;
}
