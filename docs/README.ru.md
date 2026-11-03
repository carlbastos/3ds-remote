# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · **Русский** · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Управление New 3DS с Luma3DS по сети с компьютера.

## Установка

На 3DS откройте **FBI → Remote Install → Scan QR Code**:

![QR-код последней версии](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

В каждом [релизе](https://github.com/carlbastos/3ds-remote/releases) есть `3ds-remote.cia`, `3ds-remote.3dsx`, клиент `3ds` и QR-код этой версии.

## Как это работает

Три компонента:

| Компонент | Где работает | Что делает |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, как приложение (CIA или `.3dsx`) | HTTP/JSON-сервер на порту **8080**: состояние, игры, установка и удаление CIA, запуск игр, файлы на SD-карте, перезагрузка и выключение |
| **InputRedirection** из Rosalina | 3DS, в фоне | Принимает кнопки, касания и стик по UDP **4950**, в том числе внутри игр |
| **NTR-HR** (remote play) | 3DS, в фоне | Транслирует экраны; клиент берёт кадр как скриншот (TCP **8000** + UDP **8001**) |

Клиент `3ds` работает в Windows, macOS и Linux и обращается ко всем трём.

## Установка клиента

С Python 3.9 или новее, в любой ОС:

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

Без Python скачайте исполняемый файл для своей системы из [последнего релиза](https://github.com/carlbastos/3ds-remote/releases/latest): `3ds-windows-x64.exe`, `3ds-macos-arm64` или `3ds-linux-x64`. В macOS и Linux сначала выполните `chmod +x`; macOS может попросить разрешить запуск в *Системные настройки → Конфиденциальность и безопасность*, так как файл не подписан.

`3ds config` показывает, где хранятся настройки (`%APPDATA%\3ds-remote` в Windows, `~/.config/3ds-remote` в macOS и Linux). `screenshot` принимает изображение на UDP-порт **8001**, поэтому при первом запуске брандмауэр может запросить разрешение.

## Использование

Сначала свяжите компьютер с консолью. Нажмите **Y** в 3DS Remote, чтобы увидеть пароль:

```sh
3ds login --host 192.168.1.241    # спросит пароль и сохранит его в ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # без пароля: версия и включён ли пароль

3ds status                        # батарея, Wi-Fi, SD-карта, модель, прошивка, Luma
3ds titles [--all] [--json]       # установленные игры с названиями
3ds install game.cia [...]        # пропускает CIA, если эта версия уже установлена (--force)
3ds launch <name|tid>             # запускает игру (сервер закрывается)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # устанавливает последний релиз с GitHub

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # x,y[:ms] ...
3ds snap [file.png]                           # 400x480
3ds screenshot [--screen bottom] file.png     # PNG, JPEG, WebP
```

`THREEDS=ip[:порт]` и `THREEDS_TOKEN=<пароль>` переопределяют файл настроек. `3ds logout` удаляет сохранённый пароль.

Для `press`/`touch`/`drag`/`stick` нужен включённый InputRedirection, для `screenshot` — загруженный NTR-HR. Сервер для них открывать не нужно.

## На консоли

| Экран | Что на нём |
|---|---|
| Верхний | Адрес, состояние (В СЕТИ / ПАУЗА / НЕТ СЕТИ), пароль (скрыт), батарея, Wi-Fi, ход передачи файлов и последние запросы |
| Нижний (сенсорный) | Показать пароль (**Y**), новый случайный пароль (**X**), задать пароль с клавиатуры, включить или отключить пароль, пауза (**SELECT**), выход (**START**), язык (**L/R**) |

## Языки

Интерфейс приложения доступен на всех 12 языках 3DS: португальском, английском, испанском, русском, японском, французском, немецком, итальянском, нидерландском, упрощённом китайском, корейском и традиционном китайском. По умолчанию используется язык системы. **L/R** или переключатель в углу нижнего экрана меняют язык; выбор сохраняется в `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Для китайского и корейского приложение по мере надобности загружает системные шрифты CHN/KOR/TWN.

Чтобы перевести или исправить строки, правьте `source/i18n.c`. Если перевода нет, показывается английский текст.

## Безопасность

- **Пароль обязателен** для всех маршрутов, кроме `/ping`, через `Authorization: Bearer <пароль>`. При первом запуске приложение создаёт случайный пароль из 12 символов и сохраняет его в `sdmc:/config/3ds-remote/config.ini`.
- Пароль **меняется только на консоли**. Ни один endpoint не меняет настройки, а API не может ни читать, ни записывать `config.ini`.
- **5 неверных паролей подряд** блокируют вход на 30 с (HTTP 429).
- Пути с `..` или `\` отклоняются.
- Любое чтение или запись по сети прерывается через 15 с, чтобы зависший клиент не блокировал сервер.
- **Пауза** действительно закрывает порт, и сервер слушает, только пока приложение открыто.
- Отключение пароля требует подтверждения (два касания).
- **Ограничение:** это HTTP без TLS, поэтому пароль передаётся по локальной сети открытым текстом. Используйте только в доверенной сети.

## После каждого включения 3DS

1. Откройте **Boot NTR Selector** → путь по умолчанию → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Для сервера: откройте **3DS Remote** в меню HOME.

## Разработка

Сборка, CI, список endpoints и технические заметки — в [README на английском](../README.md#build).
