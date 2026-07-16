# SDA Codes

Desktop-приложение для Steam Guard: генерация кодов из **maFile**, Telegram-бот и онлайн-подтверждения Steam. Интерфейс на русском и английском.

## Возможности

- **Коды 2FA** — из локальных `.maFile` без входа в Steam (как Steam Desktop Authenticator).
- **Импорт maFile** — один файл, несколько файлов или скан всей папки; сохранение как `login.maFile`.
- **Шифрование** — формат хранения как в SDA: ciphertext на диске, passkey только в памяти.
- **Telegram-бот** — выдача кодов по whitelist; настройка в GUI.
- **Подтверждения Steam** — вход по паролю аккаунта, список pending-подтверждений, Allow / Deny и «Подтвердить всё».
- **Прокси** — опционально для онлайн-режима, с проверкой IP.
- **Пароль сессий** — отдельный пароль для шифрования сохранённых Steam-cookies (`sessions/`).

## Быстрый старт

```bash
pip install -r requirements.txt
python gui.py
```

Или `start.bat` (Windows).

## Сборка exe

```bash
compile.bat
```

Создаёт `gui.exe` в корне проекта (PyInstaller, onefile, windowed). Папки `mafiles/`, `sessions/` и `settings.json` должны лежать **рядом с exe**.

## Хранение данных

| Путь | Назначение |
|------|------------|
| `mafiles/` | `.maFile` и `manifest.json` (шифрование как в SDA) |
| `sessions/` | Зашифрованные cookies Steam по логину (`login.json`) |
| `settings.json` | Язык, Telegram, verifier пароля сессий |

Файлы с секретами в `.gitignore` — **не коммитить**.

### Passkey maFile

При `encrypted: true` в manifest приложение запросит passkey при старте. Passkey **не сохраняется** на диск.

### Пароль сессий

Задаётся в **Настройки → Пароль сессий**. На диск пишется только verifier (salt + PBKDF2); сам пароль держится в памяти до закрытия приложения. Нужен для кнопки **Подтверждения** у аккаунта.

## Подтверждения Steam

1. Задайте пароль сессий в настройках (один раз).
2. Нажмите **Подтверждения** у нужного аккаунта.
3. Введите пароль Steam и при необходимости прокси (`host:port`, `user:pass@host:port`, `host:port;user;pass`).
4. **Открыть подтверждения** — загрузка списка; далее Allow / Deny или **Подтвердить всё**.

> Онлайн-режим использует пароль Steam и сеть. Используйте прокси, если IP аккаунта должен совпадать с обычным входом.

## CLI

```bash
python app.py
```

Консольная генерация кодов (без GUI).

## Структура проекта

```
gui.py / app.py              — точки входа
src/
  core.py                    — maFile, коды, manifest
  gui_app.py                 — главное окно, настройки
  confirmations_dialog.py    — окно подтверждений
  steam_online.py            — логин Steam, getlist, allow/cancel
  sessions_vault.py          — шифрование сессий
  proxy_parse.py             — парсинг и проверка прокси
  crypto.py                  — AES (SDA-совместимость)
  settings.py, i18n.py       — настройки и локализация
  telegram_bot.py            — Telegram-бот
compile.bat / start.bat      — сборка и запуск (Windows)
requirements.txt
```

## Зависимости

- **PyQt6** — GUI
- **cryptography** — шифрование maFile и сессий
- **pysteamauth**, **steampy**, **aiohttp-socks** — онлайн-подтверждения
- **python-telegram-bot**, **requests**, **PySocks** — бот и прокси

## Лицензия

Используйте на свой риск. Не храните maFile и пароли в публичных репозиториях.
