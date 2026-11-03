# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · **한국어** · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Luma3DS가 설치된 New 3DS를 컴퓨터에서 네트워크로 제어합니다.

## 설치

3DS에서 **FBI → Remote Install → Scan QR Code**를 엽니다:

![최신 버전 QR 코드](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

각 [릴리스](https://github.com/carlbastos/3ds-remote/releases)에는 `3ds-remote.cia`, `3ds-remote.3dsx`, 클라이언트 `3ds`, 해당 버전의 QR 코드가 들어 있습니다.

## 작동 방식

세 부분으로 이루어져 있습니다:

| 구성 요소 | 실행 위치 | 역할 |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, 앱으로 실행 (CIA 또는 `.3dsx`) | 포트 **8080**의 HTTP/JSON 서버: 상태, 타이틀 목록, CIA 설치/삭제, 타이틀 실행, SD 카드 파일, 재시작/전원 끄기 |
| Rosalina의 **InputRedirection** | 3DS, 백그라운드 | UDP **4950**으로 버튼, 터치, 슬라이드 패드 입력을 받습니다 (게임 중에도 가능) |
| **NTR-HR** (리모트 플레이) | 3DS, 백그라운드 | 화면을 스트리밍하고, 클라이언트가 한 프레임을 스크린샷으로 가져옵니다 (TCP **8000** + UDP **8001**) |

클라이언트 `3ds`(Python 3, 표준 라이브러리만 사용)가 세 부분 모두와 통신합니다. `screenshot`은 macOS의 `sips`로 이미지를 회전하며, 나머지는 Python 3가 있는 곳이면 어디서나 동작합니다.

## 사용법

처음에는 컴퓨터와 본체를 페어링합니다. 3DS Remote에서 **Y**를 누르면 비밀번호가 표시됩니다:

```sh
3ds login --host 192.168.1.241    # 비밀번호를 입력받아 ~/.config/3ds-remote/config.json (600)에 저장
```

```sh
3ds ping                          # 비밀번호 없이: 버전과 비밀번호 사용 여부

3ds status                        # 배터리, Wi-Fi, SD 카드, 모델, 펌웨어, Luma
3ds titles [--all] [--json]       # 설치된 타이틀과 이름
3ds install game.cia [...]        # 같은 버전이 이미 설치되어 있으면 건너뜀 (--force)
3ds launch <name|tid>             # 타이틀 실행 (서버는 종료됨)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # GitHub 최신 릴리스 설치

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png
```

`THREEDS=ip[:포트]`와 `THREEDS_TOKEN=<비밀번호>`는 설정 파일보다 우선합니다. `3ds logout`은 저장된 비밀번호를 지웁니다.

`press`/`touch`/`drag`/`stick`에는 InputRedirection이, `screenshot`에는 NTR-HR이 필요합니다. 둘 다 서버를 열어 둘 필요는 없습니다.

## 본체 화면

| 화면 | 내용 |
|---|---|
| 위 화면 | 주소, 상태 (온라인 / 일시 정지 / 네트워크 없음), 비밀번호 (숨김), 배터리, Wi-Fi, 전송 진행 상황, 최근 요청 |
| 아래 화면 (터치) | 비밀번호 표시 (**Y**), 새 무작위 비밀번호 (**X**), 키보드로 비밀번호 설정, 비밀번호 요구 켜기/끄기, 일시 정지 (**SELECT**), 종료 (**START**), 언어 (**L/R**) |

## 언어

앱 화면은 3DS의 12개 언어를 모두 지원합니다: 포르투갈어, 영어, 스페인어, 러시아어, 일본어, 프랑스어, 독일어, 이탈리아어, 네덜란드어, 중국어 간체, 한국어, 중국어 번체. 기본값은 시스템 언어를 따릅니다. **L/R** 또는 아래 화면 모서리의 선택기로 언어를 바꿀 수 있으며, 선택은 `config.ini`에 저장됩니다 (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

중국어와 한국어는 필요할 때 시스템 글꼴 CHN/KOR/TWN을 불러옵니다.

문구를 번역하거나 고치려면 `source/i18n.c`를 수정하세요. 번역이 없는 항목은 영어로 표시됩니다.

## 보안

- `/ping`을 제외한 모든 경로에 **비밀번호가 필요**합니다 (`Authorization: Bearer <비밀번호>`). 처음 실행할 때 앱이 12자리 무작위 비밀번호를 만들어 `sdmc:/config/3ds-remote/config.ini`에 저장합니다.
- 비밀번호는 **본체에서만 바꿀 수 있습니다**. 설정을 바꾸는 엔드포인트는 없고, API로 `config.ini`를 읽거나 쓸 수도 없습니다.
- **비밀번호를 5번 연속 틀리면** 30초 동안 로그인이 막힙니다 (HTTP 429).
- `..`나 `\`가 들어간 경로는 거부합니다.
- 모든 네트워크 읽기와 쓰기는 15초 후 시간 초과되므로, 멈춘 클라이언트가 서버를 붙잡지 못합니다.
- **일시 정지**하면 포트를 실제로 닫고, 서버는 앱이 열려 있는 동안에만 대기합니다.
- 비밀번호를 끄려면 확인이 필요합니다 (두 번 탭).
- **제한:** TLS 없는 HTTP이므로 비밀번호가 로컬 네트워크에서 평문으로 전송됩니다. 신뢰할 수 있는 네트워크에서만 사용하세요.

## 3DS를 켤 때마다

1. **Boot NTR Selector** 열기 → 기본 경로 → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. 서버를 쓸 때: HOME 메뉴에서 **3DS Remote** 열기.

## 개발

빌드, CI, 엔드포인트 목록, 기술 메모는 [영어 README](../README.md#build)를 참고하세요.
