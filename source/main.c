// 3ds-remote: HTTP/JSON control server for a 3DS running Luma3DS, with an on-console GUI.
//
// Endpoints (port 8080, all but /ping need "Authorization: Bearer <senha>"):
//   GET    /ping                         app name, version, whether auth is on (no auth)
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
//
// The password lives in sdmc:/3ds/3ds-remote/config.ini and can only be changed on the console.

#include "common.h"

bool have_mcu, have_ptmsysm;

static void run_pending(void) {
    switch (g.pending) {
        case ACT_REBOOT:
            log_add("reiniciando");
            if (have_ptmsysm) PTMSYSM_RebootAsync(0);
            else APT_HardwareResetAsync();
            g.pending = ACT_NONE;
            break;
        case ACT_SHUTDOWN:
            log_add("desligando");
            if (have_ptmsysm) PTMSYSM_ShutdownAsync(0);
            g.pending = ACT_NONE;
            break;
        case ACT_LAUNCH: {
            static u8 param[0x300], hmac[0x20];
            log_add("abrindo %016llX", g.launch_tid);
            Result r = APT_PrepareToDoApplicationJump(0, g.launch_tid, g.launch_mt);
            if (R_SUCCEEDED(r)) r = APT_DoApplicationJump(param, sizeof param, hmac);
            if (R_FAILED(r)) log_add("falha ao abrir: %08lX", r);
            g.pending = ACT_NONE;   // on success aptMainLoop() returns false and we exit
            break;
        }
    }
}

int main(void) {
    gfxInitDefault();
    LightLock_Init(&g.lock);

    amInit();
    cfguInit();
    ptmuInit();
    have_mcu = R_SUCCEEDED(mcuHwcInit());
    have_ptmsysm = R_SUCCEEDED(ptmSysmInit());
    aptSetSleepAllowed(false);   // keep serving with the lid closed

    config_load();
    gui_init();
    server_start();
    log_add("servidor iniciado");

    while (aptMainLoop()) {
        hidScanInput();
        if (!gui_frame(hidKeysDown(), hidKeysHeld())) break;
        if (g.pending == ACT_EXIT) break;
        run_pending();
    }

    server_stop();
    gui_exit();
    if (have_ptmsysm) ptmSysmExit();
    if (have_mcu) mcuHwcExit();
    ptmuExit();
    cfguExit();
    amExit();
    gfxExit();
    return 0;
}
