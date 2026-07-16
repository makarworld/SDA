# -*- coding: utf-8 -*-
"""Шифрованное хранилище Steam-паролей и cookies. Master-пароль — только verifier в settings."""
import base64
import hashlib
import json
import os
import re
import secrets

from src.core import ROOT_DIR
from src.crypto import (
    PBKDF2_ITERATIONS,
    decrypt_sda,
    encrypt_sda,
    get_initialization_vector,
    get_random_salt,
)
from src.settings import load_settings, save_settings

SESSIONS_DIR = os.path.join(ROOT_DIR, "sessions")


def ensure_sessions_dir() -> str:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    return SESSIONS_DIR


def _safe_login(login: str) -> str:
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in login.strip())
    return safe or "account"


def _vault_path(login: str) -> str:
    return os.path.join(ensure_sessions_dir(), _safe_login(login) + ".json")


def make_verifier(password: str, salt_b64: str) -> str:
    key = hashlib.pbkdf2_hmac(
        "sha1",
        password.encode("utf-8"),
        base64.b64decode(salt_b64),
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    return base64.b64encode(key).decode("ascii")


def sessions_configured(data: dict | None = None) -> bool:
    data = data if data is not None else load_settings()
    return bool((data.get("sessions_salt") or "").strip() and (data.get("sessions_verifier") or "").strip())


def verify_sessions_password(password: str, data: dict | None = None) -> bool:
    data = data if data is not None else load_settings()
    salt = (data.get("sessions_salt") or "").strip()
    verifier = (data.get("sessions_verifier") or "").strip()
    if not salt or not verifier or not password:
        return False
    return secrets.compare_digest(make_verifier(password, salt), verifier)


def set_sessions_password(password: str, data: dict | None = None) -> dict:
    """Записать salt+verifier в settings. Сам password на диск не пишется."""
    data = dict(data if data is not None else load_settings())
    salt = get_random_salt()
    data["sessions_salt"] = salt
    data["sessions_verifier"] = make_verifier(password, salt)
    save_settings(data)
    return data


def save_account_blob(
    login: str,
    sessions_password: str,
    *,
    steam_password: str | None = None,
    proxy: str | None = None,
    cookies: dict | None = None,
    steamid: int | None = None,
) -> None:
    ensure_sessions_dir()
    path = _vault_path(login)
    existing = {}
    if os.path.isfile(path) and sessions_password:
        existing = load_account_blob(login, sessions_password) or {}

    payload = {
        "steam_password": steam_password if steam_password is not None else existing.get("steam_password", ""),
        "proxy": proxy if proxy is not None else existing.get("proxy", ""),
        "cookies": cookies if cookies is not None else existing.get("cookies", {}),
        "steamid": steamid if steamid is not None else existing.get("steamid"),
    }
    salt = get_random_salt()
    iv = get_initialization_vector()
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    body = {
        "encryption_salt": salt,
        "encryption_iv": iv,
        "ciphertext": encrypt_sda(sessions_password, salt, iv, plaintext),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=2)


def load_account_blob(login: str, sessions_password: str) -> dict | None:
    path = _vault_path(login)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        body = json.load(f)
    plain = decrypt_sda(
        sessions_password,
        body.get("encryption_salt") or "",
        body.get("encryption_iv") or "",
        body.get("ciphertext") or "",
    )
    if plain is None:
        return None
    try:
        return json.loads(plain)
    except json.JSONDecodeError:
        return None
