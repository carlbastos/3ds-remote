"""Generates docs/README.<lang>.md (user-facing translations) and the language bar of every README.

The translations live in this file; README.md (English) and docs/README.pt-BR.md are written by hand.
Usage: python3 tools/gen_readmes.py .
"""
import os
import re
import sys

ROOT = sys.argv[1]
REPO = "https://github.com/carlbastos/3ds-remote"

# (file code, display name) in the same order as the app's language cycle
LANGS = [("en", "English"), ("pt-BR", "Português"), ("es", "Español"), ("ru", "Русский"), ("ja", "日本語"),
         ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("nl", "Nederlands"),
         ("zh-CN", "简体中文"), ("ko", "한국어"), ("zh-TW", "繁體中文")]


def lang_bar(current, from_docs):
    parts = []
    for code, name in LANGS:
        if code == current:
            parts.append(f"**{name}**")
            continue
        if code == "en":
            href = "../README.md" if from_docs else "README.md"
        else:
            href = f"README.{code}.md" if from_docs else f"docs/README.{code}.md"
        parts.append(f"[{name}]({href})")
    return " · ".join(parts)


T = {}

T["es"] = dict(
    intro="Controla una New 3DS con Luma3DS por la red desde tu ordenador.",
    h_install="Instalación", fbi="En la 3DS, abre **FBI → Remote Install → Scan QR Code**:", qr_alt="Código QR de la última versión",
    release="Cada [versión]({rel}) incluye `3ds-remote.cia`, `3ds-remote.3dsx`, el cliente `3ds` y el código QR de esa versión.",
    h_how="Cómo funciona", three="Son tres piezas:", th=("Pieza", "Dónde se ejecuta", "Qué hace"),
    r1=("3DS, como app (CIA o `.3dsx`)", "Servidor HTTP/JSON en el puerto **8080**: estado, títulos, instalar/eliminar CIA, abrir títulos, archivos de la SD, reinicio/apagado"),
    r2=("**InputRedirection** de Rosalina", "3DS, en segundo plano", "Recibe botones, pantalla táctil y stick por UDP **4950**, también dentro de los juegos"),
    r3=("**NTR-HR** (remote play)", "3DS, en segundo plano", "Transmite las pantallas; el cliente toma un fotograma como captura (TCP **8000** + UDP **8001**)"),
    client="El cliente `3ds` funciona en Windows, macOS y Linux y habla con las tres.",
    h_client="Instalar el cliente", inst="Con Python 3.9 o superior, en cualquier sistema:",
    inst2="Sin Python, descarga el ejecutable de tu sistema en la [última versión]({latest}): `3ds-windows-x64.exe`, `3ds-macos-arm64` o `3ds-linux-x64`. En macOS y Linux, dale permiso de ejecución con `chmod +x`; macOS puede pedir que lo autorices en *Ajustes del Sistema → Privacidad y seguridad*, porque no está firmado.",
    inst3="`3ds config` muestra dónde se guarda la configuración (`%APPDATA%\\3ds-remote` en Windows, `~/.config/3ds-remote` en macOS y Linux). `screenshot` recibe la imagen por el puerto UDP **8001**, así que la primera vez el cortafuegos puede pedir permiso.",
    h_usage="Uso", pair="La primera vez, empareja tu ordenador con la consola. Pulsa **Y** en 3DS Remote para ver la contraseña:",
    c_login="pide la contraseña y la guarda en ~/.config/3ds-remote/config.json (600)", c_ping="sin contraseña: versión y si la contraseña está activada",
    c_status="batería, Wi-Fi, SD, modelo, firmware, Luma", c_titles="títulos instalados con nombre",
    c_install="omite los CIA cuya versión ya está instalada (--force)", c_launch="abre el título (el servidor se cierra)", c_update="instala la última versión de GitHub",
    env="`THREEDS=ip[:puerto]` y `THREEDS_TOKEN=<contraseña>` tienen prioridad sobre el archivo de configuración. `3ds logout` borra la contraseña guardada.",
    needs="`press`/`touch`/`drag`/`stick` necesitan InputRedirection activado; `screenshot` necesita NTR-HR cargado. Ninguno de los dos depende de que el servidor esté abierto.",
    h_console="En la consola", sh=("Pantalla", "Contenido"),
    top=("Superior", "Dirección, estado (EN LÍNEA / EN PAUSA / SIN RED), contraseña (oculta), batería, Wi-Fi, progreso de transferencias y las últimas peticiones"),
    bottom=("Inferior (táctil)", "Mostrar contraseña (**Y**), nueva contraseña aleatoria (**X**), definir contraseña con el teclado, activar/desactivar la contraseña, pausar (**SELECT**), salir (**START**), idioma (**L/R**)"),
    h_langs="Idiomas",
    p1="La interfaz de la app está en los 12 idiomas de la 3DS: portugués, inglés, español, ruso, japonés, francés, alemán, italiano, neerlandés, chino simplificado, coreano y chino tradicional. Por defecto sigue el idioma del sistema. **L/R**, o el selector en la esquina de la pantalla inferior, cambian de idioma, y la elección se guarda en `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="El chino y el coreano usan las fuentes del sistema CHN/KOR/TWN, que la app carga cuando las necesita.",
    p3="Para traducir o corregir textos, edita `source/i18n.c`. Una traducción que falte se muestra en inglés.",
    h_security="Seguridad", sec=[
        "**Contraseña obligatoria** en todas las rutas excepto `/ping`, mediante `Authorization: Bearer <contraseña>`. En el primer arranque la app genera una contraseña aleatoria de 12 caracteres y la guarda en `sdmc:/config/3ds-remote/config.ini`.",
        "La contraseña **solo se cambia en la consola**. Ningún endpoint modifica la configuración, y la API no puede leer ni escribir `config.ini`.",
        "**5 contraseñas incorrectas seguidas** bloquean el acceso durante 30 s (HTTP 429).",
        "Se rechazan las rutas con `..` o `\\`.",
        "Toda lectura y escritura de red caduca a los 15 s, para que un cliente parado no bloquee el servidor.",
        "**Pausar** cierra el puerto de verdad, y el servidor solo escucha mientras la app está abierta.",
        "Desactivar la contraseña pide confirmación (dos toques).",
        "**Limitación:** es HTTP sin TLS, así que la contraseña viaja en texto plano por la red local. Úsalo solo en una red de confianza."],
    h_boot="Después de cada arranque de la 3DS", boot=[
        "Abre **Boot NTR Selector** → ruta predeterminada → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Para el servidor: abre **3DS Remote** desde el menú HOME."],
    h_dev="Desarrollo", dev="La compilación, la integración continua, la lista de endpoints y las notas técnicas están en el [README en inglés](../README.md#build).",
)

T["ru"] = dict(
    intro="Управление New 3DS с Luma3DS по сети с компьютера.",
    h_install="Установка", fbi="На 3DS откройте **FBI → Remote Install → Scan QR Code**:", qr_alt="QR-код последней версии",
    release="В каждом [релизе]({rel}) есть `3ds-remote.cia`, `3ds-remote.3dsx`, клиент `3ds` и QR-код этой версии.",
    h_how="Как это работает", three="Три компонента:", th=("Компонент", "Где работает", "Что делает"),
    r1=("3DS, как приложение (CIA или `.3dsx`)", "HTTP/JSON-сервер на порту **8080**: состояние, игры, установка и удаление CIA, запуск игр, файлы на SD-карте, перезагрузка и выключение"),
    r2=("**InputRedirection** из Rosalina", "3DS, в фоне", "Принимает кнопки, касания и стик по UDP **4950**, в том числе внутри игр"),
    r3=("**NTR-HR** (remote play)", "3DS, в фоне", "Транслирует экраны; клиент берёт кадр как скриншот (TCP **8000** + UDP **8001**)"),
    client="Клиент `3ds` работает в Windows, macOS и Linux и обращается ко всем трём.",
    h_client="Установка клиента", inst="С Python 3.9 или новее, в любой ОС:",
    inst2="Без Python скачайте исполняемый файл для своей системы из [последнего релиза]({latest}): `3ds-windows-x64.exe`, `3ds-macos-arm64` или `3ds-linux-x64`. В macOS и Linux сначала выполните `chmod +x`; macOS может попросить разрешить запуск в *Системные настройки → Конфиденциальность и безопасность*, так как файл не подписан.",
    inst3="`3ds config` показывает, где хранятся настройки (`%APPDATA%\\3ds-remote` в Windows, `~/.config/3ds-remote` в macOS и Linux). `screenshot` принимает изображение на UDP-порт **8001**, поэтому при первом запуске брандмауэр может запросить разрешение.",
    h_usage="Использование", pair="Сначала свяжите компьютер с консолью. Нажмите **Y** в 3DS Remote, чтобы увидеть пароль:",
    c_login="спросит пароль и сохранит его в ~/.config/3ds-remote/config.json (600)", c_ping="без пароля: версия и включён ли пароль",
    c_status="батарея, Wi-Fi, SD-карта, модель, прошивка, Luma", c_titles="установленные игры с названиями",
    c_install="пропускает CIA, если эта версия уже установлена (--force)", c_launch="запускает игру (сервер закрывается)", c_update="устанавливает последний релиз с GitHub",
    env="`THREEDS=ip[:порт]` и `THREEDS_TOKEN=<пароль>` переопределяют файл настроек. `3ds logout` удаляет сохранённый пароль.",
    needs="Для `press`/`touch`/`drag`/`stick` нужен включённый InputRedirection, для `screenshot` — загруженный NTR-HR. Сервер для них открывать не нужно.",
    h_console="На консоли", sh=("Экран", "Что на нём"),
    top=("Верхний", "Адрес, состояние (В СЕТИ / ПАУЗА / НЕТ СЕТИ), пароль (скрыт), батарея, Wi-Fi, ход передачи файлов и последние запросы"),
    bottom=("Нижний (сенсорный)", "Показать пароль (**Y**), новый случайный пароль (**X**), задать пароль с клавиатуры, включить или отключить пароль, пауза (**SELECT**), выход (**START**), язык (**L/R**)"),
    h_langs="Языки",
    p1="Интерфейс приложения доступен на всех 12 языках 3DS: португальском, английском, испанском, русском, японском, французском, немецком, итальянском, нидерландском, упрощённом китайском, корейском и традиционном китайском. По умолчанию используется язык системы. **L/R** или переключатель в углу нижнего экрана меняют язык; выбор сохраняется в `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="Для китайского и корейского приложение по мере надобности загружает системные шрифты CHN/KOR/TWN.",
    p3="Чтобы перевести или исправить строки, правьте `source/i18n.c`. Если перевода нет, показывается английский текст.",
    h_security="Безопасность", sec=[
        "**Пароль обязателен** для всех маршрутов, кроме `/ping`, через `Authorization: Bearer <пароль>`. При первом запуске приложение создаёт случайный пароль из 12 символов и сохраняет его в `sdmc:/config/3ds-remote/config.ini`.",
        "Пароль **меняется только на консоли**. Ни один endpoint не меняет настройки, а API не может ни читать, ни записывать `config.ini`.",
        "**5 неверных паролей подряд** блокируют вход на 30 с (HTTP 429).",
        "Пути с `..` или `\\` отклоняются.",
        "Любое чтение или запись по сети прерывается через 15 с, чтобы зависший клиент не блокировал сервер.",
        "**Пауза** действительно закрывает порт, и сервер слушает, только пока приложение открыто.",
        "Отключение пароля требует подтверждения (два касания).",
        "**Ограничение:** это HTTP без TLS, поэтому пароль передаётся по локальной сети открытым текстом. Используйте только в доверенной сети."],
    h_boot="После каждого включения 3DS", boot=[
        "Откройте **Boot NTR Selector** → путь по умолчанию → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Для сервера: откройте **3DS Remote** в меню HOME."],
    h_dev="Разработка", dev="Сборка, CI, список endpoints и технические заметки — в [README на английском](../README.md#build).",
)

T["ja"] = dict(
    intro="Luma3DS を導入した New 3DS を、パソコンからネットワーク経由で操作します。",
    h_install="インストール", fbi="3DS で **FBI → Remote Install → Scan QR Code** を開きます：", qr_alt="最新版の QR コード",
    release="各[リリース]({rel})には `3ds-remote.cia`、`3ds-remote.3dsx`、クライアント `3ds`、そのバージョンの QR コードが含まれます。",
    h_how="仕組み", three="3 つの部品で構成されています：", th=("部品", "動作場所", "役割"),
    r1=("3DS（CIA または `.3dsx` のアプリ）", "ポート **8080** の HTTP/JSON サーバー：状態、タイトル一覧、CIA のインストール・削除、タイトル起動、SD カードのファイル、再起動・電源オフ"),
    r2=("Rosalina の **InputRedirection**", "3DS（バックグラウンド）", "ボタン、タッチ、スライドパッドの入力を UDP **4950** で受け取ります（ゲーム中も可）"),
    r3=("**NTR-HR**（リモートプレイ）", "3DS（バックグラウンド）", "画面を配信し、クライアントが 1 フレームをスクリーンショットとして取得します（TCP **8000** + UDP **8001**）"),
    client="クライアント `3ds` は Windows、macOS、Linux で動作し、3 つすべてと通信します。",
    h_client="クライアントのインストール", inst="Python 3.9 以降があれば、どの OS でも：",
    inst2="Python がない場合は、[最新リリース]({latest})から自分の OS 用の実行ファイル（`3ds-windows-x64.exe`、`3ds-macos-arm64`、`3ds-linux-x64`）をダウンロードしてください。macOS と Linux では先に `chmod +x` を実行します。署名がないため、macOS では *システム設定 → プライバシーとセキュリティ* で許可を求められることがあります。",
    inst3="`3ds config` で設定ファイルの場所を確認できます（Windows は `%APPDATA%\\3ds-remote`、macOS と Linux は `~/.config/3ds-remote`）。`screenshot` は UDP ポート **8001** で映像を受け取るため、初回はファイアウォールが許可を求めることがあります。",
    h_usage="使い方", pair="最初にパソコンと本体をペアリングします。3DS Remote で **Y** を押すとパスワードが表示されます：",
    c_login="パスワードを入力し ~/.config/3ds-remote/config.json (600) に保存", c_ping="パスワード不要：バージョンとパスワードの有無",
    c_status="バッテリー、Wi-Fi、SD、機種、ファームウェア、Luma", c_titles="インストール済みタイトルと名前",
    c_install="同じバージョンがインストール済みならスキップ (--force)", c_launch="タイトルを起動（サーバーは終了）", c_update="GitHub の最新リリースをインストール",
    env="`THREEDS=ip[:ポート]` と `THREEDS_TOKEN=<パスワード>` は設定ファイルより優先されます。`3ds logout` で保存したパスワードを削除します。",
    needs="`press`/`touch`/`drag`/`stick` には InputRedirection、`screenshot` には NTR-HR が必要です。どちらもサーバーを開いている必要はありません。",
    h_console="本体の画面", sh=("画面", "内容"),
    top=("上画面", "アドレス、状態（オンライン / 一時停止中 / ネットなし）、パスワード（非表示）、バッテリー、Wi-Fi、転送の進行状況、最近のリクエスト"),
    bottom=("下画面（タッチ）", "パスワード表示（**Y**）、新しいランダムパスワード（**X**）、キーボードでパスワード設定、パスワード必須のオン・オフ、一時停止（**SELECT**）、終了（**START**）、言語（**L/R**）"),
    h_langs="言語",
    p1="アプリの画面は 3DS の全 12 言語に対応しています：ポルトガル語、英語、スペイン語、ロシア語、日本語、フランス語、ドイツ語、イタリア語、オランダ語、簡体字中国語、韓国語、繁体字中国語。初期設定では本体の言語に従います。**L/R** または下画面の隅のセレクターで切り替えられ、選択は `config.ini` に保存されます（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。",
    p2="中国語と韓国語では、必要に応じてシステムフォント CHN/KOR/TWN を読み込みます。",
    p3="文言の翻訳・修正は `source/i18n.c` を編集してください。翻訳がない項目は英語で表示されます。",
    h_security="セキュリティ", sec=[
        "`/ping` 以外のすべてのルートで **パスワードが必須** です（`Authorization: Bearer <パスワード>`）。初回起動時に 12 文字のランダムなパスワードを生成し、`sdmc:/config/3ds-remote/config.ini` に保存します。",
        "パスワードは **本体でしか変更できません**。設定を変更する endpoint はなく、API から `config.ini` を読み書きすることもできません。",
        "**5 回連続で間違える**と、30 秒間ログインを拒否します（HTTP 429）。",
        "`..` や `\\` を含むパスは拒否します。",
        "ネットワークの読み書きは 15 秒でタイムアウトするため、止まったクライアントがサーバーを固めることはありません。",
        "**一時停止** すると実際にポートを閉じます。サーバーはアプリを開いている間だけ待ち受けます。",
        "パスワードをオフにするには確認（2 回タップ）が必要です。",
        "**制限：** TLS なしの HTTP なので、パスワードはローカルネットワーク上を平文で流れます。信頼できるネットワークでのみ使ってください。"],
    h_boot="3DS を起動するたびに", boot=[
        "**Boot NTR Selector** を開く → デフォルトのパス → **3.6 HR**。",
        "Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。",
        "サーバーを使うとき：HOME メニューから **3DS Remote** を開く。"],
    h_dev="開発", dev="ビルド、CI、endpoint の一覧、技術的なメモは[英語の README](../README.md#build) を参照してください。",
)

T["fr"] = dict(
    intro="Pilotez une New 3DS sous Luma3DS par le réseau, depuis votre ordinateur.",
    h_install="Installation", fbi="Sur la 3DS, ouvrez **FBI → Remote Install → Scan QR Code** :", qr_alt="QR code de la dernière version",
    release="Chaque [version]({rel}) contient `3ds-remote.cia`, `3ds-remote.3dsx`, le client `3ds` et le QR code de cette version.",
    h_how="Fonctionnement", three="Trois éléments :", th=("Élément", "Où il tourne", "Rôle"),
    r1=("3DS, en tant qu'app (CIA ou `.3dsx`)", "Serveur HTTP/JSON sur le port **8080** : état, titres, installation/suppression de CIA, lancement de titres, fichiers de la carte SD, redémarrage/extinction"),
    r2=("**InputRedirection** de Rosalina", "3DS, en arrière-plan", "Reçoit boutons, écran tactile et pad circulaire en UDP **4950**, y compris en jeu"),
    r3=("**NTR-HR** (remote play)", "3DS, en arrière-plan", "Diffuse les écrans ; le client récupère une image comme capture d'écran (TCP **8000** + UDP **8001**)"),
    client="Le client `3ds` fonctionne sous Windows, macOS et Linux et dialogue avec les trois.",
    h_client="Installer le client", inst="Avec Python 3.9 ou plus récent, sur n'importe quel système :",
    inst2="Sans Python, téléchargez l'exécutable de votre système dans la [dernière version]({latest}) : `3ds-windows-x64.exe`, `3ds-macos-arm64` ou `3ds-linux-x64`. Sous macOS et Linux, faites d'abord `chmod +x` ; macOS peut demander de l'autoriser dans *Réglages Système → Confidentialité et sécurité*, car il n'est pas signé.",
    inst3="`3ds config` indique où sont enregistrés les réglages (`%APPDATA%\\3ds-remote` sous Windows, `~/.config/3ds-remote` sous macOS et Linux). `screenshot` reçoit l'image sur le port UDP **8001** : la première fois, le pare-feu peut demander une autorisation.",
    h_usage="Utilisation", pair="La première fois, associez votre ordinateur à la console. Appuyez sur **Y** dans 3DS Remote pour afficher le mot de passe :",
    c_login="demande le mot de passe et l'enregistre dans ~/.config/3ds-remote/config.json (600)", c_ping="sans mot de passe : version et état du mot de passe",
    c_status="batterie, Wi-Fi, carte SD, modèle, firmware, Luma", c_titles="titres installés avec leur nom",
    c_install="ignore les CIA dont la version est déjà installée (--force)", c_launch="lance le titre (le serveur se ferme)", c_update="installe la dernière version publiée sur GitHub",
    env="`THREEDS=ip[:port]` et `THREEDS_TOKEN=<mot de passe>` remplacent le fichier de configuration. `3ds logout` efface le mot de passe enregistré.",
    needs="`press`/`touch`/`drag`/`stick` nécessitent InputRedirection ; `screenshot` nécessite NTR-HR. Aucun des deux n'a besoin que le serveur soit ouvert.",
    h_console="Sur la console", sh=("Écran", "Contenu"),
    top=("Haut", "Adresse, état (EN LIGNE / EN PAUSE / PAS DE RÉSEAU), mot de passe (masqué), batterie, Wi-Fi, progression des transferts et dernières requêtes"),
    bottom=("Bas (tactile)", "Afficher le mot de passe (**Y**), nouveau mot de passe aléatoire (**X**), définir le mot de passe au clavier, activer/désactiver le mot de passe, pause (**SELECT**), quitter (**START**), langue (**L/R**)"),
    h_langs="Langues",
    p1="L'interface est disponible dans les 12 langues de la 3DS : portugais, anglais, espagnol, russe, japonais, français, allemand, italien, néerlandais, chinois simplifié, coréen et chinois traditionnel. Par défaut, elle suit la langue du système. **L/R**, ou le sélecteur dans le coin de l'écran du bas, change de langue ; le choix est enregistré dans `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="Le chinois et le coréen utilisent les polices système CHN/KOR/TWN, chargées à la demande.",
    p3="Pour traduire ou corriger un texte, modifiez `source/i18n.c`. Une traduction manquante s'affiche en anglais.",
    h_security="Sécurité", sec=[
        "**Mot de passe obligatoire** sur toutes les routes sauf `/ping`, via `Authorization: Bearer <mot de passe>`. Au premier lancement, l'app génère un mot de passe aléatoire de 12 caractères et l'enregistre dans `sdmc:/config/3ds-remote/config.ini`.",
        "Le mot de passe **ne se change que sur la console**. Aucun endpoint ne modifie la configuration, et l'API ne peut ni lire ni écrire `config.ini`.",
        "**5 mauvais mots de passe d'affilée** bloquent les connexions pendant 30 s (HTTP 429).",
        "Les chemins contenant `..` ou `\\` sont refusés.",
        "Chaque lecture ou écriture réseau expire au bout de 15 s, pour qu'un client bloqué ne fige pas le serveur.",
        "**Pause** ferme réellement le port, et le serveur n'écoute que tant que l'app est ouverte.",
        "Désactiver le mot de passe demande une confirmation (deux appuis).",
        "**Limite :** c'est du HTTP sans TLS, le mot de passe circule donc en clair sur le réseau local. À n'utiliser que sur un réseau de confiance."],
    h_boot="Après chaque démarrage de la 3DS", boot=[
        "Ouvrez **Boot NTR Selector** → chemin par défaut → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Pour le serveur : ouvrez **3DS Remote** depuis le menu HOME."],
    h_dev="Développement", dev="La compilation, l'intégration continue, la liste des endpoints et les notes techniques se trouvent dans le [README en anglais](../README.md#build).",
)

T["de"] = dict(
    intro="Steuere einen New 3DS mit Luma3DS über das Netzwerk von deinem Computer aus.",
    h_install="Installation", fbi="Öffne auf dem 3DS **FBI → Remote Install → Scan QR Code**:", qr_alt="QR-Code der neuesten Version",
    release="Jedes [Release]({rel}) enthält `3ds-remote.cia`, `3ds-remote.3dsx`, den Client `3ds` und den QR-Code dieser Version.",
    h_how="Funktionsweise", three="Es gibt drei Teile:", th=("Teil", "Läuft auf", "Aufgabe"),
    r1=("3DS, als App (CIA oder `.3dsx`)", "HTTP/JSON-Server auf Port **8080**: Status, Titel, CIAs installieren/entfernen, Titel starten, Dateien auf der SD-Karte, Neustart/Ausschalten"),
    r2=("**InputRedirection** von Rosalina", "3DS, im Hintergrund", "Empfängt Tasten, Touch und Schiebepad über UDP **4950**, auch in Spielen"),
    r3=("**NTR-HR** (Remote Play)", "3DS, im Hintergrund", "Überträgt die Bildschirme; der Client holt sich ein Bild als Screenshot (TCP **8000** + UDP **8001**)"),
    client="Der Client `3ds` läuft unter Windows, macOS und Linux und spricht mit allen drei.",
    h_client="Client installieren", inst="Mit Python 3.9 oder neuer, auf jedem Betriebssystem:",
    inst2="Ohne Python lädst du die ausführbare Datei für dein System aus dem [neuesten Release]({latest}): `3ds-windows-x64.exe`, `3ds-macos-arm64` oder `3ds-linux-x64`. Unter macOS und Linux zuerst `chmod +x` ausführen; macOS fragt eventuell unter *Systemeinstellungen → Datenschutz & Sicherheit* nach einer Freigabe, da die Datei nicht signiert ist.",
    inst3="`3ds config` zeigt, wo die Einstellungen liegen (`%APPDATA%\\3ds-remote` unter Windows, `~/.config/3ds-remote` unter macOS und Linux). `screenshot` empfängt das Bild auf UDP-Port **8001**, daher fragt die Firewall beim ersten Mal eventuell nach.",
    h_usage="Benutzung", pair="Verbinde beim ersten Mal deinen Computer mit der Konsole. Drücke in 3DS Remote **Y**, um das Passwort anzuzeigen:",
    c_login="fragt nach dem Passwort und speichert es in ~/.config/3ds-remote/config.json (600)", c_ping="ohne Passwort: Version und ob das Passwort aktiv ist",
    c_status="Akku, WLAN, SD-Karte, Modell, Firmware, Luma", c_titles="installierte Titel mit Namen",
    c_install="überspringt CIAs, deren Version schon installiert ist (--force)", c_launch="startet den Titel (der Server wird beendet)", c_update="installiert das neueste GitHub-Release",
    env="`THREEDS=ip[:port]` und `THREEDS_TOKEN=<passwort>` haben Vorrang vor der Konfigurationsdatei. `3ds logout` löscht das gespeicherte Passwort.",
    needs="`press`/`touch`/`drag`/`stick` brauchen InputRedirection, `screenshot` braucht NTR-HR. Für beides muss der Server nicht offen sein.",
    h_console="Auf der Konsole", sh=("Bildschirm", "Inhalt"),
    top=("Oben", "Adresse, Status (ONLINE / PAUSIERT / KEIN NETZ), Passwort (verborgen), Akku, WLAN, Fortschritt von Übertragungen und die letzten Anfragen"),
    bottom=("Unten (Touch)", "Passwort zeigen (**Y**), neues Zufallspasswort (**X**), Passwort per Tastatur festlegen, Passwortpflicht an/aus, Pause (**SELECT**), Beenden (**START**), Sprache (**L/R**)"),
    h_langs="Sprachen",
    p1="Die Oberfläche gibt es in allen 12 Sprachen des 3DS: Portugiesisch, Englisch, Spanisch, Russisch, Japanisch, Französisch, Deutsch, Italienisch, Niederländisch, vereinfachtes Chinesisch, Koreanisch und traditionelles Chinesisch. Standardmäßig folgt sie der Systemsprache. **L/R** oder die Auswahl in der Ecke des unteren Bildschirms wechseln die Sprache; die Wahl wird in `config.ini` gespeichert (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="Für Chinesisch und Koreanisch lädt die App bei Bedarf die Systemschriften CHN/KOR/TWN.",
    p3="Texte übersetzen oder korrigieren: `source/i18n.c`. Fehlt eine Übersetzung, erscheint der englische Text.",
    h_security="Sicherheit", sec=[
        "**Passwort erforderlich** auf allen Routen außer `/ping`, per `Authorization: Bearer <passwort>`. Beim ersten Start erzeugt die App ein zufälliges Passwort mit 12 Zeichen und speichert es in `sdmc:/config/3ds-remote/config.ini`.",
        "Das Passwort **lässt sich nur an der Konsole ändern**. Kein Endpoint ändert Einstellungen, und die API kann `config.ini` weder lesen noch schreiben.",
        "**5 falsche Passwörter hintereinander** sperren Anmeldungen für 30 s (HTTP 429).",
        "Pfade mit `..` oder `\\` werden abgelehnt.",
        "Jedes Lesen und Schreiben im Netzwerk bricht nach 15 s ab, damit ein hängender Client den Server nicht blockiert.",
        "**Pause** schließt den Port wirklich, und der Server lauscht nur, solange die App offen ist.",
        "Das Abschalten des Passworts muss bestätigt werden (zweimal tippen).",
        "**Einschränkung:** Es ist HTTP ohne TLS, das Passwort geht also im Klartext durchs lokale Netz. Nur in vertrauenswürdigen Netzen verwenden."],
    h_boot="Nach jedem Start des 3DS", boot=[
        "**Boot NTR Selector** öffnen → Standardpfad → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Für den Server: **3DS Remote** im HOME-Menü öffnen."],
    h_dev="Entwicklung", dev="Build, CI, die Liste der Endpoints und technische Hinweise stehen im [englischen README](../README.md#build).",
)

T["it"] = dict(
    intro="Controlla un New 3DS con Luma3DS in rete, dal tuo computer.",
    h_install="Installazione", fbi="Sul 3DS apri **FBI → Remote Install → Scan QR Code**:", qr_alt="Codice QR dell'ultima versione",
    release="Ogni [release]({rel}) contiene `3ds-remote.cia`, `3ds-remote.3dsx`, il client `3ds` e il codice QR di quella versione.",
    h_how="Come funziona", three="Ci sono tre parti:", th=("Parte", "Dove gira", "Cosa fa"),
    r1=("3DS, come app (CIA o `.3dsx`)", "Server HTTP/JSON sulla porta **8080**: stato, titoli, installazione/rimozione di CIA, avvio dei titoli, file della scheda SD, riavvio/spegnimento"),
    r2=("**InputRedirection** di Rosalina", "3DS, in background", "Riceve pulsanti, touch e Circle Pad via UDP **4950**, anche dentro i giochi"),
    r3=("**NTR-HR** (remote play)", "3DS, in background", "Trasmette gli schermi; il client prende un fotogramma come screenshot (TCP **8000** + UDP **8001**)"),
    client="Il client `3ds` funziona su Windows, macOS e Linux e comunica con tutte e tre.",
    h_client="Installare il client", inst="Con Python 3.9 o successivo, su qualsiasi sistema:",
    inst2="Senza Python, scarica l'eseguibile per il tuo sistema dall'[ultima release]({latest}): `3ds-windows-x64.exe`, `3ds-macos-arm64` o `3ds-linux-x64`. Su macOS e Linux esegui prima `chmod +x`; macOS potrebbe chiedere di autorizzarlo in *Impostazioni di Sistema → Privacy e sicurezza*, perché non è firmato.",
    inst3="`3ds config` mostra dove sono salvate le impostazioni (`%APPDATA%\\3ds-remote` su Windows, `~/.config/3ds-remote` su macOS e Linux). `screenshot` riceve l'immagine sulla porta UDP **8001**, quindi la prima volta il firewall potrebbe chiedere il permesso.",
    h_usage="Uso", pair="La prima volta, abbina il computer alla console. Premi **Y** in 3DS Remote per vedere la password:",
    c_login="chiede la password e la salva in ~/.config/3ds-remote/config.json (600)", c_ping="senza password: versione e se la password è attiva",
    c_status="batteria, Wi-Fi, scheda SD, modello, firmware, Luma", c_titles="titoli installati con il nome",
    c_install="salta i CIA la cui versione è già installata (--force)", c_launch="avvia il titolo (il server si chiude)", c_update="installa l'ultima release di GitHub",
    env="`THREEDS=ip[:porta]` e `THREEDS_TOKEN=<password>` hanno la precedenza sul file di configurazione. `3ds logout` cancella la password salvata.",
    needs="`press`/`touch`/`drag`/`stick` richiedono InputRedirection attivo; `screenshot` richiede NTR-HR caricato. Nessuno dei due ha bisogno che il server sia aperto.",
    h_console="Sulla console", sh=("Schermo", "Contenuto"),
    top=("Superiore", "Indirizzo, stato (ONLINE / IN PAUSA / NESSUNA RETE), password (nascosta), batteria, Wi-Fi, avanzamento dei trasferimenti e ultime richieste"),
    bottom=("Inferiore (touch)", "Mostra password (**Y**), nuova password casuale (**X**), imposta la password con la tastiera, attiva/disattiva la password, pausa (**SELECT**), esci (**START**), lingua (**L/R**)"),
    h_langs="Lingue",
    p1="L'interfaccia è disponibile in tutte le 12 lingue del 3DS: portoghese, inglese, spagnolo, russo, giapponese, francese, tedesco, italiano, olandese, cinese semplificato, coreano e cinese tradizionale. Di default segue la lingua di sistema. **L/R**, o il selettore nell'angolo dello schermo inferiore, cambiano lingua; la scelta viene salvata in `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="Cinese e coreano usano i font di sistema CHN/KOR/TWN, caricati quando servono.",
    p3="Per tradurre o correggere i testi, modifica `source/i18n.c`. Una traduzione mancante viene mostrata in inglese.",
    h_security="Sicurezza", sec=[
        "**Password obbligatoria** su tutte le rotte tranne `/ping`, tramite `Authorization: Bearer <password>`. Al primo avvio l'app genera una password casuale di 12 caratteri e la salva in `sdmc:/config/3ds-remote/config.ini`.",
        "La password **si cambia solo sulla console**. Nessun endpoint modifica le impostazioni, e l'API non può né leggere né scrivere `config.ini`.",
        "**5 password errate di fila** bloccano gli accessi per 30 s (HTTP 429).",
        "I percorsi con `..` o `\\` vengono rifiutati.",
        "Ogni lettura e scrittura di rete scade dopo 15 s, così un client bloccato non blocca il server.",
        "**Pausa** chiude davvero la porta, e il server resta in ascolto solo mentre l'app è aperta.",
        "Disattivare la password richiede una conferma (due tocchi).",
        "**Limite:** è HTTP senza TLS, quindi la password viaggia in chiaro sulla rete locale. Usalo solo su una rete fidata."],
    h_boot="Dopo ogni avvio del 3DS", boot=[
        "Apri **Boot NTR Selector** → percorso predefinito → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Per il server: apri **3DS Remote** dal menu HOME."],
    h_dev="Sviluppo", dev="Compilazione, CI, elenco degli endpoint e note tecniche sono nel [README in inglese](../README.md#build).",
)

T["nl"] = dict(
    intro="Bestuur een New 3DS met Luma3DS via het netwerk vanaf je computer.",
    h_install="Installeren", fbi="Open op de 3DS **FBI → Remote Install → Scan QR Code**:", qr_alt="QR-code van de nieuwste versie",
    release="Elke [release]({rel}) bevat `3ds-remote.cia`, `3ds-remote.3dsx`, de client `3ds` en de QR-code van die versie.",
    h_how="Hoe het werkt", three="Er zijn drie onderdelen:", th=("Onderdeel", "Draait op", "Wat het doet"),
    r1=("3DS, als app (CIA of `.3dsx`)", "HTTP/JSON-server op poort **8080**: status, titels, CIA's installeren/verwijderen, titels starten, bestanden op de SD-kaart, herstarten/uitschakelen"),
    r2=("**InputRedirection** van Rosalina", "3DS, op de achtergrond", "Ontvangt knoppen, aanraakscherm en Circle Pad via UDP **4950**, ook in games"),
    r3=("**NTR-HR** (remote play)", "3DS, op de achtergrond", "Streamt de schermen; de client pakt één beeld als screenshot (TCP **8000** + UDP **8001**)"),
    client="De client `3ds` werkt op Windows, macOS en Linux en praat met alle drie.",
    h_client="De client installeren", inst="Met Python 3.9 of nieuwer, op elk besturingssysteem:",
    inst2="Zonder Python download je het uitvoerbare bestand voor jouw systeem uit de [nieuwste release]({latest}): `3ds-windows-x64.exe`, `3ds-macos-arm64` of `3ds-linux-x64`. Op macOS en Linux eerst `chmod +x`; macOS vraagt mogelijk om toestemming in *Systeeminstellingen → Privacy en beveiliging*, omdat het bestand niet ondertekend is.",
    inst3="`3ds config` toont waar de instellingen staan (`%APPDATA%\\3ds-remote` op Windows, `~/.config/3ds-remote` op macOS en Linux). `screenshot` ontvangt het beeld op UDP-poort **8001**, dus de eerste keer kan de firewall om toestemming vragen.",
    h_usage="Gebruik", pair="Koppel de eerste keer je computer aan de console. Druk in 3DS Remote op **Y** om het wachtwoord te zien:",
    c_login="vraagt het wachtwoord en bewaart het in ~/.config/3ds-remote/config.json (600)", c_ping="zonder wachtwoord: versie en of het wachtwoord aan staat",
    c_status="batterij, wifi, SD-kaart, model, firmware, Luma", c_titles="geïnstalleerde titels met naam",
    c_install="slaat CIA's over waarvan de versie al geïnstalleerd is (--force)", c_launch="start de titel (de server sluit)", c_update="installeert de nieuwste GitHub-release",
    env="`THREEDS=ip[:poort]` en `THREEDS_TOKEN=<wachtwoord>` gaan voor het configuratiebestand. `3ds logout` wist het bewaarde wachtwoord.",
    needs="`press`/`touch`/`drag`/`stick` hebben InputRedirection nodig; `screenshot` heeft NTR-HR nodig. Voor geen van beide hoeft de server open te zijn.",
    h_console="Op de console", sh=("Scherm", "Inhoud"),
    top=("Boven", "Adres, status (ONLINE / GEPAUZEERD / GEEN NETWERK), wachtwoord (verborgen), batterij, wifi, voortgang van overdrachten en de laatste verzoeken"),
    bottom=("Onder (aanraak)", "Wachtwoord tonen (**Y**), nieuw willekeurig wachtwoord (**X**), wachtwoord instellen met het toetsenbord, wachtwoord vereisen aan/uit, pauzeren (**SELECT**), afsluiten (**START**), taal (**L/R**)"),
    h_langs="Talen",
    p1="De interface is beschikbaar in alle 12 talen van de 3DS: Portugees, Engels, Spaans, Russisch, Japans, Frans, Duits, Italiaans, Nederlands, vereenvoudigd Chinees, Koreaans en traditioneel Chinees. Standaard volgt hij de systeemtaal. **L/R**, of de keuzeknop in de hoek van het onderste scherm, wisselt van taal; de keuze wordt bewaard in `config.ini` (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="Chinees en Koreaans gebruiken de systeemlettertypen CHN/KOR/TWN, die de app laadt wanneer dat nodig is.",
    p3="Teksten vertalen of verbeteren: `source/i18n.c`. Ontbreekt een vertaling, dan verschijnt de Engelse tekst.",
    h_security="Beveiliging", sec=[
        "**Wachtwoord verplicht** op alle routes behalve `/ping`, via `Authorization: Bearer <wachtwoord>`. Bij de eerste start maakt de app een willekeurig wachtwoord van 12 tekens en bewaart het in `sdmc:/config/3ds-remote/config.ini`.",
        "Het wachtwoord **kan alleen op de console worden gewijzigd**. Geen enkel endpoint wijzigt instellingen, en de API kan `config.ini` niet lezen of schrijven.",
        "**5 foute wachtwoorden achter elkaar** blokkeren inloggen 30 s lang (HTTP 429).",
        "Paden met `..` of `\\` worden geweigerd.",
        "Elke netwerklees- en schrijfactie stopt na 15 s, zodat een vastgelopen client de server niet blokkeert.",
        "**Pauzeren** sluit de poort echt, en de server luistert alleen zolang de app open is.",
        "Het wachtwoord uitzetten vraagt om bevestiging (twee keer tikken).",
        "**Beperking:** het is HTTP zonder TLS, dus het wachtwoord gaat onversleuteld over het lokale netwerk. Gebruik het alleen op een vertrouwd netwerk."],
    h_boot="Na elke start van de 3DS", boot=[
        "Open **Boot NTR Selector** → standaardpad → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "Voor de server: open **3DS Remote** in het HOME-menu."],
    h_dev="Ontwikkeling", dev="Bouwen, CI, de lijst met endpoints en technische notities staan in de [Engelse README](../README.md#build).",
)

T["zh-CN"] = dict(
    intro="从电脑通过网络控制运行 Luma3DS 的 New 3DS。",
    h_install="安装", fbi="在 3DS 上打开 **FBI → Remote Install → Scan QR Code**：", qr_alt="最新版本的二维码",
    release="每个[发布版本]({rel})都包含 `3ds-remote.cia`、`3ds-remote.3dsx`、客户端 `3ds` 以及该版本的二维码。",
    h_how="工作原理", three="共有三个部分：", th=("部分", "运行位置", "作用"),
    r1=("3DS，作为应用（CIA 或 `.3dsx`）", "端口 **8080** 上的 HTTP/JSON 服务器：状态、游戏列表、安装/删除 CIA、启动游戏、SD 卡文件、重启/关机"),
    r2=("Rosalina 的 **InputRedirection**", "3DS，后台", "通过 UDP **4950** 接收按键、触摸和摇杆输入，游戏中也可以"),
    r3=("**NTR-HR**（远程游玩）", "3DS，后台", "串流画面；客户端截取一帧作为截图（TCP **8000** + UDP **8001**）"),
    client="客户端 `3ds` 可在 Windows、macOS 和 Linux 上运行，并与这三部分通信。",
    h_client="安装客户端", inst="在任何系统上，只要有 Python 3.9 或更高版本：",
    inst2="没有 Python 的话，请从[最新发布版本]({latest})下载对应系统的可执行文件：`3ds-windows-x64.exe`、`3ds-macos-arm64` 或 `3ds-linux-x64`。在 macOS 和 Linux 上先运行 `chmod +x`；由于未签名，macOS 可能会要求在 *系统设置 → 隐私与安全性* 中允许运行。",
    inst3="`3ds config` 会显示配置文件的位置（Windows 为 `%APPDATA%\\3ds-remote`，macOS 和 Linux 为 `~/.config/3ds-remote`）。`screenshot` 通过 UDP 端口 **8001** 接收画面，因此首次使用时防火墙可能会请求许可。",
    h_usage="使用方法", pair="第一次使用时，先将电脑与主机配对。在 3DS Remote 中按 **Y** 显示密码：",
    c_login="输入密码并保存到 ~/.config/3ds-remote/config.json (600)", c_ping="无需密码：版本以及是否启用密码",
    c_status="电池、Wi-Fi、SD 卡、型号、固件、Luma", c_titles="已安装的游戏及名称",
    c_install="如果该版本已安装则跳过 (--force)", c_launch="启动游戏（服务器会关闭）", c_update="安装 GitHub 上的最新版本",
    env="`THREEDS=ip[:端口]` 和 `THREEDS_TOKEN=<密码>` 优先于配置文件。`3ds logout` 会删除已保存的密码。",
    needs="`press`/`touch`/`drag`/`stick` 需要开启 InputRedirection；`screenshot` 需要加载 NTR-HR。两者都不需要打开服务器。",
    h_console="主机上的界面", sh=("屏幕", "内容"),
    top=("上屏", "地址、状态（在线 / 已暂停 / 无网络）、密码（隐藏）、电池、Wi-Fi、传输进度和最近的请求"),
    bottom=("下屏（触摸）", "显示密码（**Y**）、生成随机新密码（**X**）、用键盘设置密码、开启/关闭密码、暂停（**SELECT**）、退出（**START**）、语言（**L/R**）"),
    h_langs="语言",
    p1="应用界面支持 3DS 的全部 12 种语言：葡萄牙语、英语、西班牙语、俄语、日语、法语、德语、意大利语、荷兰语、简体中文、韩语和繁体中文。默认跟随系统语言。按 **L/R** 或点下屏角落的选择器切换语言，选择会保存到 `config.ini`（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。",
    p2="中文和韩语会在需要时加载系统字体 CHN/KOR/TWN。",
    p3="翻译或修改文本请编辑 `source/i18n.c`。缺少的翻译会显示英文。",
    h_security="安全", sec=[
        "除 `/ping` 外的所有接口都**需要密码**（`Authorization: Bearer <密码>`）。首次运行时，应用会生成 12 位随机密码并保存到 `sdmc:/config/3ds-remote/config.ini`。",
        "密码**只能在主机上修改**。没有任何接口能修改设置，API 也无法读取或写入 `config.ini`。",
        "**连续 5 次密码错误**会锁定登录 30 秒（HTTP 429）。",
        "拒绝包含 `..` 或 `\\` 的路径。",
        "所有网络读写在 15 秒后超时，卡住的客户端不会拖住服务器。",
        "**暂停**会真正关闭端口，服务器只在应用打开时监听。",
        "关闭密码需要确认（点两次）。",
        "**限制：**这是没有 TLS 的 HTTP，密码在局域网中以明文传输。请只在可信的网络中使用。"],
    h_boot="每次启动 3DS 后", boot=[
        "打开 **Boot NTR Selector** → 默认路径 → **3.6 HR**。",
        "Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。",
        "使用服务器时：从 HOME 菜单打开 **3DS Remote**。"],
    h_dev="开发", dev="编译、CI、接口列表和技术说明请见[英文 README](../README.md#build)。",
)

T["ko"] = dict(
    intro="Luma3DS가 설치된 New 3DS를 컴퓨터에서 네트워크로 제어합니다.",
    h_install="설치", fbi="3DS에서 **FBI → Remote Install → Scan QR Code**를 엽니다:", qr_alt="최신 버전 QR 코드",
    release="각 [릴리스]({rel})에는 `3ds-remote.cia`, `3ds-remote.3dsx`, 클라이언트 `3ds`, 해당 버전의 QR 코드가 들어 있습니다.",
    h_how="작동 방식", three="세 부분으로 이루어져 있습니다:", th=("구성 요소", "실행 위치", "역할"),
    r1=("3DS, 앱으로 실행 (CIA 또는 `.3dsx`)", "포트 **8080**의 HTTP/JSON 서버: 상태, 타이틀 목록, CIA 설치/삭제, 타이틀 실행, SD 카드 파일, 재시작/전원 끄기"),
    r2=("Rosalina의 **InputRedirection**", "3DS, 백그라운드", "UDP **4950**으로 버튼, 터치, 슬라이드 패드 입력을 받습니다 (게임 중에도 가능)"),
    r3=("**NTR-HR** (리모트 플레이)", "3DS, 백그라운드", "화면을 스트리밍하고, 클라이언트가 한 프레임을 스크린샷으로 가져옵니다 (TCP **8000** + UDP **8001**)"),
    client="클라이언트 `3ds`는 Windows, macOS, Linux에서 동작하며 세 부분 모두와 통신합니다.",
    h_client="클라이언트 설치", inst="Python 3.9 이상이 있다면 어떤 OS에서든:",
    inst2="Python이 없다면 [최신 릴리스]({latest})에서 운영체제에 맞는 실행 파일(`3ds-windows-x64.exe`, `3ds-macos-arm64`, `3ds-linux-x64`)을 내려받으세요. macOS와 Linux에서는 먼저 `chmod +x`를 실행하세요. 서명되지 않은 파일이라 macOS에서는 *시스템 설정 → 개인정보 보호 및 보안*에서 허용하라고 할 수 있습니다.",
    inst3="`3ds config`로 설정 파일 위치를 확인할 수 있습니다 (Windows는 `%APPDATA%\\3ds-remote`, macOS와 Linux는 `~/.config/3ds-remote`). `screenshot`은 UDP 포트 **8001**로 화면을 받으므로 처음에는 방화벽이 허용을 요청할 수 있습니다.",
    h_usage="사용법", pair="처음에는 컴퓨터와 본체를 페어링합니다. 3DS Remote에서 **Y**를 누르면 비밀번호가 표시됩니다:",
    c_login="비밀번호를 입력받아 ~/.config/3ds-remote/config.json (600)에 저장", c_ping="비밀번호 없이: 버전과 비밀번호 사용 여부",
    c_status="배터리, Wi-Fi, SD 카드, 모델, 펌웨어, Luma", c_titles="설치된 타이틀과 이름",
    c_install="같은 버전이 이미 설치되어 있으면 건너뜀 (--force)", c_launch="타이틀 실행 (서버는 종료됨)", c_update="GitHub 최신 릴리스 설치",
    env="`THREEDS=ip[:포트]`와 `THREEDS_TOKEN=<비밀번호>`는 설정 파일보다 우선합니다. `3ds logout`은 저장된 비밀번호를 지웁니다.",
    needs="`press`/`touch`/`drag`/`stick`에는 InputRedirection이, `screenshot`에는 NTR-HR이 필요합니다. 둘 다 서버를 열어 둘 필요는 없습니다.",
    h_console="본체 화면", sh=("화면", "내용"),
    top=("위 화면", "주소, 상태 (온라인 / 일시 정지 / 네트워크 없음), 비밀번호 (숨김), 배터리, Wi-Fi, 전송 진행 상황, 최근 요청"),
    bottom=("아래 화면 (터치)", "비밀번호 표시 (**Y**), 새 무작위 비밀번호 (**X**), 키보드로 비밀번호 설정, 비밀번호 요구 켜기/끄기, 일시 정지 (**SELECT**), 종료 (**START**), 언어 (**L/R**)"),
    h_langs="언어",
    p1="앱 화면은 3DS의 12개 언어를 모두 지원합니다: 포르투갈어, 영어, 스페인어, 러시아어, 일본어, 프랑스어, 독일어, 이탈리아어, 네덜란드어, 중국어 간체, 한국어, 중국어 번체. 기본값은 시스템 언어를 따릅니다. **L/R** 또는 아래 화면 모서리의 선택기로 언어를 바꿀 수 있으며, 선택은 `config.ini`에 저장됩니다 (`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`).",
    p2="중국어와 한국어는 필요할 때 시스템 글꼴 CHN/KOR/TWN을 불러옵니다.",
    p3="문구를 번역하거나 고치려면 `source/i18n.c`를 수정하세요. 번역이 없는 항목은 영어로 표시됩니다.",
    h_security="보안", sec=[
        "`/ping`을 제외한 모든 경로에 **비밀번호가 필요**합니다 (`Authorization: Bearer <비밀번호>`). 처음 실행할 때 앱이 12자리 무작위 비밀번호를 만들어 `sdmc:/config/3ds-remote/config.ini`에 저장합니다.",
        "비밀번호는 **본체에서만 바꿀 수 있습니다**. 설정을 바꾸는 엔드포인트는 없고, API로 `config.ini`를 읽거나 쓸 수도 없습니다.",
        "**비밀번호를 5번 연속 틀리면** 30초 동안 로그인이 막힙니다 (HTTP 429).",
        "`..`나 `\\`가 들어간 경로는 거부합니다.",
        "모든 네트워크 읽기와 쓰기는 15초 후 시간 초과되므로, 멈춘 클라이언트가 서버를 붙잡지 못합니다.",
        "**일시 정지**하면 포트를 실제로 닫고, 서버는 앱이 열려 있는 동안에만 대기합니다.",
        "비밀번호를 끄려면 확인이 필요합니다 (두 번 탭).",
        "**제한:** TLS 없는 HTTP이므로 비밀번호가 로컬 네트워크에서 평문으로 전송됩니다. 신뢰할 수 있는 네트워크에서만 사용하세요."],
    h_boot="3DS를 켤 때마다", boot=[
        "**Boot NTR Selector** 열기 → 기본 경로 → **3.6 HR**.",
        "Rosalina (L+↓+Select) → *Miscellaneous options* → **Start InputRedirection**.",
        "서버를 쓸 때: HOME 메뉴에서 **3DS Remote** 열기."],
    h_dev="개발", dev="빌드, CI, 엔드포인트 목록, 기술 메모는 [영어 README](../README.md#build)를 참고하세요.",
)

T["zh-TW"] = dict(
    intro="從電腦透過網路控制執行 Luma3DS 的 New 3DS。",
    h_install="安裝", fbi="在 3DS 上開啟 **FBI → Remote Install → Scan QR Code**：", qr_alt="最新版本的 QR 碼",
    release="每個[發行版本]({rel})都包含 `3ds-remote.cia`、`3ds-remote.3dsx`、用戶端 `3ds` 以及該版本的 QR 碼。",
    h_how="運作方式", three="共有三個部分：", th=("部分", "執行位置", "用途"),
    r1=("3DS，作為應用程式（CIA 或 `.3dsx`）", "連接埠 **8080** 上的 HTTP/JSON 伺服器：狀態、遊戲清單、安裝/刪除 CIA、啟動遊戲、SD 卡檔案、重新啟動/關機"),
    r2=("Rosalina 的 **InputRedirection**", "3DS，背景執行", "透過 UDP **4950** 接收按鍵、觸控和類比搖桿輸入，遊戲中也可以"),
    r3=("**NTR-HR**（遠端遊玩）", "3DS，背景執行", "串流畫面；用戶端擷取一格畫面作為螢幕截圖（TCP **8000** + UDP **8001**）"),
    client="用戶端 `3ds` 可在 Windows、macOS 和 Linux 上執行，並與這三個部分通訊。",
    h_client="安裝用戶端", inst="在任何系統上，只要有 Python 3.9 或更新版本：",
    inst2="沒有 Python 的話，請從[最新發行版本]({latest})下載對應系統的執行檔：`3ds-windows-x64.exe`、`3ds-macos-arm64` 或 `3ds-linux-x64`。在 macOS 和 Linux 上請先執行 `chmod +x`；由於沒有簽署，macOS 可能會要求在 *系統設定 → 隱私權與安全性* 中允許執行。",
    inst3="`3ds config` 會顯示設定檔的位置（Windows 為 `%APPDATA%\\3ds-remote`，macOS 和 Linux 為 `~/.config/3ds-remote`）。`screenshot` 透過 UDP 連接埠 **8001** 接收畫面，因此第一次使用時防火牆可能會要求允許。",
    h_usage="使用方式", pair="第一次使用時，先將電腦與主機配對。在 3DS Remote 中按 **Y** 顯示密碼：",
    c_login="輸入密碼並儲存到 ~/.config/3ds-remote/config.json (600)", c_ping="不需密碼：版本及是否啟用密碼",
    c_status="電池、Wi-Fi、SD 卡、型號、韌體、Luma", c_titles="已安裝的遊戲及名稱",
    c_install="若該版本已安裝則略過 (--force)", c_launch="啟動遊戲（伺服器會關閉）", c_update="安裝 GitHub 上的最新版本",
    env="`THREEDS=ip[:連接埠]` 和 `THREEDS_TOKEN=<密碼>` 優先於設定檔。`3ds logout` 會刪除已儲存的密碼。",
    needs="`press`/`touch`/`drag`/`stick` 需要開啟 InputRedirection；`screenshot` 需要載入 NTR-HR。兩者都不需要開啟伺服器。",
    h_console="主機上的畫面", sh=("螢幕", "內容"),
    top=("上螢幕", "位址、狀態（線上 / 已暫停 / 無網路）、密碼（隱藏）、電池、Wi-Fi、傳輸進度和最近的請求"),
    bottom=("下螢幕（觸控）", "顯示密碼（**Y**）、產生隨機新密碼（**X**）、用鍵盤設定密碼、開啟/關閉密碼、暫停（**SELECT**）、結束（**START**）、語言（**L/R**）"),
    h_langs="語言",
    p1="應用程式介面支援 3DS 的全部 12 種語言：葡萄牙文、英文、西班牙文、俄文、日文、法文、德文、義大利文、荷蘭文、簡體中文、韓文和繁體中文。預設跟隨系統語言。按 **L/R** 或點下螢幕角落的選擇器切換語言，選擇會儲存到 `config.ini`（`lang=auto|pt|en|es|ru|ja|fr|de|it|nl|zh|ko|tw`）。",
    p2="中文和韓文會在需要時載入系統字型 CHN/KOR/TWN。",
    p3="翻譯或修改文字請編輯 `source/i18n.c`。缺少的翻譯會顯示英文。",
    h_security="安全性", sec=[
        "除了 `/ping` 以外的所有路徑都**需要密碼**（`Authorization: Bearer <密碼>`）。第一次執行時，應用程式會產生 12 個字元的隨機密碼並儲存到 `sdmc:/config/3ds-remote/config.ini`。",
        "密碼**只能在主機上變更**。沒有任何端點能變更設定，API 也無法讀取或寫入 `config.ini`。",
        "**連續 5 次密碼錯誤**會鎖定登入 30 秒（HTTP 429）。",
        "拒絕包含 `..` 或 `\\` 的路徑。",
        "所有網路讀寫在 15 秒後逾時，卡住的用戶端不會拖住伺服器。",
        "**暫停**會真正關閉連接埠，伺服器只在應用程式開啟時監聽。",
        "關閉密碼需要確認（點兩次）。",
        "**限制：**這是沒有 TLS 的 HTTP，密碼在區域網路中以明文傳輸。請只在可信任的網路中使用。"],
    h_boot="每次啟動 3DS 後", boot=[
        "開啟 **Boot NTR Selector** → 預設路徑 → **3.6 HR**。",
        "Rosalina（L+↓+Select）→ *Miscellaneous options* → **Start InputRedirection**。",
        "使用伺服器時：從 HOME 選單開啟 **3DS Remote**。"],
    h_dev="開發", dev="編譯、CI、端點清單和技術說明請見[英文 README](../README.md#build)。",
)

BADGES = f"""[![build]({REPO}/actions/workflows/build.yml/badge.svg)]({REPO}/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/carlbastos/3ds-remote)]({REPO}/releases/latest)"""


def render(code, t):
    rows = "\n".join([
        f"| {t['th'][0]} | {t['th'][1]} | {t['th'][2]} |",
        "|---|---|---|",
        f"| **3DS Remote** (`source/`) | {t['r1'][0]} | {t['r1'][1]} |",
        f"| {t['r2'][0]} | {t['r2'][1]} | {t['r2'][2]} |",
        f"| {t['r3'][0]} | {t['r3'][1]} | {t['r3'][2]} |",
    ])
    usage = f"""```sh
3ds login --host 192.168.1.241    # {t['c_login']}
```

```sh
3ds ping                          # {t['c_ping']}

3ds status                        # {t['c_status']}
3ds titles [--all] [--json]       # {t['c_titles']}
3ds install game.cia [...]        # {t['c_install']}
3ds launch <name|tid>             # {t['c_launch']}
3ds delete <name|tid>
3ds ls /3ds ; 3ds get /x [local] ; 3ds put local /x ; 3ds rm /x
3ds reboot | shutdown | exit
3ds update [--force]              # {t['c_update']}

3ds press A ; 3ds press L+R ; 3ds press UP UP A ; 3ds press HOME
3ds touch 160 120 ; 3ds stick 1 0
3ds drag 273,175:2200 57,55:3000 40,67:1000   # x,y[:ms] ...
3ds snap [file.png]                           # 400x480
3ds screenshot [--screen bottom] file.png     # PNG, JPEG, WebP
```"""
    sec = "\n".join(f"- {s}" for s in t["sec"])
    boot = "\n".join(f"{i}. {s}" for i, s in enumerate(t["boot"], 1))
    return f"""# 3ds-remote

{lang_bar(code, True)}

{BADGES}

{t['intro']}

## {t['h_install']}

{t['fbi']}

![{t['qr_alt']}]({REPO}/releases/latest/download/3ds-remote-qr.png)

{t['release'].format(rel=REPO + '/releases')}

## {t['h_how']}

{t['three']}

{rows}

{t['client']}

## {t['h_client']}

{t['inst']}

```sh
pipx install "git+{REPO}#subdirectory=client"
```

{t['inst2'].format(latest=REPO + '/releases/latest')}

{t['inst3']}

## {t['h_usage']}

{t['pair']}

{usage}

{t['env']}

{t['needs']}

## {t['h_console']}

| {t['sh'][0]} | {t['sh'][1]} |
|---|---|
| {t['top'][0]} | {t['top'][1]} |
| {t['bottom'][0]} | {t['bottom'][1]} |

## {t['h_langs']}

{t['p1']}

{t['p2']}

{t['p3']}

## {t['h_security']}

{sec}

## {t['h_boot']}

{boot}

## {t['h_dev']}

{t['dev']}
"""


KEYS = set(T["es"])
for code, t in T.items():
    assert set(t) == KEYS, (code, KEYS ^ set(t))
    with open(os.path.join(ROOT, "docs", f"README.{code}.md"), "w") as f:
        f.write(render(code, t))

# language bar in the two hand-written READMEs (first "**...**" bar line after the title)
BAR = re.compile(r"^(?:\*\*[^*\n]+\*\*|\[[^\]\n]+\]\([^)\n]+\))(?: · .+)$", re.M)
for path, code, from_docs in ((os.path.join(ROOT, "README.md"), "en", False),
                              (os.path.join(ROOT, "docs", "README.pt-BR.md"), "pt-BR", True)):
    s = open(path).read()
    s, n = BAR.subn(lang_bar(code, from_docs), s, count=1)
    assert n == 1, path
    open(path, "w").write(s)
print("generated", len(T), "translations")
