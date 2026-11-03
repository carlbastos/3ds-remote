# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Italiano** · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Controlla un New 3DS con Luma3DS in rete, dal tuo computer.

## Installazione

Sul 3DS apri **FBI → Remote Install → Scan QR Code**:

![Codice QR dell'ultima versione](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Ogni [release](https://github.com/carlbastos/3ds-remote/releases) contiene `3ds-remote.cia`, `3ds-remote.3dsx`, il client `3ds` e il codice QR di quella versione.

## Come funziona

Ci sono tre parti:

| Parte | Dove gira | Cosa fa |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, come app (CIA o `.3dsx`) | Server HTTP/JSON sulla porta **8080**: stato, titoli, installazione/rimozione di CIA, avvio dei titoli, file della scheda SD, riavvio/spegnimento |
| **InputRedirection** di Rosalina | 3DS, in background | Riceve pulsanti, touch e Circle Pad via UDP **4950**, anche dentro i giochi |
| **NTR-HR** (remote play) | 3DS, in background | Trasmette gli schermi; il client prende un fotogramma come screenshot (TCP **8000** + UDP **8001**) |

Il client `3ds` funziona su Windows, macOS e Linux e comunica con tutte e tre.

## Installare il client

Con Python 3.9 o successivo, su qualsiasi sistema:

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

Senza Python, scarica l'eseguibile per il tuo sistema dall'[ultima release](https://github.com/carlbastos/3ds-remote/releases/latest): `3ds-windows-x64.exe`, `3ds-macos-arm64` o `3ds-linux-x64`. Su macOS e Linux esegui prima `chmod +x`; macOS potrebbe chiedere di autorizzarlo in *Impostazioni di Sistema → Privacy e sicurezza*, perché non è firmato.

`3ds config` mostra dove sono salvate le impostazioni (`%APPDATA%\3ds-remote` su Windows, `~/.config/3ds-remote` su macOS e Linux). `screenshot` riceve l'immagine sulla porta UDP **8001**, quindi la prima volta il firewall potrebbe chiedere il permesso.

## Uso

La prima volta, abbina il computer alla console. Premi **Y** in 3DS Remote per vedere la password:

```sh
3ds login --host 192.168.1.241    # chiede la password e la salva in ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # senza password: versione e se la password è attiva

3ds status                        # batteria, Wi-Fi, scheda SD, modello, firmware, Luma
3ds titles [--all] [--json]       # titoli installati con il nome
3ds install game.cia [...]        # salta i CIA la cui versione è già installata (--force)
3ds launch <name|tid>             # avvia il titolo (il server si chiude)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # installa l'ultima release di GitHub

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # x,y[:ms] ...
3ds snap [file.png]                           # 400x480
3ds screenshot [--screen bottom] file.png     # PNG, JPEG, WebP
```

`THREEDS=ip[:porta]` e `THREEDS_TOKEN=<password>` hanno la precedenza sul file di configurazione. `3ds logout` cancella la password salvata.

`press`/`touch`/`drag`/`stick` richiedono InputRedirection attivo; `screenshot` richiede NTR-HR caricato. Nessuno dei due ha bisogno che il server sia aperto.

## Sulla console

| Schermo | Contenuto |
|---|---|
| Superiore | Indirizzo, stato (ONLINE / IN PAUSA / NESSUNA RETE), password (nascosta), batteria, Wi-Fi, avanzamento dei trasferimenti e ultime richieste |
| Inferiore (touch) | Mostra password (**Y**), nuova password casuale (**X**), imposta la password con la tastiera, attiva/disattiva la password, pausa (**SELECT**), esci (**START**), lingua (**L/R**) |

## Lingue

L'interfaccia è disponibile in tutte le 12 lingue del 3DS: portoghese, inglese, spagnolo, russo, giapponese, francese, tedesco, italiano, olandese, cinese semplificato, coreano e cinese tradizionale. Di default segue la lingua di sistema. **L/R**, o il selettore nell'angolo dello schermo inferiore, cambiano lingua; la scelta viene salvata in `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Cinese e coreano usano i font di sistema CHN/KOR/TWN, caricati quando servono.

Per tradurre o correggere i testi, modifica `source/i18n.c`. Una traduzione mancante viene mostrata in inglese.

## Sicurezza

- **Password obbligatoria** su tutte le rotte tranne `/ping`, tramite `Authorization: Bearer <password>`. Al primo avvio l'app genera una password casuale di 12 caratteri e la salva in `sdmc:/config/3ds-remote/config.ini`.
- La password **si cambia solo sulla console**. Nessun endpoint modifica le impostazioni, e l'API non può né leggere né scrivere `config.ini`.
- **5 password errate di fila** bloccano gli accessi per 30 s (HTTP 429).
- I percorsi con `..` o `\` vengono rifiutati.
- Ogni lettura e scrittura di rete scade dopo 15 s, così un client bloccato non blocca il server.
- **Pausa** chiude davvero la porta, e il server resta in ascolto solo mentre l'app è aperta.
- Disattivare la password richiede una conferma (due tocchi).
- **Limite:** è HTTP senza TLS, quindi la password viaggia in chiaro sulla rete locale. Usalo solo su una rete fidata.

## Dopo ogni avvio del 3DS

1. Apri **Boot NTR Selector** → percorso predefinito → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Per il server: apri **3DS Remote** dal menu HOME.

## Sviluppo

Compilazione, CI, elenco degli endpoint e note tecniche sono nel [README in inglese](../README.md#build).
