# -*- coding: utf-8 -*-
"""Строки интерфейса и бота: ru / en."""

STRINGS = {
    "ru": {
        "app_title": "SDA Codes",
        "settings_title": "Настройки",
        "about_title": "Справка",
        "select_account": "Выберите аккаунт",
        "no_mafile": "Нет maFile",
        "code_hint": "Обновление каждые 30 с · клик по коду — копировать",
        "copy": "Копировать",
        "copied": "Скопировано",
        "accounts": "АККАУНТЫ",
        "add_mafile": "Добавить maFile",
        "online": "Подтверждения",
        "online_soon": "Подтверждения будут добавлены скоро",
        "sessions_pwd_section": "ПАРОЛЬ СЕССИЙ",
        "sessions_pwd_placeholder": "Новый пароль (пусто — не менять)",
        "sessions_pwd_help": (
            "Шифрует пароли Steam и cookies сессий. maFile не затрагивает.\n"
            "На диск сохраняется только проверка — сам пароль только в памяти."
        ),
        "sessions_pwd_title": "Пароль сессий",
        "sessions_pwd_prompt": "Введите пароль сессий:",
        "sessions_pwd_bad": "Неверный пароль сессий.",
        "sessions_pwd_required": "Сначала задайте пароль сессий в Настройках.",
        "conf_title": "Подтверждения Steam",
        "conf_login": "Логин",
        "conf_password": "Пароль Steam",
        "conf_proxy": "Прокси",
        "conf_check_proxy": "Проверить",
        "conf_proxy_warn": "При большом числе аккаунтов обязательно используйте прокси.",
        "conf_proxy_empty": "Введите прокси.",
        "conf_proxy_ok": "Успешно. IP: {ip}",
        "conf_proxy_invalid": "Не удалось разобрать прокси.",
        "conf_proxy_fail": "Ошибка: {err}",
        "conf_open": "Открыть подтверждения",
        "conf_need_password": "Введите пароль Steam.",
        "conf_no_secrets": "В maFile нет shared_secret или identity_secret.",
        "conf_count": "Найдено: {n}",
        "conf_empty": "Нет подтверждений.",
        "conf_allow": "Подтвердить",
        "conf_deny": "Отменить",
        "conf_confirm_all": "Подтвердить всё",
        "conf_all_done": "Все подтверждения обработаны.",
        "conf_step": "Шаг {step}/{total}: {action}",
        "conf_step_init": "Инициализация клиента",
        "conf_step_restore": "Восстановление сохранённой сессии",
        "conf_step_restore_skip": "Сохранённой сессии нет",
        "conf_step_auth_check": "Проверка авторизации",
        "conf_step_login": "Вход в аккаунт Steam",
        "conf_step_session_ok": "Сессия активна",
        "conf_step_cookies": "Сохранение cookies сессии",
        "conf_step_fetch": "Запрос списка подтверждений",
        "conf_step_parse": "Обработка ответа",
        "conf_step_done": "Готово",
        "conf_step_proxy_parse": "Разбор строки прокси",
        "conf_step_proxy_connect": "Подключение через прокси",
        "conf_step_proxy_ip": "Получение IP-адреса",
        "conf_step_confirm_allow": "Подтверждение операции",
        "conf_step_confirm_deny": "Отмена операции",
        "conf_step_confirm_item": "Подтверждение {step} из {total}",
        "settings": "Настройки",
        "about": "Справка",
        "language": "Язык",
        "bot_offline": "Бот не подключен",
        "bot_connecting": "Подключение…",
        "bot_connected": "Подключено: @{user}",
        "bot_error": "Бот: ошибка — {err}",
        "minimize": "Свернуть",
        "maximize": "Развернуть",
        "restore": "Восстановить",
        "close": "Закрыть",
        "save": "Сохранить",
        "proxy": "Прокси",
        "proxy_none": "Нет",
        "proxy_http": "HTTP",
        "proxy_socks": "SOCKS",
        "proxy_placeholder": "login:password@178.171.42.127:8888",
        "token_placeholder": "123456:AA...TOKEN",
        "settings_help": (
            "BOT_TOKEN — у @BotFather в Telegram: /newbot, затем скопируйте токен.\n"
            "Прокси — если api.telegram.org недоступен. HTTP или SOCKS.\n"
            "Формат обязательно: user:pass@host:port"
        ),
        "checking": "Проверка…",
        "pair_section": "КОД ПРИВЯЗКИ",
        "pair_new": "Новый",
        "pair_hint": (
            "Отправьте этот код боту одним сообщением — аккаунт попадёт в whitelist.\n"
            "Дальше: команды аккаунтов в Menu бота. Приложение должно быть запущено."
        ),
        "whitelist_empty": "Пользователи Telegram: пусто",
        "whitelist_label": "Пользователи Telegram: {ids}",
        "import_title": "Импорт maFile",
        "import_pick": "Выберите файлы или папку со сканированием .maFile",
        "import_files": "Файлы…",
        "import_folder": "Папка…",
        "import_folder_title": "Папка с maFile",
        "import_empty": "В папке нет .maFile",
        "import_ok": "Импортирован: {name}",
        "import_ok_many": "Импортировано: {n}",
        "enc_title": "Пароль шифрования SDA",
        "enc_prompt": "Введите passkey (как в Steam Desktop Authenticator):",
        "enc_import_src": "Passkey для импорта (источник)",
        "enc_import_vault": "Passkey хранилища SDA Codes",
        "enc_warn_title": "Шифрование",
        "enc_warn_body": (
            "В папке mafiles есть зашифрованные файлы SDA.\n"
            "Passkey не хранится на диск (как в оригинальном SDA) —\n"
            "его нужно ввести при каждом запуске.\n\n"
            "Нужен также manifest.json с salt/IV."
        ),
        "enc_bad": "Неверный passkey.",
        "enc_vault_bad": "Неверный passkey хранилища.",
        "token_bad": "Токен неверный:\n{err}",
        "about_text": (
            "SDA Codes\n\n"
            "Генератор Steam Guard кодов из maFile.\n"
            "Без логина в Steam — только 2FA-коды из локальных файлов.\n\n"
            "Хранение как в оригинальном SDA:\n"
            "• .maFile на диске может быть AES-шифром\n"
            "• salt/IV — в mafiles/manifest.json\n"
            "• passkey НЕ сохраняется на диск — только в памяти\n"
            "  до закрытия приложения (как в SDA)\n\n"
            "Telegram-бот:\n"
            "• BOT_TOKEN и код привязки — в Настройках\n"
            "• /start — введите код из приложения\n"
            "• команды аккаунтов — в Menu бота\n\n"
            "Не связан с Valve / Steam официально."
        ),
        # bot
        "bot_cmd_start": "Приветствие и справка",
        "bot_cmd_account": "Код: {label}",
        "bot_start_guest": (
            "<b>SDA Codes Bot</b>\n\n"
            "Отправьте <b>код привязки</b> из приложения (Настройки).\n"
            "После привязки все аккаунты доступны в <b>Menu → Commands</b>."
        ),
        "bot_start_user": (
            "<b>Добро пожаловать!</b>\n\n"
            "Бот выдаёт Steam Guard коды из локальных maFile.\n"
            "Выберите аккаунт в <b>Menu → Commands</b> — получите код.\n"
            "Код обновляется каждые 30 секунд.\n\n"
            "Приложение SDA Codes должно быть запущено."
        ),
        "bot_denied": "Доступ закрыт. Отправьте код привязки из Настроек приложения.",
        "bot_no_account": "Нет такого аккаунта.",
        "bot_no_secret": "Нет shared_secret для этого аккаунта.",
        "bot_paired": "Готово. Вы в whitelist. Аккаунты — в Menu → Commands.",
        "bot_paired_empty": "Готово. Вы в whitelist. Добавьте maFile в приложении.",
        "bot_need_pair": "Доступ закрыт. Отправьте код привязки из Настроек или /start.",
        "bot_hint_cmds": "Аккаунты — в Menu → Commands.",
    },
    "en": {
        "app_title": "SDA Codes",
        "settings_title": "Settings",
        "about_title": "About",
        "no_mafile": "No maFile",
        "code_hint": "Refreshes every 30 s · click code to copy",
        "copy": "Copy",
        "copied": "Copied",
        "accounts": "ACCOUNTS",
        "add_mafile": "Add maFile",
        "online": "Confirmations",
        "online_soon": "Online features soon",
        "sessions_pwd_section": "SESSIONS PASSWORD",
        "sessions_pwd_placeholder": "New password (empty — keep current)",
        "sessions_pwd_help": (
            "Encrypts Steam passwords and session cookies. Does not affect maFiles.\n"
            "Only a verifier is stored on disk — the password stays in memory."
        ),
        "sessions_pwd_title": "Sessions password",
        "sessions_pwd_prompt": "Enter sessions password:",
        "sessions_pwd_bad": "Invalid sessions password.",
        "sessions_pwd_required": "Set a sessions password in Settings first.",
        "conf_title": "Steam Confirmations",
        "conf_login": "Login",
        "conf_password": "Steam password",
        "conf_proxy": "Proxy",
        "conf_check_proxy": "Check",
        "conf_proxy_warn": "Use a proxy when you manage many accounts.",
        "conf_proxy_empty": "Enter a proxy.",
        "conf_proxy_ok": "OK. IP: {ip}",
        "conf_proxy_invalid": "Could not parse proxy.",
        "conf_proxy_fail": "Error: {err}",
        "conf_open": "Open confirmations",
        "conf_need_password": "Enter Steam password.",
        "conf_no_secrets": "maFile missing shared_secret or identity_secret.",
        "conf_count": "Found: {n}",
        "conf_empty": "No confirmations.",
        "conf_allow": "Allow",
        "conf_deny": "Deny",
        "conf_confirm_all": "Allow all",
        "conf_all_done": "All confirmations processed.",
        "conf_step": "Step {step}/{total}: {action}",
        "conf_step_init": "Initializing client",
        "conf_step_restore": "Restoring saved session",
        "conf_step_restore_skip": "No saved session",
        "conf_step_auth_check": "Checking authorization",
        "conf_step_login": "Logging into Steam",
        "conf_step_session_ok": "Session active",
        "conf_step_cookies": "Saving session cookies",
        "conf_step_fetch": "Fetching confirmations list",
        "conf_step_parse": "Processing response",
        "conf_step_done": "Done",
        "conf_step_proxy_parse": "Parsing proxy string",
        "conf_step_proxy_connect": "Connecting via proxy",
        "conf_step_proxy_ip": "Getting IP address",
        "conf_step_confirm_allow": "Allowing operation",
        "conf_step_confirm_deny": "Denying operation",
        "conf_step_confirm_item": "Confirming {step} of {total}",
        "settings": "Settings",
        "about": "About",
        "language": "Language",
        "bot_offline": "Bot not connected",
        "bot_connecting": "Connecting…",
        "bot_connected": "Connected: @{user}",
        "bot_error": "Bot error — {err}",
        "minimize": "Minimize",
        "maximize": "Maximize",
        "restore": "Restore",
        "close": "Close",
        "save": "Save",
        "proxy": "Proxy",
        "proxy_none": "None",
        "proxy_http": "HTTP",
        "proxy_socks": "SOCKS",
        "proxy_placeholder": "login:password@178.171.42.127:8888",
        "token_placeholder": "123456:AA...TOKEN",
        "settings_help": (
            "BOT_TOKEN — from @BotFather in Telegram: /newbot, then paste the token.\n"
            "Proxy — if api.telegram.org is blocked. HTTP or SOCKS.\n"
            "Required format: user:pass@host:port\n"
            "Example: login:password@178.171.42.127:8888"
        ),
        "checking": "Checking…",
        "pair_section": "PAIRING CODE",
        "pair_new": "New",
        "pair_hint": (
            "Send this code to the bot as one message — your account joins the whitelist.\n"
            "Then use account commands from the bot Menu. Keep the app running."
        ),
        "whitelist_empty": "Telegram users: empty",
        "whitelist_label": "Telegram users: {ids}",
        "import_title": "Import maFile",
        "import_pick": "Pick files or a folder to scan for .maFile",
        "import_files": "Files…",
        "import_folder": "Folder…",
        "import_folder_title": "Folder with maFile",
        "import_empty": "No .maFile in folder",
        "import_ok": "Imported: {name}",
        "import_ok_many": "Imported: {n}",
        "enc_title": "SDA encryption password",
        "enc_prompt": "Enter passkey (same as Steam Desktop Authenticator):",
        "enc_import_src": "Passkey for import (source)",
        "enc_import_vault": "SDA Codes vault passkey",
        "enc_warn_title": "Encryption",
        "enc_warn_body": (
            "Encrypted SDA files found in mafiles/.\n"
            "Passkey is not stored on disk (same as original SDA) —\n"
            "enter it each launch.\n\n"
            "You also need manifest.json with salt/IV."
        ),
        "enc_bad": "Invalid passkey.",
        "enc_vault_bad": "Invalid vault passkey.",
        "token_bad": "Invalid token:\n{err}",
        "about_text": (
            "SDA Codes\n\n"
            "Steam Guard code generator from maFile.\n"
            "No Steam login — local 2FA codes only.\n\n"
            "Storage like original SDA:\n"
            "• .maFile on disk may be AES ciphertext\n"
            "• salt/IV — in mafiles/manifest.json\n"
            "• passkey is NOT saved to disk — memory only\n"
            "  until the app closes (like SDA)\n\n"
            "Telegram bot:\n"
            "• BOT_TOKEN and pairing code — in Settings\n"
            "• /start — enter the code from the app\n"
            "• account commands — in the bot Menu\n\n"
            "Not affiliated with Valve / Steam."
        ),
        "bot_cmd_start": "Welcome and help",
        "bot_cmd_account": "Code: {label}",
        "bot_start_guest": (
            "<b>SDA Codes Bot</b>\n\n"
            "Send the <b>pairing code</b> from the app (Settings).\n"
            "After pairing, all accounts are in <b>Menu → Commands</b>."
        ),
        "bot_start_user": (
            "<b>Welcome back!</b>\n\n"
            "This bot returns Steam Guard codes from local maFiles.\n"
            "Pick an account in <b>Menu → Commands</b> to get a code.\n"
            "Codes refresh every 30 seconds.\n\n"
            "Keep the SDA Codes app running."
        ),
        "bot_denied": "Access denied. Send the pairing code from the app Settings.",
        "bot_no_account": "Unknown account.",
        "bot_no_secret": "No shared_secret for this account.",
        "bot_paired": "Done. You are on the whitelist. Accounts — Menu → Commands.",
        "bot_paired_empty": "Done. You are on the whitelist. Add a maFile in the app.",
        "bot_need_pair": "Access denied. Send the pairing code from Settings or /start.",
        "bot_hint_cmds": "Accounts — Menu → Commands.",
    },
}


def t(key: str, lang: str | None = None, **kwargs) -> str:
    lang = (lang or "ru").lower()
    if lang not in STRINGS:
        lang = "ru"
    text = STRINGS[lang].get(key) or STRINGS["ru"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
