# -*- coding: utf-8 -*-
"""Парсинг прокси login/password/host/port и проверка IP."""
import ipaddress
import re
from urllib.parse import quote

import requests

IP_CHECK_URL = "https://api.ipify.org?format=json"
PROXY_TIMEOUT = 10


def _is_port(s: str) -> bool:
    try:
        p = int(s)
        return 1 <= p <= 65535
    except ValueError:
        return False


def _is_host(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        pass
    return bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*", s)) and "." in s


def parse_proxy(raw: str) -> dict | None:
    """
    Распознать HTTP/SOCKS прокси из строки.
    Разделители : ; @ — части login, password, host, port в любой перестановке.
    Возвращает {scheme, login, password, host, port, url} или None.
    """
    text = (raw or "").strip()
    if not text:
        return None
    if "://" in text:
        scheme = "http" if text.lower().startswith("http://") else "socks5"
        rest = text.split("://", 1)[1]
        parts = re.split(r"[:;@]", rest)
    else:
        scheme = "http"
        parts = re.split(r"[:;@]", text)

    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        return None

    host = port = login = password = None
    rest = []

    for p in parts:
        if _is_port(p) and port is None:
            port = int(p)
        elif _is_host(p) and host is None:
            host = p
        else:
            rest.append(p)

    if host is None or port is None:
        # fallback: последнее число — порт, предпоследний token — host
        nums = [p for p in parts if _is_port(p)]
        hosts = [p for p in parts if _is_host(p)]
        if nums and hosts:
            port = int(nums[-1])
            host = hosts[-1]
            used = {str(port), host}
            creds = [p for p in parts if p not in used]
            if len(creds) >= 2:
                login, password = creds[0], creds[1]
            elif len(creds) == 1:
                login, password = creds[0], ""
            else:
                login, password = "", ""
        else:
            return None
    else:
        if len(rest) >= 2:
            login, password = rest[0], rest[1]
        elif len(rest) == 1:
            login, password = rest[0], ""
        else:
            login, password = "", ""

    # auto-detect socks if scheme ambiguous and port common for socks
    if "://" not in text and port in (1080, 9050, 9150):
        scheme = "socks5"

    if login:
        auth = quote(login, safe="") + ":" + quote(password or "", safe="") + "@"
    else:
        auth = ""
    url = "%s://%s%s:%d" % (scheme, auth, host, port)
    return {
        "scheme": scheme,
        "login": login or "",
        "password": password or "",
        "host": host,
        "port": port,
        "url": url,
    }


def proxy_requests_dict(parsed: dict) -> dict:
    return {"http": parsed["url"], "https": parsed["url"]}


def check_proxy(raw: str, report=None) -> tuple[bool, str]:
    """Проверить прокси, вернуть (ok, message с IP или ошибкой). Таймаут 10 с."""
    if report:
        report(1, 3, "conf_step_proxy_parse")
    parsed = parse_proxy(raw)
    if not parsed:
        return False, "invalid"
    if report:
        report(2, 3, "conf_step_proxy_connect")
    try:
        if report:
            report(3, 3, "conf_step_proxy_ip")
        r = requests.get(
            IP_CHECK_URL,
            proxies=proxy_requests_dict(parsed),
            timeout=PROXY_TIMEOUT,
        )
        r.raise_for_status()
        ip = r.json().get("ip") or r.text.strip()
        return True, ip
    except Exception as e:
        return False, str(e)[:200]
