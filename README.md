# 3ds-remote

Controle de um New 3DS (Luma3DS) pela rede, a partir do Mac.

São três peças:

| Peça | Onde roda | O que faz |
|---|---|---|
| **3DS Remote** (`source/main.c`) | 3DS, como app (CIA ou `.3dsx`) | Servidor HTTP/JSON na porta **8080**: status, títulos, instalar/remover CIA, abrir títulos, arquivos do SD, reboot/shutdown |
| **InputRedirection** da Rosalina | 3DS, em segundo plano | Recebe botões, toque e analógico por UDP **4950**, inclusive dentro de jogos |
| **NTR-HR** (remote play) | 3DS, em segundo plano | Transmite as telas; o cliente pega um quadro como screenshot (TCP **8000** + UDP **8001**) |

O cliente `3ds` (Python 3, só biblioteca padrão) fala com as três.

## Uso

```sh
export THREEDS=192.168.1.241      # padrão; aceita ip:porta

3ds status                        # bateria, Wi-Fi, SD, modelo, firmware, Luma
3ds titles [--all] [--json]       # títulos instalados com nome
3ds install jogo.cia [...]        # pula se a mesma versão já estiver instalada (--force)
3ds launch <nome|tid>             # abre o título (o servidor fecha)
3ds delete <nome|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] arquivo.png
```

Os comandos `press`/`touch`/`drag`/`stick` precisam do InputRedirection ligado; `screenshot` precisa do NTR-HR carregado. Nenhum dos dois depende do servidor estar aberto.

## Rotina a cada boot do 3DS

1. Abrir **Boot NTR Selector** → caminho padrão → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Para o servidor: abrir **3DS Remote** (pasta H do menu).

## Build

Requisitos: devkitPro com `3ds-dev` em `/opt/devkitpro`.

```sh
./build-cia.sh      # gera 3ds-remote.3dsx e 3ds-remote.cia
```

Na primeira vez, `tools/fetch-tools.sh` baixa o makerom 0.19.0 (Project_CTR) e compila o bannertool 1.2.3 (fork do carstene1ns) em `tools/`. Nada disso é versionado.

Para atualizar o app instalado: subir `VERSION`, rodar `./build-cia.sh` e `3ds install 3ds-remote.cia`. O 3DS recusa CIA de mesma versão (`0xC8E083FC`).

Para testar sem instalar: Homebrew Launcher → **Y**, depois
`/opt/devkitpro/tools/bin/3dslink -a 192.168.1.241 3ds-remote.3dsx`.

## Endpoints

| Método | Caminho | Notas |
|---|---|---|
| GET | `/status` | |
| GET | `/titles?media=sd\|nand\|card` | nome vem do SMDH |
| POST | `/install?media=sd` | corpo = CIA cru, com `Content-Length` |
| POST | `/delete?tid=HEX&media=sd` | |
| POST | `/launch?tid=HEX&media=sd` | o app sai para abrir o título |
| GET | `/ls?path=/dir` | |
| GET/PUT/DELETE | `/file?path=/x` | PUT cria as pastas pai |
| POST | `/reboot`, `/shutdown`, `/exit` | |

Erros vêm como `{"error": "...", "result": "0x..."}`.

## Notas

- **NTR-HR**: o comando de remote play (901) precisa dos argumentos no formato do NTRViewer-HR (`arg3 = 1404036572`, `arg4 = porta UDP`). O formato antigo do NTR derruba a rede do NTR até reiniciar o console.
- **Mover ícone no HOME Menu** pelo `drag`: segurar ~2 s levanta o ícone; parar ~4 s sobre uma pasta abre a pasta; soltar só funciona em espaço **vazio**.
- `meta/app.rsf` vem do template do buildtools (Steveice10). Title ID `000400000FE3D500`, product code `CTR-P-RMTE`.
- `tools/make_art.py` gera `meta/icon.png`, `meta/banner.png` e `meta/audio.wav`.
