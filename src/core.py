# -*- coding: utf-8 -*-
"""Генерация Steam Guard кодов. Хранение maFile как в SDA (manifest + шифр на диске)."""
import json
import os
from os import listdir
from os.path import isfile, join
import hmac
import struct
import time
from hashlib import sha1
import base64

from src.exceptions import MafilesNotFoundError
from src.crypto import (
    decrypt_sda,
    encrypt_sda,
    get_initialization_vector,
    get_random_salt,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAFILES_DIR = os.path.join(ROOT_DIR, "mafiles")
MANIFEST_NAME = "manifest.json"


def generate_one_time_code(shared_secret: str, timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    time_buffer = struct.pack(">Q", timestamp // 30)
    time_hmac = hmac.new(base64.b64decode(shared_secret), time_buffer, digestmod=sha1).digest()
    begin = ord(time_hmac[19:20]) & 0xF
    full_code = struct.unpack(">I", time_hmac[begin : begin + 4])[0] & 0x7FFFFFFF
    chars = "23456789BCDFGHJKMNPQRTVWXY"
    code = ""
    for _ in range(5):
        full_code, i = divmod(full_code, len(chars))
        code += chars[i]
    return code


def seconds_until_refresh(timestamp: int = None) -> int:
    if timestamp is None:
        timestamp = int(time.time())
    return 30 - (timestamp % 30)


def ensure_mafiles_dir() -> str:
    os.makedirs(MAFILES_DIR, exist_ok=True)
    return MAFILES_DIR


def get_mafiles() -> list:
    ensure_mafiles_dir()
    return sorted(
        [f for f in listdir(MAFILES_DIR) if isfile(join(MAFILES_DIR, f)) and f.endswith(".maFile")],
        key=str.lower,
    )


def empty_manifest() -> dict:
    return {
        "encrypted": False,
        "first_run": False,
        "entries": [],
        "periodic_checking": False,
        "periodic_checking_interval": 5,
        "periodic_checking_checkall": False,
        "auto_confirm_market_transactions": False,
        "auto_confirm_trades": False,
    }


def load_manifest(directory: str = None) -> dict | None:
    path = join(directory or MAFILES_DIR, MANIFEST_NAME)
    if not isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict, directory: str = None) -> None:
    ensure_mafiles_dir()
    path = join(directory or MAFILES_DIR, MANIFEST_NAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def is_encrypted_folder(directory: str = None) -> bool:
    man = load_manifest(directory)
    return bool(man and man.get("encrypted"))


def _manifest_entry_for(filename: str, manifest: dict | None) -> dict | None:
    if not manifest:
        return None
    for entry in manifest.get("entries") or []:
        if entry.get("filename") == filename:
            return entry
    return None


def steam_id_from_data(data: dict) -> int | None:
    session = data.get("Session") or {}
    sid = session.get("SteamID") or data.get("steamid") or data.get("SteamId")
    if sid is None:
        return None
    try:
        return int(sid)
    except (TypeError, ValueError):
        return None


def read_mafile(path: str, password: str | None = None, manifest: dict | None = None) -> dict:
    """Прочитать maFile. На диске может быть JSON или SDA-ciphertext — в память всегда dict."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    if not password:
        raise ValueError("Файл зашифрован (SDA). Нужен пароль.")

    filename = os.path.basename(path)
    directory = os.path.dirname(path)
    man = manifest if manifest is not None else load_manifest(directory)
    entry = _manifest_entry_for(filename, man)
    if not entry or not entry.get("encryption_salt") or not entry.get("encryption_iv"):
        raise ValueError(
            "Нет salt/IV в manifest.json рядом с файлом. "
            "Скопируйте и maFile, и manifest.json из SDA."
        )
    plain = decrypt_sda(password, entry["encryption_salt"], entry["encryption_iv"], raw)
    if plain is None:
        raise ValueError("Неверный пароль или повреждённый файл.")
    return json.loads(plain)


def open_mafiles(mafiles: list, password: str | None = None) -> dict:
    ensure_mafiles_dir()
    man = load_manifest()
    response = {}
    for mafile in mafiles:
        response[mafile] = read_mafile(join(MAFILES_DIR, mafile), password=password, manifest=man)
    return response


def folder_needs_password() -> bool:
    if is_encrypted_folder():
        return True
    for name in get_mafiles():
        path = join(MAFILES_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.loads(f.read())
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return True
    return False


def verify_passkey(password: str) -> bool:
    """Как Manifest.VerifyPasskey: расшифровать хотя бы один аккаунт."""
    man = load_manifest()
    if not man or not man.get("encrypted"):
        return True
    entries = man.get("entries") or []
    if not entries:
        return True
    for entry in entries:
        path = join(MAFILES_DIR, entry["filename"])
        if not isfile(path):
            continue
        try:
            read_mafile(path, password=password, manifest=man)
            return True
        except ValueError:
            return False
    return False


def save_account(data: dict, password: str | None = None) -> str:
    """
    Как Manifest.SaveAccount: пишет .maFile и обновляет manifest.json.
    password=None → plaintext; иначе AES на диске, encrypted=true.
    Возвращает имя файла.
    """
    ensure_mafiles_dir()
    man = load_manifest() or empty_manifest()
    if man.get("encrypted") and not password:
        raise ValueError("Хранилище зашифровано — нужен passkey.")

    sid = steam_id_from_data(data)
    if sid:
        filename = "%s.maFile" % sid
    else:
        name = data.get("account_name") or "account"
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        filename = safe + ".maFile"

    plaintext = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    salt = None
    iv = None
    if password:
        salt = get_random_salt()
        iv = get_initialization_vector()
        file_body = encrypt_sda(password, salt, iv, plaintext)
        man["encrypted"] = True
    else:
        if man.get("encrypted"):
            raise ValueError("Хранилище зашифровано — нужен passkey.")
        file_body = plaintext
        man["encrypted"] = False

    entry = {
        "encryption_iv": iv,
        "encryption_salt": salt,
        "filename": filename,
        "steamid": sid or 0,
    }
    entries = [e for e in (man.get("entries") or []) if e.get("filename") != filename]
    if sid:
        entries = [e for e in entries if int(e.get("steamid") or 0) != sid]
    entries.append(entry)
    man["entries"] = entries

    with open(join(MAFILES_DIR, filename), "w", encoding="utf-8") as f:
        f.write(file_body)
    save_manifest(man)
    return filename


def import_mafile(src_path: str, import_password: str | None = None, vault_password: str | None = None) -> str:
    """
    Импорт как в SDA: читаем (при необходимости расшифровываем источник в памяти),
    сохраняем в наше mafiles/.

    Если источник был зашифрован ИЛИ наше хранилище уже encrypted —
    на диск пишется снова ciphertext (нужен vault_password).
    Пароль на диск не сохраняется.
    """
    ensure_mafiles_dir()
    src_dir = os.path.dirname(os.path.abspath(src_path))
    src_man = load_manifest(src_dir)

    with open(src_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    source_was_encrypted = False
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        source_was_encrypted = True
        data = read_mafile(src_path, password=import_password, manifest=src_man)

    vault = load_manifest() or empty_manifest()
    vault_encrypted = bool(vault.get("encrypted"))

    must_encrypt = vault_encrypted or source_was_encrypted
    if must_encrypt:
        pwd = vault_password or import_password
        if not pwd:
            raise ValueError("Нужен passkey для записи зашифрованного maFile.")
        if vault_encrypted and vault_password and not verify_passkey(vault_password):
            raise ValueError("Неверный passkey хранилища.")
        return save_account(data, password=pwd)

    return save_account(data, password=None)


def account_label(mafile_name: str, data: dict) -> str:
    return data.get("account_name") or mafile_name.replace(".maFile", "")


def find_name(name: str, mafiles: list, mafiles_dict: dict):
    name_lower = name.lower().strip()
    for mafile in mafiles:
        if name_lower == mafile.replace(".maFile", "").lower():
            return mafile
    for mafile, data in mafiles_dict.items():
        if name_lower == (data.get("account_name") or "").lower():
            return mafile
        if name_lower == mafile.lower():
            return mafile
    try:
        idx = int(name.strip())
        if 1 <= idx <= len(mafiles):
            return mafiles[idx - 1]
    except ValueError:
        pass
    return False


def main():
    mafiles = get_mafiles()
    if not mafiles:
        raise MafilesNotFoundError("Put mafiles in %s" % MAFILES_DIR)

    password = None
    if folder_needs_password():
        password = input("SDA encryption passkey: ").strip()
        if is_encrypted_folder() and not verify_passkey(password):
            raise SystemExit("Invalid passkey")

    mafiles_dict = open_mafiles(mafiles, password=password)

    print("mafiles:")
    for i, item in enumerate(mafiles):
        print("%s. %s" % (i + 1, account_label(item, mafiles_dict[item])))

    while True:
        name = input("input mafile name or index to generate GuardCode: ").strip()
        if name in ("menu", "accs", "mafiles", "m"):
            print("mafiles:")
            for i, item in enumerate(mafiles):
                print("%s. %s" % (i + 1, account_label(item, mafiles_dict[item])))
            continue

        mafile_name = find_name(name, mafiles, mafiles_dict)
        if mafile_name is False:
            print("Invalid name")
            continue
        shared_secret = mafiles_dict[mafile_name]["shared_secret"]
        code = generate_one_time_code(shared_secret)
        print("%s GuardCode: %s" % (account_label(mafile_name, mafiles_dict[mafile_name]), code))


if __name__ == "__main__":
    main()
