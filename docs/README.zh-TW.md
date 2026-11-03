# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · **繁體中文**

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

從電腦透過網路控制執行 Luma3DS 的 New 3DS。

## 安裝

在 3DS 上開啟 **FBI → Remote Install → Scan QR Code**：

![最新版本的 QR 碼](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

每個[發行版本](https://github.com/carlbastos/3ds-remote/releases)都包含 `3ds-remote.cia`、`3ds-remote.3dsx`、用戶端 `3ds` 以及該版本的 QR 碼。

## 運作方式

共有三個部分：

| 部分 | 執行位置 | 用途 |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS，作為應用程式（CIA 或 `.3dsx`） | 連接埠 **8080** 上的 HTTP/JSON 伺服器：狀態、遊戲清單、安裝/刪除 CIA、啟動遊戲、SD 卡檔案、重新啟動/關機 |
| Rosalina 的 **InputRedirection** | 3DS，背景執行 | 透過 UDP **4950** 接收按鍵、觸控和類比搖桿輸入，遊戲中也可以 |
| **NTR-HR**（遠端遊玩） | 3DS，背景執行 | 串流畫面；用戶端擷取一格畫面作為螢幕截圖（TCP **8000** + UDP **8001**） |

用戶端 `3ds` 可在 Windows、macOS 和 Linux 上執行，並與這三個部分通訊。

## 安裝用戶端

在任何系統上，只要有 Python 3.9 或更新版本：

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

沒有 Python 的話，請從[最新發行版本](https://github.com/carlbastos/3ds-remote/releases/latest)下載對應系統的執行檔：`3ds-windows-x64.exe`、`3ds-macos-arm64` 或 `3ds-linux-x64`。在 macOS 和 Linux 上請先執行 `chmod +x`；由於沒有簽署，macOS 可能會要求在 *系統設定 → 隱私權與安全性* 中允許執行。

`3ds config` 會顯示設定檔的位置（Windows 為 `%APPDATA%\3ds-remote`，macOS 和 Linux 為 `~/.config/3ds-remote`）。`screenshot` 透過 UDP 連接埠 **8001** 接收畫面，因此第一次使用時防火牆可能會要求允許。

## 使用方式

第一次使用時，先將電腦與主機配對。在 3DS Remote 中按 **Y** 顯示密碼：

```sh
3ds login --host 192.168.1.241    # 輸入密碼並儲存到 ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # 不需密碼：版本及是否啟用密碼

3ds status                        # 電池、Wi-Fi、SD 卡、型號、韌體、Luma
3ds titles [--all] [--json]       # 已安裝的遊戲及名稱
3ds install game.cia [...]        # 若該版本已安裝則略過 (--force)
3ds launch <name|tid>             # 啟動遊戲（伺服器會關閉）
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # 安裝 GitHub 上的最新版本

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # x,y[:ms] ...
3ds snap [file.png]                           # 400x480
3ds screenshot [--screen bottom] file.png     # PNG, JPEG, WebP
```

`THREEDS=ip[:連接埠]` 和 `THREEDS_TOKEN=<密碼>` 優先於設定檔。`3ds logout` 會刪除已儲存的密碼。

`press`/`touch`/`drag`/`stick` 需要開啟 InputRedirection；`screenshot` 需要載入 NTR-HR。兩者都不需要開啟伺服器。

## 主機上的畫面

| 螢幕 | 內容 |
|---|---|
| 上螢幕 | 位址、狀態（線上 / 已暫停 / 無網路）、密碼（隱藏）、電池、Wi-Fi、傳輸進度和最近的請求 |
| 下螢幕（觸控） | 顯示密碼（**Y**）、產生隨機新密碼（**X**）、用鍵盤設定密碼、開啟/關閉密碼、暫停（**SELECT**）、結束（**START**）、語言（**L/R**） |

## 語言

應用程式介面支援 3DS 的全部 12 種語言：葡萄牙文、英文、西班牙文、俄文、日文、法文、德文、義大利文、荷蘭文、簡體中文、韓文和繁體中文。預設跟隨系統語言。按 **L/R** 或點下螢幕角落的選擇器切換語言，選擇會儲存到 `config.ini`（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。

中文和韓文會在需要時載入系統字型 CHN/KOR/TWN。

翻譯或修改文字請編輯 `source/i18n.c`。缺少的翻譯會顯示英文。

## 安全性

- 除了 `/ping` 以外的所有路徑都**需要密碼**（`Authorization: Bearer <密碼>`）。第一次執行時，應用程式會產生 12 個字元的隨機密碼並儲存到 `sdmc:/config/3ds-remote/config.ini`。
- 密碼**只能在主機上變更**。沒有任何端點能變更設定，API 也無法讀取或寫入 `config.ini`。
- **連續 5 次密碼錯誤**會鎖定登入 30 秒（HTTP 429）。
- 拒絕包含 `..` 或 `\` 的路徑。
- 所有網路讀寫在 15 秒後逾時，卡住的用戶端不會拖住伺服器。
- **暫停**會真正關閉連接埠，伺服器只在應用程式開啟時監聽。
- 關閉密碼需要確認（點兩次）。
- **限制：**這是沒有 TLS 的 HTTP，密碼在區域網路中以明文傳輸。請只在可信任的網路中使用。

## 每次啟動 3DS 後

1. 開啟 **Boot NTR Selector** → 預設路徑 → **3.6 HR**。
2. Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。
3. 使用伺服器時：從 HOME 選單開啟 **3DS Remote**。

## 開發

編譯、CI、端點清單和技術說明請見[英文 README](../README.md#build)。
