#pragma once

#include "common.h"

typedef struct { char *d; size_t n, cap; } buf_t;

void b_put(buf_t *b, const char *s, size_t n);
void b_printf(buf_t *b, const char *fmt, ...);
void b_str(buf_t *b, const char *s);   // JSON string literal

typedef struct {
    char method[8];
    char path[256];
    char query[1024];
    char token[TOKEN_MAX + 1];   // from "Authorization: Bearer" or "X-Auth-Token"
    long long clen;
    char *body0;                 // body bytes read together with the header
    size_t body0len;
} req_t;

extern int last_status;          // status code of the last response sent

bool read_request(int fd, req_t *rq, char *hdr);
bool send_all(int fd, const void *data, size_t n);
void send_head(int fd, int code, const char *ctype, long long len);
void send_json(int fd, int code, buf_t *b);
void send_err(int fd, int code, const char *what, Result r);
void send_ok(int fd);
bool get_param(const char *q, const char *key, char *out, size_t outsz);

// Streams the request body into sink(); progress goes to the GUI activity line.
typedef bool (*sink_fn)(void *ctx, u64 off, const void *data, u32 len);
long long recv_body(int fd, req_t *rq, sink_fn sink, void *ctx, const char *label);
