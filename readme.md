# SDA Codes

Генератор Steam Guard кодов из maFile. Без логина в Steam.

## GUI

```bash
pip install -r requirements.txt
python gui.py
```

Хранение как в оригинальном **Steam Desktop Authenticator**:

| | |
|---|---|
| На диске | ciphertext AES-256-CBC (если encryption включён) |
| `manifest.json` | `encryption_salt`, `encryption_iv`, `filename`, `steamid` |
| Passkey | **не сохраняется** — только в памяти до закрытия |

При запуске, если `encrypted: true`, приложение спросит passkey (как SDA).

Импорт зашифрованного maFile: читается с паролем источника + его `manifest.json`, в нашу папку снова пишется **шифр** и обновляется наш `manifest.json`.

Telegram-бот: токен и код привязки в Настройках. Язык RU/EN переключается на главном экране (GUI и бот).

## CLI

```bash
python app.py
```

## Структура

```
gui.py / app.py   — точки входа
src/              — код приложения
mafiles/          — .maFile и manifest.json
settings.json     — токен, whitelist, язык (не коммитить)
```
