# 3ds-remote

[English](../README.md) · [Português](README.pt-BR.md) · [Español](README.es.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · **Français** · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [繁體中文](README.zh-TW.md)

[![build](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml/badge.svg)](https://github.com/carlbastos/3ds-remote/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)](https://github.com/carlbastos/3ds-remote/releases/latest)

Pilotez une New 3DS sous Luma3DS par le réseau, depuis votre ordinateur.

## Installation

Sur la 3DS, ouvrez **FBI → Remote Install → Scan QR Code** :

![QR code de la dernière version](https://github.com/carlbastos/3ds-remote/releases/latest/download/3ds-remote-qr.png)

Chaque [version](https://github.com/carlbastos/3ds-remote/releases) contient `3ds-remote.cia`, `3ds-remote.3dsx`, le client `3ds` et le QR code de cette version.

## Fonctionnement

Trois éléments :

| Élément | Où il tourne | Rôle |
|---|---|---|
| **3DS Remote** (`source/`) | 3DS, en tant qu'app (CIA ou `.3dsx`) | Serveur HTTP/JSON sur le port **8080** : état, titres, installation/suppression de CIA, lancement de titres, fichiers de la carte SD, redémarrage/extinction |
| **InputRedirection** de Rosalina | 3DS, en arrière-plan | Reçoit boutons, écran tactile et pad circulaire en UDP **4950**, y compris en jeu |
| **NTR-HR** (remote play) | 3DS, en arrière-plan | Diffuse les écrans ; le client récupère une image comme capture d'écran (TCP **8000** + UDP **8001**) |

Le client `3ds` fonctionne sous Windows, macOS et Linux et dialogue avec les trois.

## Installer le client

Avec Python 3.9 ou plus récent, sur n'importe quel système :

```sh
pipx install "git+https://github.com/carlbastos/3ds-remote#subdirectory=client"
```

Sans Python, téléchargez l'exécutable de votre système dans la [dernière version](https://github.com/carlbastos/3ds-remote/releases/latest) : `3ds-windows-x64.exe`, `3ds-macos-arm64` ou `3ds-linux-x64`. Sous macOS et Linux, faites d'abord `chmod +x` ; macOS peut demander de l'autoriser dans *Réglages Système → Confidentialité et sécurité*, car il n'est pas signé.

`3ds config` indique où sont enregistrés les réglages (`%APPDATA%\3ds-remote` sous Windows, `~/.config/3ds-remote` sous macOS et Linux). `screenshot` reçoit l'image sur le port UDP **8001** : la première fois, le pare-feu peut demander une autorisation.

## Utilisation

La première fois, associez votre ordinateur à la console. Appuyez sur **Y** dans 3DS Remote pour afficher le mot de passe :

```sh
3ds login --host 192.168.1.241    # demande le mot de passe et l'enregistre dans ~/.config/3ds-remote/config.json (600)
```

```sh
3ds ping                          # sans mot de passe : version et état du mot de passe

3ds status                        # batterie, Wi-Fi, carte SD, modèle, firmware, Luma
3ds titles [--all] [--json]       # titres installés avec leur nom
3ds install game.cia [...]        # ignore les CIA dont la version est déjà installée (--force)
3ds launch <name|tid>             # lance le titre (le serveur se ferme)
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # installe la dernière version publiée sur GitHub

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds drag x1 y1 x2 y2 ; 3ds stick 1 0
3ds screenshot [--screen bottom] file.png   # PNG, JPEG, WebP
```

`THREEDS=ip[:port]` et `THREEDS_TOKEN=<mot de passe>` remplacent le fichier de configuration. `3ds logout` efface le mot de passe enregistré.

`press`/`touch`/`drag`/`stick` nécessitent InputRedirection ; `screenshot` nécessite NTR-HR. Aucun des deux n'a besoin que le serveur soit ouvert.

## Sur la console

| Écran | Contenu |
|---|---|
| Haut | Adresse, état (EN LIGNE / EN PAUSE / PAS DE RÉSEAU), mot de passe (masqué), batterie, Wi-Fi, progression des transferts et dernières requêtes |
| Bas (tactile) | Afficher le mot de passe (**Y**), nouveau mot de passe aléatoire (**X**), définir le mot de passe au clavier, activer/désactiver le mot de passe, pause (**SELECT**), quitter (**START**), langue (**L/R**) |

## Langues

L'interface est disponible dans les 12 langues de la 3DS : portugais, anglais, espagnol, russe, japonais, français, allemand, italien, néerlandais, chinois simplifié, coréen et chinois traditionnel. Par défaut, elle suit la langue du système. **L/R**, ou le sélecteur dans le coin de l'écran du bas, change de langue ; le choix est enregistré dans `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).

Le chinois et le coréen utilisent les polices système CHN/KOR/TWN, chargées à la demande.

Pour traduire ou corriger un texte, modifiez `source/i18n.c`. Une traduction manquante s'affiche en anglais.

## Sécurité

- **Mot de passe obligatoire** sur toutes les routes sauf `/ping`, via `Authorization: Bearer <mot de passe>`. Au premier lancement, l'app génère un mot de passe aléatoire de 12 caractères et l'enregistre dans `sdmc:/config/3ds-remote/config.ini`.
- Le mot de passe **ne se change que sur la console**. Aucun endpoint ne modifie la configuration, et l'API ne peut ni lire ni écrire `config.ini`.
- **5 mauvais mots de passe d'affilée** bloquent les connexions pendant 30 s (HTTP 429).
- Les chemins contenant `..` ou `\` sont refusés.
- Chaque lecture ou écriture réseau expire au bout de 15 s, pour qu'un client bloqué ne fige pas le serveur.
- **Pause** ferme réellement le port, et le serveur n'écoute que tant que l'app est ouverte.
- Désactiver le mot de passe demande une confirmation (deux appuis).
- **Limite :** c'est du HTTP sans TLS, le mot de passe circule donc en clair sur le réseau local. À n'utiliser que sur un réseau de confiance.

## Après chaque démarrage de la 3DS

1. Ouvrez **Boot NTR Selector** → chemin par défaut → **3.6 HR**.
2. Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.
3. Pour le serveur : ouvrez **3DS Remote** depuis le menu HOME.

## Développement

La compilation, l'intégration continue, la liste des endpoints et les notes techniques se trouvent dans le [README en anglais](../README.md#build).
