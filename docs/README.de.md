# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · **Deutsch** · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Steuere einen New 3DS mit Luma3DS über das Netzwerk von deinem Computer aus.

## Installation

Öffne auf dem 3DS **FBI → Remote Install → Scan QR Code**:

![QR-Code der neuesten Version](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Jedes [Release](https://github.com/carlbastos/3ds-remote/releases) enthält `3ds-remote.cia`, `3ds-remote.3dsx`, den Client `3ds` und den QR-Code dieser Version.

## Funktionsweise

Es gibt drei Teile:

| Teil | Läuft auf | Aufgabe |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, als App (CIA oder `.3dsx`) | HTTP/JSON-Server auf Port **8080**: Status, Titel, CIAs installieren/entfernen, Titel starten, Dateien auf der SD-Karte, Neustart/Ausschalten |
| **InputRedirection** von Rosalina | 3DS, im Hintergrund | Empfängt Tasten, Touch und Schiebepad über UDP **4950**, auch in Spielen |
| **NTR-HR** (Remote Play) | 3DS, im Hintergrund | Überträgt die Bildschirme; der Client holt sich ein Bild als Screenshot (TCP **8000** + UDP **8001**) |

Der Client `3ds` (Python 3, nur Standardbibliothek) spricht mit allen drei. `screenshot` dreht das Bild mit `sips` von macOS; alles andere läuft überall, wo Python 3 läuft.

## Benutzung

Verbinde beim ersten Mal deinen Computer mit der Konsole. Drücke in 3DS Remote **Y**, um das Passwort anzuzeigen:

```sh
3ds login --host 192.168.1.241    # fragt nach dem Passwort und speichert es in ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # ohne Passwort: Version und ob das Passwort aktiv ist

3ds status                        # Akku, WLAN, SD-Karte, Modell, Firmware, Luma
3ds titles [--all] [--json]       # installierte Titel mit Namen
3ds install game.cia [...]        # überspringt CIAs, deren Version schon installiert ist (--force)
3ds launch <name|tid>             # startet den Titel (der Server wird beendet)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # installiert das neueste GitHub-Release

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png
```

`THREEDS=ip[:port]` und `THREEDS_TOKEN=<passwort>` haben Vorrang vor der Konfigurationsdatei. `3ds logout` löscht das gespeicherte Passwort.

`press`/`touch`/`drag`/`stick` brauchen InputRedirection, `screenshot` braucht NTR-HR. Für beides muss der Server nicht offen sein.

## Auf der Konsole

| Bildschirm | Inhalt |
|---|---|
| Oben | Adresse, Status (ONLINE / PAUSIERT / KEIN NETZ), Passwort (verborgen), Akku, WLAN, Fortschritt von Übertragungen und die letzten Anfragen |
| Unten (Touch) | Passwort zeigen (**Y**), neues Zufallspasswort (**X**), Passwort per Tastatur festlegen, Passwortpflicht an/aus, Pause (**SELECT**), Beenden (**START**), Sprache (**L/R**) |

## Sprachen

Die Oberfläche gibt es in allen 12 Sprachen des 3DS: Portugiesisch, Englisch, Spanisch, Russisch, Japanisch, Französisch, Deutsch, Italienisch, Niederländisch, vereinfachtes Chinesisch, Koreanisch und traditionelles Chinesisch. Standardmäßig folgt sie der Systemsprache. **L/R** oder die Auswahl in der Ecke des unteren Bildschirms wechseln die Sprache; die Wahl wird in `config.ini` gespeichert (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Für Chinesisch und Koreanisch lädt die App bei Bedarf die Systemschriften CHN/KOR/TWN.

Texte übersetzen oder korrigieren: `source/i18n.c`. Fehlt eine Übersetzung, erscheint der englische Text.

## Sicherheit

- **Passwort erforderlich** auf allen Routen außer `/ping`, per `Authorization: Bearer <passwort>`. Beim ersten Start erzeugt die App ein zufälliges Passwort mit 12 Zeichen und speichert es in `sdmc:/config/3ds-remote/config.ini`.
- Das Passwort **lässt sich nur an der Konsole ändern**. Kein Endpoint ändert Einstellungen, und die API kann `config.ini` weder lesen noch schreiben.
- **5 falsche Passwörter hintereinander** sperren Anmeldungen für 30 s (HTTP 429).
- Pfade mit `..` oder `\` werden abgelehnt.
- Jedes Lesen und Schreiben im Netzwerk bricht nach 15 s ab, damit ein hängender Client den Server nicht blockiert.
- **Pause** schließt den Port wirklich, und der Server lauscht nur, solange die App offen ist.
- Das Abschalten des Passworts muss bestätigt werden (zweimal tippen).
- **Einschränkung:** Es ist HTTP ohne TLS, das Passwort geht also im Klartext durchs lokale Netz. Nur in vertrauenswürdigen Netzen verwenden.

## Nach jedem Start des 3DS

1. **Boot NTR Selector** öffnen → Standardpfad → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Für den Server: **3DS Remote** im HOME-Menü öffnen.

## Entwicklung

Build, CI, die Liste der Endpoints und technische Hinweise stehen im [englischen README](../README.md#build).
