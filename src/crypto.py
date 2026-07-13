# -*- coding: utf-8 -*-
"""Шифрование maFile как в Steam Desktop Authenticator (Jessecar96 FileEncryptor).

PBKDF2-HMAC-SHA1, 50000 итераций → AES-256-CBC PKCS7.
Salt/IV — в manifest.json (entries[].encryption_salt / encryption_iv).
Пароль в SDA на диск НЕ сохраняется — только в памяти на сессию.
"""
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

PBKDF2_ITERATIONS = 50000
KEY_SIZE = 32
SALT_LENGTH = 8
IV_LENGTH = 16


def _key(password: str, salt_b64: str) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha1",
        password.encode("utf-8"),
        base64.b64decode(salt_b64),
        PBKDF2_ITERATIONS,
        dklen=KEY_SIZE,
    )


def get_random_salt() -> str:
    return base64.b64encode(os.urandom(SALT_LENGTH)).decode("ascii")


def get_initialization_vector() -> str:
    return base64.b64encode(os.urandom(IV_LENGTH)).decode("ascii")


def encrypt_sda(password: str, salt_b64: str, iv_b64: str, plaintext: str) -> str:
    """Вернуть ciphertext в base64 (как пишет SDA в .maFile)."""
    key = _key(password, salt_b64)
    iv = base64.b64decode(iv_b64)
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_sda(password: str, salt_b64: str, iv_b64: str, ciphertext_b64: str) -> str | None:
    """Вернуть plaintext или None при неверном пароле."""
    try:
        key = _key(password, salt_b64)
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64.strip())
        decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")
    except Exception:
        return None
