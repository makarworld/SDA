# -*- coding: utf-8 -*-
"""Настройки приложения (BOT_TOKEN, whitelist, язык). pair_code — только в памяти."""
import json
import os
import re
import secrets
import string

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(ROOT, "settings.json")
_PAIR_LETTERS = string.ascii_uppercase

# код привязки только на сессию, не пишем в settings.json
_pair_code: str = ""


def new_pair_code() -> str:
    """4 заглавные латинские буквы."""
    return "".join(secrets.choice(_PAIR_LETTERS) for _ in range(4))


def is_valid_pair_code(code: str) -> bool:
    return bool(code) and re.fullmatch(r"[A-Z]{4}", code.strip().upper()) is not None


def get_pair_code() -> str:
    global _pair_code
    if not _pair_code:
        _pair_code = new_pair_code()
    return _pair_code


def set_pair_code(code: str | None = None) -> str:
    """Задать код (или сгенерировать новый). Не сохраняется на диск."""
    global _pair_code
    _pair_code = (code or new_pair_code()).strip().upper()
    if not is_valid_pair_code(_pair_code):
        _pair_code = new_pair_code()
    return _pair_code


def _default():
    return {
        "bot_token": "",
        "proxy_type": "",  # "" | http | socks5
        "proxy": "",
        "whitelist": [],
        "language": "ru",
    }


def proxy_url(data: dict | None = None) -> str | None:
    """URL для requests / PTB."""
    data = data if data is not None else load_settings()
    ptype = (data.get("proxy_type") or "").strip().lower()
    raw = (data.get("proxy") or "").strip()
    if not ptype or not raw:
        return None
    if "://" in raw:
        return raw
    if ptype == "http":
        return "http://" + raw
    if ptype in ("socks", "socks5"):
        return "socks5://" + raw
    return None


def load_settings() -> dict:
    if not os.path.isfile(SETTINGS_PATH):
        data = _default()
        save_settings(data)
        return data
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    base = _default()
    base.update(data)
    base.pop("pair_code", None)  # никогда из файла
    if not isinstance(base.get("whitelist"), list):
        base["whitelist"] = []
    lang = (base.get("language") or "ru").strip().lower()
    base["language"] = lang if lang in ("ru", "en") else "ru"
    if (base.get("proxy_type") or "").strip().lower() in ("mtproxy", "mtproto"):
        base["proxy_type"] = ""
        save_settings(base)
    return base


def save_settings(data: dict) -> None:
    out = {k: v for k, v in data.items() if k != "pair_code"}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def get_language() -> str:
    return load_settings().get("language") or "ru"
