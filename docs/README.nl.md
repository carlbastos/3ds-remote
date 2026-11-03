# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · **Nederlands** · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Bestuur een New 3DS met Luma3DS via het netwerk vanaf je computer.

## Installeren

Open op de 3DS **FBI → Remote Install → Scan QR Code**:

![QR-code van de nieuwste versie](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Elke [release](https://github.com/carlbastos/3ds-remote/releases) bevat `3ds-remote.cia`, `3ds-remote.3dsx`, de client `3ds` en de QR-code van die versie.

## Hoe het werkt

Er zijn drie onderdelen:

| Onderdeel | Draait op | Wat het doet |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, als app (CIA of `.3dsx`) | HTTP/JSON-server op poort **8080**: status, titels, CIA's installeren/verwijderen, titels starten, bestanden op de SD-kaart, herstarten/uitschakelen |
| **InputRedirection** van Rosalina | 3DS, op de achtergrond | Ontvangt knoppen, aanraakscherm en Circle Pad via UDP **4950**, ook in games |
| **NTR-HR** (remote play) | 3DS, op de achtergrond | Streamt de schermen; de client pakt één beeld als screenshot (TCP **8000** + UDP **8001**) |

De client `3ds` werkt op Windows, macOS en Linux en praat met alle drie.

## De client installeren

Met Python 3.9 of nieuwer, op elk besturingssysteem:

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

Zonder Python download je het uitvoerbare bestand voor jouw systeem uit de [nieuwste release](https://github.com/carlbastos/3ds-remote/releases/latest): `3ds-windows-x64.exe`, `3ds-macos-arm64` of `3ds-linux-x64`. Op macOS en Linux eerst `chmod +x`; macOS vraagt mogelijk om toestemming in *Systeeminstellingen → Privacy en beveiliging*, omdat het bestand niet ondertekend is.

`3ds config` toont waar de instellingen staan (`%APPDATA%\3ds-remote` op Windows, `~/.config/3ds-remote` op macOS en Linux). `screenshot` ontvangt het beeld op UDP-poort **8001**, dus de eerste keer kan de firewall om toestemming vragen.

## Gebruik

Koppel de eerste keer je computer aan de console. Druk in 3DS Remote op **Y** om het wachtwoord te zien:

```sh
3ds login --host 192.168.1.241    # vraagt het wachtwoord en bewaart het in ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # zonder wachtwoord: versie en of het wachtwoord aan staat

3ds status                        # batterij, wifi, SD-kaart, model, firmware, Luma
3ds titles [--all] [--json]       # geïnstalleerde titels met naam
3ds install game.cia [...]        # slaat CIA's over waarvan de versie al geïnstalleerd is (--force)
3ds launch <name|tid>             # start de titel (de server sluit)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # installeert de nieuwste GitHub-release

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png   # PNG, JPEG, WebP
```

`THREEDS=ip[:poort]` en `THREEDS_TOKEN=<wachtwoord>` gaan voor het configuratiebestand. `3ds logout` wist het bewaarde wachtwoord.

`press`/`touch`/`drag`/`stick` hebben InputRedirection nodig; `screenshot` heeft NTR-HR nodig. Voor geen van beide hoeft de server open te zijn.

## Op de console

| Scherm | Inhoud |
|---|---|
| Boven | Adres, status (ONLINE / GEPAUZEERD / GEEN NETWERK), wachtwoord (verborgen), batterij, wifi, voortgang van overdrachten en de laatste verzoeken |
| Onder (aanraak) | Wachtwoord tonen (**Y**), nieuw willekeurig wachtwoord (**X**), wachtwoord instellen met het toetsenbord, wachtwoord vereisen aan/uit, pauzeren (**SELECT**), afsluiten (**START**), taal (**L/R**) |

## Talen

De interface is beschikbaar in alle 12 talen van de 3DS: Portugees, Engels, Spaans, Russisch, Japans, Frans, Duits, Italiaans, Nederlands, vereenvoudigd Chinees, Koreaans en traditioneel Chinees. Standaard volgt hij de systeemtaal. **L/R**, of de keuzeknop in de hoek van het onderste scherm, wisselt van taal; de keuze wordt bewaard in `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Chinees en Koreaans gebruiken de systeemlettertypen CHN/KOR/TWN, die de app laadt wanneer dat nodig is.

Teksten vertalen of verbeteren: `source/i18n.c`. Ontbreekt een vertaling, dan verschijnt de Engelse tekst.

## Beveiliging

- **Wachtwoord verplicht** op alle routes behalve `/ping`, via `Authorization: Bearer <wachtwoord>`. Bij de eerste start maakt de app een willekeurig wachtwoord van 12 tekens en bewaart het in `sdmc:/config/3ds-remote/config.ini`.
- Het wachtwoord **kan alleen op de console worden gewijzigd**. Geen enkel endpoint wijzigt instellingen, en de API kan `config.ini` niet lezen of schrijven.
- **5 foute wachtwoorden achter elkaar** blokkeren inloggen 30 s lang (HTTP 429).
- Paden met `..` of `\` worden geweigerd.
- Elke netwerklees- en schrijfactie stopt na 15 s, zodat een vastgelopen client de server niet blokkeert.
- **Pauzeren** sluit de poort echt, en de server luistert alleen zolang de app open is.
- Het wachtwoord uitzetten vraagt om bevestiging (twee keer tikken).
- **Beperking:** het is HTTP zonder TLS, dus het wachtwoord gaat onversleuteld over het lokale netwerk. Gebruik het alleen op een vertrouwd netwerk.

## Na elke start van de 3DS

1. Open **Boot NTR Selector** → standaardpad → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Voor de server: open **3DS Remote** in het HOME-menu.

## Ontwikkeling

Bouwen, CI, de lijst met endpoints en technische notities staan in de [Engelse README](../README.md#build).
