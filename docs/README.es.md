# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · **Español** · [Русский](README.ru.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Controla una New 3DS con Luma3DS por la red desde tu ordenador.

## Instalación

En la 3DS, abre **FBI → Remote Install → Scan QR Code**:

![Código QR de la última versión](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Cada [versión](https://github.com/carlbastos/3ds-remote/releases) incluye `3ds-remote.cia`, `3ds-remote.3dsx`, el cliente `3ds` y el código QR de esa versión.

## Cómo funciona

Son tres piezas:

| Pieza | Dónde se ejecuta | Qué hace |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, como app (CIA o `.3dsx`) | Servidor HTTP/JSON en el puerto **8080**: estado, títulos, instalar/eliminar CIA, abrir títulos, archivos de la SD, reinicio/apagado |
| **InputRedirection** de Rosalina | 3DS, en segundo plano | Recibe botones, pantalla táctil y stick por UDP **4950**, también dentro de los juegos |
| **NTR-HR** (remote play) | 3DS, en segundo plano | Transmite las pantallas; el cliente toma un fotograma como captura (TCP **8000** + UDP **8001**) |

El cliente `3ds` (Python 3, solo biblioteca estándar) habla con las tres. `screenshot` usa `sips` de macOS para girar la imagen; el resto funciona en cualquier sistema con Python 3.

## Uso

La primera vez, empareja tu ordenador con la consola. Pulsa **Y** en 3DS Remote para ver la contraseña:

```sh
3ds login --host 192.168.1.241    # pide la contraseña y la guarda en ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # sin contraseña: versión y si la contraseña está activada

3ds status                        # batería, Wi-Fi, SD, modelo, firmware, Luma
3ds titles [--all] [--json]       # títulos instalados con nombre
3ds install game.cia [...]        # omite los CIA cuya versión ya está instalada (--force)
3ds launch <name|tid>             # abre el título (el servidor se cierra)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # instala la última versión de GitHub

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png
```

`THREEDS=ip[:puerto]` y `THREEDS_TOKEN=<contraseña>` tienen prioridad sobre el archivo de configuración. `3ds logout` borra la contraseña guardada.

`press`/`touch`/`drag`/`stick` necesitan InputRedirection activado; `screenshot` necesita NTR-HR cargado. Ninguno de los dos depende de que el servidor esté abierto.

## En la consola

| Pantalla | Contenido |
|---|---|
| Superior | Dirección, estado (EN LÍNEA / EN PAUSA / SIN RED), contraseña (oculta), batería, Wi-Fi, progreso de transferencias y las últimas peticiones |
| Inferior (táctil) | Mostrar contraseña (**Y**), nueva contraseña aleatoria (**X**), definir contraseña con el teclado, activar/desactivar la contraseña, pausar (**SELECT**), salir (**START**), idioma (**L/R**) |

## Idiomas

La interfaz de la app está en los 12 idiomas de la 3DS: portugués, inglés, español, ruso, japonés, francés, alemán, italiano, neerlandés, chino simplificado, coreano y chino tradicional. Por defecto sigue el idioma del sistema. **L/R**, o el selector en la esquina de la pantalla inferior, cambian de idioma, y la elección se guarda en `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

El chino y el coreano usan las fuentes del sistema CHN/KOR/TWN, que la app carga cuando las necesita.

Para traducir o corregir textos, edita `source/i18n.c`. Una traducción que falte se muestra en inglés.

## Seguridad

- **Contraseña obligatoria** en todas las rutas excepto `/ping`, mediante `Authorization: Bearer <contraseña>`. En el primer arranque la app genera una contraseña aleatoria de 12 caracteres y la guarda en `sdmc:/config/3ds-remote/config.ini`.
- La contraseña **solo se cambia en la consola**. Ningún endpoint modifica la configuración, y la API no puede leer ni escribir `config.ini`.
- **5 contraseñas incorrectas seguidas** bloquean el acceso durante 30 s (HTTP 429).
- Se rechazan las rutas con `..` o `\`.
- Toda lectura y escritura de red caduca a los 15 s, para que un cliente parado no bloquee el servidor.
- **Pausar** cierra el puerto de verdad, y el servidor solo escucha mientras la app está abierta.
- Desactivar la contraseña pide confirmación (dos toques).
- **Limitación:** es HTTP sin TLS, así que la contraseña viaja en texto plano por la red local. Úsalo solo en una red de confianza.

## Después de cada arranque de la 3DS

1. Abre **Boot NTR Selector** → ruta predeterminada → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Para el servidor: abre **3DS Remote** desde el menú HOME.

## Desarrollo

La compilación, la integración continua, la lista de endpoints y las notas técnicas están en el [README en inglés](../README.md#build).
