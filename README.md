# 3ds-remote

**English** · [Português](docs/README.pt-BR.md) · [Español](docs/README.es.md) · [Русский](docs/README.ru.md) · [日本語](docs/README.ja.md) · [Français](docs/README.fr.md) · [Deutsch](docs/README.de.md) · [Italiano](docs/README.it.md) · [Nederlands](docs/README.nl.md) · [简体中文](docs/README.zh-CN.md) · [한국어](docs/README.ko.md) · [繁體中文](docs/README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Control a New 3DS running Luma3DS over the network from your computer.

## Install

On the 3DS, open **FBI → Remote Install → Scan QR Code**:

![QR code for the latest release](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Every [release](https://github.com/carlbastos/3ds-remote/releases) ships `3ds-remote.cia`, `3ds-remote.3dsx`, the `3ds` client and the QR code for that version.

## How it works

There are three parts:

| Part | Runs on | What it does |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, as an app (CIA or `.3dsx`) | HTTP/JSON server on port **8080**: status, titles, install/remove CIAs, launch titles, SD card files, reboot/shutdown |
| Rosalina **InputRedirection** | 3DS, in the background | Receives buttons, touch and circle pad over UDP **4950**, including inside games |
| **NTR-HR** (remote play) | 3DS, in the background | Streams the screens; the client grabs a frame as a screenshot (TCP **8000** + UDP **8001**) |

The `3ds` client runs on Windows, macOS and Linux and talks to all three.

## Install the client

With Python 3.9 or newer, on any OS:

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

(`pip install` works too; [pipx](https://pipx.pypa.io) keeps it in its own environment.) Without Python, download the executable for your system from the [latest release](https://github.com/carlbastos/3ds-remote/releases/latest): `3ds-windows-x64.exe`, `3ds-macos-arm64` or `3ds-linux-x64`. On macOS and Linux, `chmod +x` it first; macOS may also ask you to allow it under *System Settings → Privacy & Security*, since it is not signed.

| OS | Settings file |
|---|---|
| Windows | `%APPDATA%\3ds-remote\config.json` |
| macOS, Linux | `~/.config/3ds-remote/config.json` (or `$XDG_CONFIG_HOME`) |

`3ds config` shows where it is. `screenshot` receives the stream on UDP port **8001**, so the first time your firewall (Windows Defender, for instance) may ask to allow it.

## Usage

The first time, pair your computer with the console. Press **Y** in 3DS Remote to show the password:

```sh
3ds login --host 192.168.1.241    # asks for the password, saves it to ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # no password needed: version and whether the password is on

3ds status                        # battery, Wi-Fi, SD card, model, firmware, Luma
3ds titles [--all] [--json]       # installed titles with names
3ds install game.cia [...]        # skips CIAs whose version is already installed (--force)
3ds launch <name|tid>             # launches a title (the server closes)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # installs the latest GitHub release

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png   # PNG, JPEG, WebP... by extension
```

`THREEDS=ip[:port]` and `THREEDS_TOKEN=<password>` override the config file. `3ds logout` forgets the saved password.

`press`/`touch`/`drag`/`stick` need InputRedirection enabled; `screenshot` needs NTR-HR loaded. Neither needs the server to be open.

## On the console

| Screen | Contents |
|---|---|
| Top | Address, state (ONLINE / PAUSED / NO NETWORK), password (hidden), battery, Wi-Fi, transfer progress and the latest requests |
| Bottom (touch) | Show password (**Y**), new random password (**X**), set password with the keyboard, turn the password requirement on/off, pause (**SELECT**), exit (**START**), language (**L/R**) |

## Languages

The app's UI is available in all 12 languages the 3DS offers: Portuguese, English, Spanish, Russian, Japanese, French, German, Italian, Dutch, Simplified Chinese, Korean and Traditional Chinese. By default it follows the system language. **L/R**, or the selector in the corner of the bottom screen, cycles through them (*automatic* → Português → … → 繁體中文); the choice is saved in `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Chinese and Korean use the CHN/KOR/TWN system fonts, loaded when needed. Each log line is drawn with the font of the language it was logged in.

To translate or fix strings, edit `source/i18n.c`. A missing translation falls back to English.

The translated READMEs in `docs/` cover the user-facing sections and are generated by `tools/gen_readmes.py` (the translations live in that script); this file and `docs/README.pt-BR.md` are edited by hand.

## Security

- **Password required** on every route except `/ping`, via `Authorization: Bearer <password>`. On first run the app generates a random 12-character password (from the `ssl:C` RNG) and stores it in `sdmc:/config/3ds-remote/config.ini`.
- Versions up to 0.2.0 kept the config in `/3ds/3ds-remote/`. The app moves it to `/config/3ds-remote/` automatically, because the Homebrew Launcher lists every folder under `/3ds` as an app.
- The password **can only be changed on the console** (touch screen). No endpoint changes settings, and the API can neither read nor write `config.ini`.
- **5 wrong passwords in a row** lock out logins for 30 s (HTTP 429).
- Paths containing `..` or `\` are rejected.
- Every network read and write times out after 15 s, so a stalled client can't hang the server.
- **Pause** really closes the port, and the server only listens while the app is open.
- Turning the password off asks for confirmation (two taps).
- **Limitation:** this is plain HTTP without TLS, so the password crosses the local network in clear text. Only use it on a network you trust.

## After every 3DS boot

1. Open **Boot NTR Selector** → default path → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. For the server: open **3DS Remote** from the HOME Menu.

## Build

Requirements: devkitPro with `3ds-dev` in `/opt/devkitpro`.

```sh
./build-cia.sh      # builds 3ds-remote.3dsx and 3ds-remote.cia
```

On first use, `tools/fetch-tools.sh` downloads makerom 0.19.0 (Project_CTR) and builds bannertool 1.2.3 (carstene1ns fork) into `tools/`. None of that is committed.

Client development: `pip install -e ./client`, then `python -m unittest discover -s client/tests`. From a checkout you can also run `./3ds` directly.

The 3DS refuses a CIA with the same version as the installed one (`0xC8E083FC`), so every change to the app needs a new version in `VERSION`.

## CI and releases

The [`build`](.github/workflows/build.yml) workflow compiles in the `devkitpro/devkitarm` container:

- **push / PR:** builds the `.3dsx` and the CIA, tests the client on Linux, macOS and Windows (Python 3.9 and 3.13), builds the standalone client executables, and keeps everything as run artifacts.
- **tag `vX.Y.Z`:** checks that the tag (and the client version) matches `VERSION`, builds, and publishes a release with the CIA, 3dsx, QR code and client executables.

To cut a release:

```sh
tools/release.sh X.Y.Z     # updates VERSION, commits, tags vX.Y.Z and pushes
gh run watch               # follow the build
3ds update                 # install it on the 3DS (with the server open)
```

To test without installing: Homebrew Launcher → **Y**, then
`/opt/devkitpro/tools/bin/3dslink -a <3DS IP> 3ds-remote.3dsx`.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/ping` | no password |
| GET | `/status` | |
| GET | `/titles?media=sd\|nand\|card` | names come from the SMDH |
| POST | `/install?media=sd` | body = raw CIA, with `Content-Length` |
| POST | `/delete?tid=HEX&media=sd` | |
| POST | `/launch?tid=HEX&media=sd` | the app exits to launch the title |
| GET | `/ls?path=/dir` | |
| GET/PUT/DELETE | `/file?path=/x` | PUT creates parent folders |
| POST | `/reboot`, `/shutdown`, `/exit` | |

Every route except `/ping` requires `Authorization: Bearer <password>` (or `X-Auth-Token`). Errors look like `{"error": "...", "result": "0x..."}`, with 401 (missing or wrong password) and 429 (locked out).

## Notes

- **NTR-HR**: the remote play command (901) needs its arguments in NTRViewer-HR's format (`arg3 = 1404036572`, `arg4 = UDP port`). The old NTR format takes NTR's networking down until the console is rebooted.
- **Moving a HOME Menu icon** with `drag`: holding ~2 s lifts the icon; hovering ~4 s over a folder opens it; dropping only works on an **empty** slot.
- **CIA version**: makerom 0.19.0 ignores `-ver`/`-major`/`-minor`/`-micro` when building from an ELF and only takes the major part from the RSF's `RemasterVersion`. `build-cia.sh` passes the major part through the RSF and `tools/set-cia-version.py` writes the full X.Y.Z into the TMD and ticket (check with `ctrtool -p --intype=cia`). That is why the first valid release is v0.1.1.
- `meta/app.rsf` comes from the buildtools template (Steveice10). Title ID `000400000FE3D500`, product code `CTR-P-RMTE`.
- `tools/make_art.py` generates `meta/icon.png`, `meta/banner.png` and `meta/audio.wav`.
