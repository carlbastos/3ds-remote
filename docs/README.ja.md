# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · **日本語** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Luma3DS を導入した New 3DS を、パソコンからネットワーク経由で操作します。

## インストール

3DS で **FBI → Remote Install → Scan QR Code** を開きます：

![最新版の QR コード](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

各[リリース](https://github.com/carlbastos/3ds-remote/releases)には `3ds-remote.cia`、`3ds-remote.3dsx`、クライアント `3ds`、そのバージョンの QR コードが含まれます。

## 仕組み

3 つの部品で構成されています：

| 部品 | 動作場所 | 役割 |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS（CIA または `.3dsx` のアプリ） | ポート **8080** の HTTP/JSON サーバー：状態、タイトル一覧、CIA のインストール・削除、タイトル起動、SD カードのファイル、再起動・電源オフ |
| Rosalina の **InputRedirection** | 3DS（バックグラウンド） | ボタン、タッチ、スライドパッドの入力を UDP **4950** で受け取ります（ゲーム中も可） |
| **NTR-HR**（リモートプレイ） | 3DS（バックグラウンド） | 画面を配信し、クライアントが 1 フレームをスクリーンショットとして取得します（TCP **8000** + UDP **8001**） |

クライアント `3ds` は Windows、macOS、Linux で動作し、3 つすべてと通信します。

## クライアントのインストール

Python 3.9 以降があれば、どの OS でも：

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

Python がない場合は、[最新リリース](https://github.com/carlbastos/3ds-remote/releases/latest)から自分の OS 用の実行ファイル（`3ds-windows-x64.exe`、`3ds-macos-arm64`、`3ds-linux-x64`）をダウンロードしてください。macOS と Linux では先に `chmod +x` を実行します。署名がないため、macOS では *システム設定 → プライバシーとセキュリティ* で許可を求められることがあります。

`3ds config` で設定ファイルの場所を確認できます（Windows は `%APPDATA%\3ds-remote`、macOS と Linux は `~/.config/3ds-remote`）。`screenshot` は UDP ポート **8001** で映像を受け取るため、初回はファイアウォールが許可を求めることがあります。

## 使い方

最初にパソコンと本体をペアリングします。3DS Remote で **Y** を押すとパスワードが表示されます：

```sh
3ds login --host 192.168.1.241    # パスワードを入力し ~/.config/3ds-remote/config.json (600) に保存
```

```sh
3ds ping                          # パスワード不要：バージョンとパスワードの有無

3ds status                        # バッテリー、Wi-Fi、SD、機種、ファームウェア、Luma
3ds titles [--all] [--json]       # インストール済みタイトルと名前
3ds install game.cia [...]        # 同じバージョンがインストール済みならスキップ (--force)
3ds launch <name|tid>             # タイトルを起動（サーバーは終了）
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # GitHub の最新リリースをインストール

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png   # PNG, JPEG, WebP
```

`THREEDS=ip[:ポート]` と `THREEDS_TOKEN=<パスワード>` は設定ファイルより優先されます。`3ds logout` で保存したパスワードを削除します。

`press`/`touch`/`drag`/`stick` には InputRedirection、`screenshot` には NTR-HR が必要です。どちらもサーバーを開いている必要はありません。

## 本体の画面

| 画面 | 内容 |
|---|---|
| 上画面 | アドレス、状態（オンライン / 一時停止中 / ネットなし）、パスワード（非表示）、バッテリー、Wi-Fi、転送の進行状況、最近のリクエスト |
| 下画面（タッチ） | パスワード表示（**Y**）、新しいランダムパスワード（**X**）、キーボードでパスワード設定、パスワード必須のオン・オフ、一時停止（**SELECT**）、終了（**START**）、言語（**L/R**） |

## 言語

アプリの画面は 3DS の全 12 言語に対応しています：ポルトガル語、英語、スペイン語、ロシア語、日本語、フランス語、ドイツ語、イタリア語、オランダ語、簡体字中国語、韓国語、繁体字中国語。初期設定では本体の言語に従います。**L/R** または下画面の隅のセレクターで切り替えられ、選択は `config.ini` に保存されます（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。

中国語と韓国語では、必要に応じてシステムフォント CHN/KOR/TWN を読み込みます。

文言の翻訳・修正は `source/i18n.c` を編集してください。翻訳がない項目は英語で表示されます。

## セキュリティ

- `/ping` 以外のすべてのルートで **パスワードが必須** です（`Authorization: Bearer <パスワード>`）。初回起動時に 12 文字のランダムなパスワードを生成し、`sdmc:/config/3ds-remote/config.ini` に保存します。
- パスワードは **本体でしか変更できません**。設定を変更する endpoint はなく、API から `config.ini` を読み書きすることもできません。
- **5 回連続で間違える**と、30 秒間ログインを拒否します（HTTP 429）。
- `..` や `\` を含むパスは拒否します。
- ネットワークの読み書きは 15 秒でタイムアウトするため、止まったクライアントがサーバーを固めることはありません。
- **一時停止** すると実際にポートを閉じます。サーバーはアプリを開いている間だけ待ち受けます。
- パスワードをオフにするには確認（2 回タップ）が必要です。
- **制限：** TLS なしの HTTP なので、パスワードはローカルネットワーク上を平文で流れます。信頼できるネットワークでのみ使ってください。

## 3DS を起動するたびに

1. **Boot NTR Selector** を開く → デフォルトのパス → **3.6 HR**。
2. Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。
3. サーバーを使うとき：HOME メニューから **3DS Remote** を開く。

## 開発

ビルド、CI、endpoint の一覧、技術的なメモは[英語の README](../README.md#build) を参照してください。
