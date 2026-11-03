// Network thread: owns the listening socket and serves one connection at a time,
// so the GUI keeps drawing during long transfers.

#include "common.h"

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <malloc.h>
#include <netinet/in.h>
#include <poll.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define SOC_BUFSIZE  0x100000
#define STACK_SIZE   0x10000

static Thread thread;
static u32 *socbuf;

static int open_listener(void) {
    int s = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (s < 0) return -1;
    struct sockaddr_in a = {0};
    a.sin_family = AF_INET;
    a.sin_port = htons(PORT);
    a.sin_addr.s_addr = INADDR_ANY;
    if (bind(s, (struct sockaddr *)&a, sizeof a) < 0 || listen(s, 4) < 0) {
        close(s);
        return -1;
    }
    return s;
}

static void set_listening(bool on) {
    LightLock_Lock(&g.lock);
    g.listening = on;
    LightLock_Unlock(&g.lock);
}

static void server_main(void *arg) {
    (void)arg;
    int srv = -1;
    u64 retry_at = 0;

    while (!g.quit) {
        bool want = !g.paused && g.pending == ACT_NONE;
        if (!want && srv >= 0) {
            close(srv);
            srv = -1;
            set_listening(false);
        }
        if (want && srv < 0 && osGetTime() >= retry_at) {
            srv = open_listener();
            set_listening(srv >= 0);
            if (srv < 0) retry_at = osGetTime() + 2000;   // e.g. Wi-Fi off; try again later
        }
        if (srv < 0) {
            svcSleepThread(100 * 1000 * 1000ULL);
            continue;
        }

        struct pollfd p = {.fd = srv, .events = POLLIN};
        if (poll(&p, 1, 250) <= 0 || !(p.revents & POLLIN)) continue;

        struct sockaddr_in peer;
        socklen_t plen = sizeof peer;
        int c = accept(srv, (struct sockaddr *)&peer, &plen);
        if (c < 0) continue;
        api_handle(c, peer.sin_addr.s_addr);
        shutdown(c, SHUT_RDWR);
        close(c);
    }
    if (srv >= 0) close(srv);
    set_listening(false);
}

void server_start(void) {
    socbuf = memalign(0x1000, SOC_BUFSIZE);
    if (!socbuf || R_FAILED(socInit(socbuf, SOC_BUFSIZE))) {
        log_add("socInit falhou");
        return;
    }
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    // Slightly higher priority than the GUI so requests are served promptly; it blocks on I/O.
    thread = threadCreate(server_main, NULL, STACK_SIZE, prio - 1, -2, false);
    if (!thread) log_add("thread do servidor falhou");
}

void server_stop(void) {
    g.quit = true;
    if (thread) {
        threadJoin(thread, U64_MAX);
        threadFree(thread);
        thread = NULL;
    }
    socExit();
    free(socbuf);
}
