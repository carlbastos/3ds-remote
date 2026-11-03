# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · **简体中文** · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

从电脑通过网络控制运行 Luma3DS 的 New 3DS。

## 安装

在 3DS 上打开 **FBI → Remote Install → Scan QR Code**：

![最新版本的二维码](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

每个[发布版本](https://github.com/carlbastos/3ds-remote/releases)都包含 `3ds-remote.cia`、`3ds-remote.3dsx`、客户端 `3ds` 以及该版本的二维码。

## 工作原理

共有三个部分：

| 部分 | 运行位置 | 作用 |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS，作为应用（CIA 或 `.3dsx`） | 端口 **8080** 上的 HTTP/JSON 服务器：状态、游戏列表、安装/删除 CIA、启动游戏、SD 卡文件、重启/关机 |
| Rosalina 的 **InputRedirection** | 3DS，后台 | 通过 UDP **4950** 接收按键、触摸和摇杆输入，游戏中也可以 |
| **NTR-HR**（远程游玩） | 3DS，后台 | 串流画面；客户端截取一帧作为截图（TCP **8000** + UDP **8001**） |

客户端 `3ds` 可在 Windows、macOS 和 Linux 上运行，并与这三部分通信。

## 安装客户端

在任何系统上，只要有 Python 3.9 或更高版本：

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

没有 Python 的话，请从[最新发布版本](https://github.com/carlbastos/3ds-remote/releases/latest)下载对应系统的可执行文件：`3ds-windows-x64.exe`、`3ds-macos-arm64` 或 `3ds-linux-x64`。在 macOS 和 Linux 上先运行 `chmod +x`；由于未签名，macOS 可能会要求在 *系统设置 → 隐私与安全性* 中允许运行。

`3ds config` 会显示配置文件的位置（Windows 为 `%APPDATA%\3ds-remote`，macOS 和 Linux 为 `~/.config/3ds-remote`）。`screenshot` 通过 UDP 端口 **8001** 接收画面，因此首次使用时防火墙可能会请求许可。

## 使用方法

第一次使用时，先将电脑与主机配对。在 3DS Remote 中按 **Y** 显示密码：

```sh
3ds login --host 192.168.1.241    # 输入密码并保存到 ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # 无需密码：版本以及是否启用密码

3ds status                        # 电池、Wi-Fi、SD 卡、型号、固件、Luma
3ds titles [--all] [--json]       # 已安装的游戏及名称
3ds install game.cia [...]        # 如果该版本已安装则跳过 (--force)
3ds launch <name|tid>             # 启动游戏（服务器会关闭）
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # 安装 GitHub 上的最新版本

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # x,y[:ms] ...
3ds snap [file.png]                           # 400x480
3ds screenshot [--screen bottom] file.png     # PNG, JPEG, WebP
```

`THREEDS=ip[:端口]` 和 `THREEDS_TOKEN=<密码>` 优先于配置文件。`3ds logout` 会删除已保存的密码。

`press`/`touch`/`drag`/`stick` 需要开启 InputRedirection；`screenshot` 需要加载 NTR-HR。两者都不需要打开服务器。

## 主机上的界面

| 屏幕 | 内容 |
|---|---|
| 上屏 | 地址、状态（在线 / 已暂停 / 无网络）、密码（隐藏）、电池、Wi-Fi、传输进度和最近的请求 |
| 下屏（触摸） | 显示密码（**Y**）、生成随机新密码（**X**）、用键盘设置密码、开启/关闭密码、暂停（**SELECT**）、退出（**START**）、语言（**L/R**） |

## 语言

应用界面支持 3DS 的全部 12 种语言：葡萄牙语、英语、西班牙语、俄语、日语、法语、德语、意大利语、荷兰语、简体中文、韩语和繁体中文。默认跟随系统语言。按 **L/R** 或点下屏角落的选择器切换语言，选择会保存到 `config.ini`（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。

中文和韩语会在需要时加载系统字体 CHN/KOR/TWN。

翻译或修改文本请编辑 `source/i18n.c`。缺少的翻译会显示英文。

## 安全

- 除 `/ping` 外的所有接口都**需要密码**（`Authorization: Bearer <密码>`）。首次运行时，应用会生成 12 位随机密码并保存到 `sdmc:/config/3ds-remote/config.ini`。
- 密码**只能在主机上修改**。没有任何接口能修改设置，API 也无法读取或写入 `config.ini`。
- **连续 5 次密码错误**会锁定登录 30 秒（HTTP 429）。
- 拒绝包含 `..` 或 `\` 的路径。
- 所有网络读写在 15 秒后超时，卡住的客户端不会拖住服务器。
- **暂停**会真正关闭端口，服务器只在应用打开时监听。
- 关闭密码需要确认（点两次）。
- **限制：**这是没有 TLS 的 HTTP，密码在局域网中以明文传输。请只在可信的网络中使用。

## 每次启动 3DS 后

1. 打开 **Boot NTR Selector** → 默认路径 → **3.6 HR**。
2. Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。
3. 使用服务器时：从 HOME 菜单打开 **3DS Remote**。

## 开发

编译、CI、接口列表和技术说明请见[英文 README](../README.md#build)。
