# 3ds-remote

[English](../README.md) · **Português** · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Controle de um New 3DS (Luma3DS) pela rede, a partir do Mac.

## Instalar

No 3DS, pelo **FBI → Remote Install → Scan QR Code**:

![QR code da última versão](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Cada [release](https://github.com/carlbastos/3ds-remote/releases) traz `3ds-remote.cia`, `3ds-remote.3dsx`, o cliente `3ds` e o QR daquela versão.

## Como funciona

São três peças:

| Peça | Onde roda | O que faz |
|---|---|---|
| **3DS Remote** (`source/main.c`) | 3DS, como app (CIA ou `.3dsx`) | Servidor HTTP/JSON na porta **8080**: status, títulos, instalar/remover CIA, abrir títulos, arquivos do SD, reboot/shutdown |
| **InputRedirection** da Rosalina | 3DS, em segundo plano | Recebe botões, toque e analógico por UDP **4950**, inclusive dentro de jogos |
| **NTR-HR** (remote play) | 3DS, em segundo plano | Transmite as telas; o cliente pega um quadro como screenshot (TCP **8000** + UDP **8001**) |

O cliente `3ds` roda no Windows, no macOS e no Linux e fala com as três.

## Instalar o cliente

Com Python 3.9 ou mais novo, em qualquer sistema:

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

(`pip install` também funciona; o [pipx](https://pipx.pypa.io) deixa o cliente num ambiente só dele.) Sem Python, baixe o executável do seu sistema na [última release](https://github.com/carlbastos/3ds-remote/releases/latest): `3ds-windows-x64.exe`, `3ds-macos-arm64` ou `3ds-linux-x64`. No macOS e no Linux, rode `chmod +x` antes; o macOS pode pedir para liberar o arquivo em *Ajustes do Sistema → Privacidade e Segurança*, porque ele não é assinado.

| Sistema | Arquivo de configuração |
|---|---|
| Windows | `%APPDATA%\3ds-remote\config.json` |
| macOS, Linux | `~/.config/3ds-remote/config.json` (ou `$XDG_CONFIG_HOME`) |

`3ds config` mostra onde ele está. O `screenshot` recebe a imagem pela porta UDP **8001**, então na primeira vez o firewall (o do Windows, por exemplo) pode pedir permissão.

## Uso

Na primeira vez, pareie o Mac com o console. A senha aparece no 3DS Remote ao apertar **Y**:

```sh
3ds login --host 192.168.1.241    # pede a senha e salva em ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # sem senha: versão e se a senha está ligada

3ds status                        # bateria, Wi-Fi, SD, modelo, firmware, Luma
3ds titles [--all] [--json]       # títulos instalados com nome
3ds install jogo.cia [...]        # pula se a mesma versão já estiver instalada (--force)
3ds launch <nome|tid>             # abre o título (o servidor fecha)
3ds delete <nome|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # instala a última release do GitHub

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # segura e desliza pelos pontos x,y[:ms], depois solta
3ds snap [arquivo.png]  # as duas telas numa imagem (tela de baixo em +40,+240)
3ds screenshot [--screen bottom] arquivo.png   # PNG, JPEG, WebP... pela extensão
```

`THREEDS=ip[:porta]` e `THREEDS_TOKEN=<senha>` sobrescrevem o arquivo de configuração. `3ds logout` apaga a senha salva.

Os comandos `press`/`touch`/`drag`/`stick` precisam do InputRedirection ligado; `screenshot` precisa do NTR-HR carregado. Nenhum dos dois depende do servidor estar aberto.

## No console

| Tela | Conteúdo |
|---|---|
| Superior | Endereço, estado (ONLINE / PAUSADO / SEM REDE), senha (oculta), bateria, Wi-Fi, progresso de transferências e os últimos pedidos |
| Inferior (toque) | Mostrar senha (**Y**), nova senha aleatória (**X**), definir senha pelo teclado, ligar/desligar a exigência de senha, pausar (**SELECT**), sair (**START**), idioma (**L/R**) |

## Idiomas

A interface do app está nos 12 idiomas do 3DS: português, inglês, espanhol, russo, japonês, francês, alemão, italiano, holandês, chinês simplificado, coreano e chinês tradicional. Por padrão ela segue o idioma do sistema. **L/R** ou o seletor no canto da tela de baixo trocam o idioma (*automático* → Português → … → 繁體中文), e a escolha fica salva no `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Chinês e coreano usam as fontes de sistema CHN/KOR/TWN, que o app carrega quando precisa. Cada linha do log é desenhada com a fonte do idioma em que foi registrada.

Para traduzir ou corrigir textos: `source/i18n.c`. Uma tradução que falte cai para o inglês.

## Segurança

- **Senha obrigatória** em todas as rotas, menos `/ping`, via `Authorization: Bearer <senha>`. Na primeira execução o app gera uma senha aleatória de 12 caracteres (gerador do serviço `ssl:C`) e a guarda em `sdmc:/config/3ds-remote/config.ini`.
- Versões até a 0.2.0 guardavam a configuração em `/3ds/3ds-remote/`. O app move o arquivo para `/config/3ds-remote/` sozinho, porque o Homebrew Launcher lista toda pasta dentro de `/3ds` como se fosse um app.
- A senha **só muda no console** (tela de toque). Nenhum endpoint altera a configuração e o `config.ini` não pode ser lido nem escrito pela API.
- **5 senhas erradas seguidas** bloqueiam novos logins por 30 s (HTTP 429).
- Caminhos com `..` ou `\` são recusados.
- Toda leitura e escrita de rede tem tempo limite de 15 s, para um cliente parado não travar o servidor.
- **Pausar** fecha a porta de verdade, e o servidor só escuta enquanto o app está aberto.
- Desligar a senha pede confirmação (dois toques).
- **Limite:** é HTTP sem TLS, então a senha passa em texto puro pela rede local. Use só em rede de confiança.

## Rotina a cada boot do 3DS

1. Abrir **Boot NTR Selector** → caminho padrão → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Para o servidor: abrir **3DS Remote** no HOME Menu.

## Build

Requisitos: devkitPro com `3ds-dev` em `/opt/devkitpro`.

```sh
./build-cia.sh      # gera 3ds-remote.3dsx e 3ds-remote.cia
```

Na primeira vez, `tools/fetch-tools.sh` baixa o makerom 0.19.0 (Project_CTR) e compila o bannertool 1.2.3 (fork do carstene1ns) em `tools/`. Nada disso é versionado.

Desenvolvimento do cliente: `pip install -e ./client` e depois `python -m unittest discover -s client/tests`. Num clone do repo também dá para rodar `./3ds` direto.

O 3DS recusa CIA de mesma versão (`0xC8E083FC`), por isso toda mudança no app precisa de uma versão nova em `VERSION`.

## CI e releases

O workflow [`build`](../.github/workflows/build.yml) roda no container `devkitpro/devkitarm`:

- **push / PR:** compila o `.3dsx` e o CIA, testa o cliente no Linux, no macOS e no Windows (Python 3.9 e 3.13), gera os executáveis do cliente e guarda tudo como artifact do run.
- **tag `vX.Y.Z`:** confere se a tag (e a versão do cliente) bate com `VERSION`, compila e publica a release com CIA, 3dsx, QR code e os executáveis do cliente.

Para lançar uma versão:

```sh
tools/release.sh X.Y.Z     # atualiza VERSION, commita, cria a tag vX.Y.Z e faz push
gh run watch               # acompanha o build
3ds update                 # instala no 3DS (com o servidor aberto)
```

Para testar sem instalar: Homebrew Launcher → **Y**, depois
`/opt/devkitpro/tools/bin/3dslink -a 192.168.1.241 3ds-remote.3dsx`.

## Endpoints

| Método | Caminho | Notas |
|---|---|---|
| GET | `/ping` | sem senha |
| GET | `/status` | |
| GET | `/titles?media=sd\|nand\|card` | nome vem do SMDH |
| POST | `/install?media=sd` | corpo = CIA cru, com `Content-Length` |
| POST | `/delete?tid=HEX&media=sd` | |
| POST | `/launch?tid=HEX&media=sd` | o app sai para abrir o título |
| GET | `/ls?path=/dir` | |
| GET/PUT/DELETE | `/file?path=/x` | PUT cria as pastas pai |
| POST | `/reboot`, `/shutdown`, `/exit` | |

Todas as rotas, menos `/ping`, exigem `Authorization: Bearer <senha>` (ou `X-Auth-Token`). Erros vêm como `{"error": "...", "result": "0x..."}`, com 401 (sem senha ou senha errada) e 429 (bloqueado).

## Notas

- **NTR-HR**: o comando de remote play (901) precisa dos argumentos no formato do NTRViewer-HR (`arg3 = 1404036572`, `arg4 = porta UDP`). O formato antigo do NTR derruba a rede do NTR até reiniciar o console.
- **Mover ícone no HOME Menu** pelo `drag`: segurar ~2 s levanta o ícone; parar ~4 s sobre uma pasta abre a pasta; soltar só funciona em espaço **vazio**.
- **Versão do CIA**: o makerom 0.19.0 ignora `-ver`/`-major`/`-minor`/`-micro` em builds a partir do ELF e só usa o `RemasterVersion` do RSF como major. O `build-cia.sh` passa o major pelo RSF e o `tools/set-cia-version.py` grava o X.Y.Z completo no TMD e no ticket (confira com `ctrtool -p --intype=cia`). Por isso a primeira release válida é a v0.1.1.
- `meta/app.rsf` vem do template do buildtools (Steveice10). Title ID `000400000FE3D500`, product code `CTR-P-RMTE`.
- `tools/make_art.py` gera `meta/icon.png`, `meta/banner.png` e `meta/audio.wav`.
