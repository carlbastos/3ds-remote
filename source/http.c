// Minimal HTTP/1.1: one request per connection, Content-Length bodies, JSON responses.

#include "http.h"

#include <malloc.h>
#include <poll.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>

#define IO_TIMEOUT_MS 15000

int last_status;

void b_put(buf_t *b, const char *s, size_t n) {
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

void b_printf(buf_t *b, const char *fmt, ...) {
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

void b_str(buf_t *b, const char *s) {
    b_put(b, "\"", 1);
    for (; *s; s++) {
        unsigned char c = *s;
        if (c == '"' || c == '\\') { char e[2] = {'\\', c}; b_put(b, e, 2); }
        else if (c < 0x20) { char e[8]; snprintf(e, sizeof e, "\\u%04x", c); b_put(b, e, 6); }
        else b_put(b, (const char *)&c, 1);
    }
    b_put(b, "\"", 1);
}

// recv() that gives up after IO_TIMEOUT_MS without data.
static ssize_t recv_t(int fd, void *buf, size_t n) {
    struct pollfd p = {.fd = fd, .events = POLLIN};
    if (poll(&p, 1, IO_TIMEOUT_MS) <= 0) return -1;
    return recv(fd, buf, n, 0);
}

bool send_all(int fd, const void *data, size_t n) {
    const char *p = data;
    while (n) {
        struct pollfd pf = {.fd = fd, .events = POLLOUT};
        if (poll(&pf, 1, IO_TIMEOUT_MS) <= 0) return false;
        ssize_t s = send(fd, p, n > CHUNK ? CHUNK : n, 0);
        if (s <= 0) return false;
        p += s;
        n -= s;
    }
    return true;
}

void send_head(int fd, int code, const char *ctype, long long len) {
    const char *msg = code == 200 ? "OK" : code == 400 ? "Bad Request" : code == 401 ? "Unauthorized"
                    : code == 404 ? "Not Found" : code == 429 ? "Too Many Requests" : "Error";
    char h[320];
    int n = snprintf(h, sizeof h,
        "HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %lld\r\nConnection: close\r\n%s\r\n",
        code, msg, ctype, len, code == 401 ? "WWW-Authenticate: Bearer realm=\"3ds-remote\"\r\n" : "");
    last_status = code;
    send_all(fd, h, n);
}

void send_json(int fd, int code, buf_t *b) {
    b_put(b, "\n", 1);
    send_head(fd, code, "application/json", b->n);
    send_all(fd, b->d, b->n);
}

void send_err(int fd, int code, const char *what, Result r) {
    buf_t b = {0};
    b_put(&b, "{\"error\":", 9);
    b_str(&b, what);
    if (r) b_printf(&b, ",\"result\":\"0x%08lX\"", (unsigned long)r);
    b_put(&b, "}", 1);
    send_json(fd, code, &b);
    free(b.d);
}

void send_ok(int fd) {
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

bool get_param(const char *q, const char *key, char *out, size_t outsz) {
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

static void copy_value(char *dst, size_t dstsz, const char *src) {
    while (*src == ' ') src++;
    size_t n = strcspn(src, "\r\n");
    while (n && src[n - 1] == ' ') n--;
    if (n >= dstsz) n = dstsz - 1;
    memcpy(dst, src, n);
    dst[n] = 0;
}

bool read_request(int fd, req_t *rq, char *hdr) {
    size_t n = 0;
    char *end = NULL;
    while (!end) {
        if (n >= HDR_MAX - 1) return false;
        ssize_t r = recv_t(fd, hdr + n, HDR_MAX - 1 - n);
        if (r <= 0) return false;
        n += r;
        hdr[n] = 0;
        end = strstr(hdr, "\r\n\r\n");
    }
    end[2] = 0;   // keep the last header's CRLF so every header line ends with one
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
    rq->token[0] = 0;
    for (char *line = strstr(hdr, "\r\n"); line && line[2]; line = strstr(line + 2, "\r\n")) {
        char *h = line + 2;
        if (!strncasecmp(h, "Content-Length:", 15)) rq->clen = strtoll(h + 15, NULL, 10);
        else if (!strncasecmp(h, "Authorization:", 14)) {
            char *v = h + 14;
            while (*v == ' ') v++;
            if (!strncasecmp(v, "Bearer ", 7)) copy_value(rq->token, sizeof rq->token, v + 7);
        }
        else if (!strncasecmp(h, "X-Auth-Token:", 13)) copy_value(rq->token, sizeof rq->token, h + 13);
    }
    return rq->clen >= 0;
}

long long recv_body(int fd, req_t *rq, sink_fn sink, void *ctx, const char *label) {
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
        ssize_t r = recv_t(fd, buf, want > CHUNK ? CHUNK : want);
        if (r <= 0) break;
        if (!failed && !sink(ctx, off, buf, r)) failed = true;   // keep draining so the client gets the error
        off += r;
        int pct = (int)(off * 100 / rq->clen);
        if (pct != lastpct) {
            activity_set("%s %d%% (%llu/%llu MB)", label, pct, off >> 20, (u64)rq->clen >> 20);
            lastpct = pct;
        }
    }
    activity_set(NULL);
    free(buf);
    return failed ? -1 : (long long)off;
}
