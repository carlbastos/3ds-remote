---
name: 3ds-control
description: Operate a Nintendo 3DS running Luma3DS through this repo's `3ds` client — see both screens, press buttons and touch, navigate the HOME Menu, launch and close games, install or remove CIAs, move SD files, reboot. Use whenever a task involves doing something on the 3DS itself.
---

# Driving the 3DS

The `3ds` client talks to three independent things on the console. Check which ones you need
before acting, because each must be started again by the user after every boot:

| Need | Provided by | Check | If missing, ask the user to |
|---|---|---|---|
| status, titles, install/delete, launch, SD files, reboot | 3DS Remote app (TCP 8080) | `3ds ping` | open **3DS Remote** from the HOME Menu |
| seeing the screens (`snap`, `screenshot`) | NTR-HR remote play (TCP 8000, UDP 8001) | `3ds snap` returns an image | open **BootNTR Selector** and pick **3.6 HR** |
| buttons, touch, drags (`press`, `touch`, `drag`, `stick`) | Rosalina InputRedirection (UDP 4950) | `snap`, `press R`, `snap`, `press L`: the images differ | open the Rosalina menu (L+Down+Select) → Miscellaneous → InputRedirection |

InputRedirection is UDP, so nothing confirms a press arrived: verify with a screenshot. Input and
screenshots do not need the 3DS Remote app to be open. Use the `3ds` on PATH, or `.venv/bin/3ds`
when the client is installed editable in this repo (`snap` needs Pillow, a dependency).

## The control loop

1. `3ds snap /tmp/x.png` and look at it. The image is 400x480: top screen at (0,0), bottom screen
   at **(+40,+240)**. Touch coordinates are bottom-screen pixels (0-319 x 0-239), so subtract 40 and
   240 from what you see in the image.
2. Do **one** action: `3ds press A`, `3ds touch x y`, `3ds drag ...`.
3. Wait for the UI (HOME Menu ~1-1.5 s, opening a folder ~1.5 s, launching a game 6-10 s), then
   snap again. Never chain blind actions: a missed press shifts everything after it.

On the HOME Menu, tapping an icon once selects it and the **top screen shows that title's banner**:
use the banner to identify icons instead of guessing from 48 px pictures.

## Commands

```sh
3ds snap out.png                      # both screens; screenshot --screen bottom for one
3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME   # --hold/--gap in ms
3ds touch 160 120                     # tap on the bottom screen
3ds drag 280,150 40,150 --grab 50 --move 300 --drop 50             # swipe (scroll the grid)
3ds drag 273,175:2200 57,55:3000 40,67:1000                        # x,y:ms = hold there ms
3ds status ; 3ds titles [--all] ; 3ds launch <name|tid> ; 3ds install x.cia ; 3ds delete <name|tid>
3ds ls /path ; 3ds get /x ; 3ds put local /x ; 3ds rm /x
3ds update ; 3ds reboot ; 3ds shutdown ; 3ds exit
```

`3ds launch` closes 3DS Remote (it jumps to the title); `3ds launch 000400000FE3D500` relaunches
3DS Remote itself, which is how to load a version just installed with `3ds install`/`update`.

## Never

- Turn the backlights off through `gsp::Lcd` (`GSPLCD_PowerOff*Backlight*`): on a New 3DS XL no
  PowerOn call brought them back, and the console had to be power-cycled by hand.
- Send NTR's remote-play command (901) in the old NTR format: it kills NTR's networking until
  reboot. The client already uses the NTR-HR format; don't hand-roll it.
- Drop a dragged icon on an occupied HOME Menu slot unless you mean to swap (see the reference).
- Assume a game's unsaved progress is disposable: closing software loses it. Ask first if a game
  was already running when you arrived.

## References

- [references/home-menu.md](references/home-menu.md): grid, folders, moving icons, opening and
  closing software.
- [references/installing.md](references/installing.md): versions, `update`, downgrading through FBI.
- [references/recovery.md](references/recovery.md): reboot/shutdown behaviour, crash screens, what
  only the user can fix.
