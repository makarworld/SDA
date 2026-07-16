# -*- coding: utf-8 -*-
"""Steam login и mobile confirmations (по conf.py)."""
import asyncio
import json
import time
from typing import Any, Callable

from pysteamauth.auth import Steam
from pysteamauth.base import BaseCookieStorage, BaseRequestStrategy
from steampy import guard as steampy_guard

from src.proxy_parse import parse_proxy

ProgressFn = Callable[[int, int, str], None]


class ProxyRequestStrategy(BaseRequestStrategy):
    def __init__(self, proxy_url: str | None = None):
        super().__init__()
        self._proxy_url = proxy_url

    def _create_session(self):
        import aiohttp

        if self._proxy_url and self._proxy_url.startswith("socks"):
            from aiohttp_socks import ProxyConnector

            connector = ProxyConnector.from_url(self._proxy_url, ssl=False)
            return aiohttp.ClientSession(connector=connector)
        return super()._create_session()

    async def request(self, url: str, method: str, **kwargs: Any):
        if self._proxy_url and not self._proxy_url.startswith("socks"):
            kwargs.setdefault("proxy", self._proxy_url)
        return await super().request(url, method, **kwargs)


def _noop_progress(_step: int, _total: int, _key: str) -> None:
    pass


def _mafile_fields(data: dict) -> dict:
    session = data.get("Session") or {}
    sid = session.get("SteamID") or data.get("steamid")
    return {
        "steamid": int(sid) if sid else None,
        "device_id": data.get("device_id") or "",
        "identity_secret": data.get("identity_secret") or "",
        "shared_secret": data.get("shared_secret") or "",
    }


def _conf_params(data: dict, tag: str) -> dict:
    fields = _mafile_fields(data)
    sid = str(fields["steamid"])
    ts = int(time.time())
    key = steampy_guard.generate_confirmation_key(fields["identity_secret"], tag, ts)
    if isinstance(key, bytes):
        key = key.decode()
    return {
        "p": fields["device_id"],
        "a": sid,
        "k": key,
        "t": str(ts),
        "m": "android",
        "tag": tag,
    }


def _proxy_url(proxy_raw: str | None) -> str | None:
    if not proxy_raw:
        return None
    parsed = parse_proxy(proxy_raw)
    return parsed["url"] if parsed else None


async def _export_cookies(steam: Steam) -> dict:
    domains = (
        "steamcommunity.com",
        "store.steampowered.com",
        "help.steampowered.com",
    )
    out = {}
    for domain in domains:
        cookies = await steam.cookies(domain)
        if cookies:
            out[domain] = dict(cookies)
    return out


async def open_confirmations_flow(
    login: str,
    password: str,
    mafile: dict,
    proxy_raw: str | None,
    saved_cookies: dict | None,
    report: ProgressFn | None = None,
) -> tuple[dict, list]:
    """Вход + список подтверждений. 7 шагов."""
    report = report or _noop_progress
    total = 7

    report(1, total, "conf_step_init")
    fields = _mafile_fields(mafile)
    storage = BaseCookieStorage()
    if saved_cookies:
        report(2, total, "conf_step_restore")
        await storage.set(login=login, cookies=saved_cookies)
    else:
        report(2, total, "conf_step_restore_skip")

    steam = Steam(
        login=login,
        password=password,
        steamid=fields["steamid"],
        shared_secret=fields["shared_secret"],
        identity_secret=fields["identity_secret"],
        device_id=fields["device_id"],
        cookie_storage=storage,
        request_strategy=ProxyRequestStrategy(_proxy_url(proxy_raw)),
    )

    report(3, total, "conf_step_auth_check")
    if not await steam.is_authorized():
        report(4, total, "conf_step_login")
        await steam.login_to_steam()
    else:
        report(4, total, "conf_step_session_ok")

    report(5, total, "conf_step_cookies")
    cookies = await _export_cookies(steam)

    report(6, total, "conf_step_fetch")
    headers = {"X-Requested-With": "com.valvesoftware.android.steam.community"}
    body = await steam.request(
        "https://steamcommunity.com/mobileconf/getlist",
        params=_conf_params(mafile, "conf"),
        headers=headers,
    )

    report(7, total, "conf_step_parse")
    js = json.loads(body)
    if not js.get("success"):
        need = js.get("needauth")
        raise RuntimeError("needauth" if need else (js.get("message") or "getlist failed"))
    return cookies, js.get("conf") or []


async def login_and_export(
    login: str,
    password: str,
    mafile: dict,
    proxy_raw: str | None,
    saved_cookies: dict | None,
    report: ProgressFn | None = None,
) -> tuple[dict, int | None]:
    cookies, _confs = await open_confirmations_flow(
        login, password, mafile, proxy_raw, saved_cookies, report
    )
    sid = None
    session = mafile.get("Session") or {}
    sid_raw = session.get("SteamID") or mafile.get("steamid")
    if sid_raw:
        sid = int(sid_raw)
    return cookies, sid


async def fetch_confirmations(
    login: str,
    password: str,
    mafile: dict,
    proxy_raw: str | None,
    saved_cookies: dict | None,
    report: ProgressFn | None = None,
) -> list:
    _cookies, confs = await open_confirmations_flow(
        login, password, mafile, proxy_raw, saved_cookies, report
    )
    return confs


async def confirm_one(
    login: str,
    password: str,
    mafile: dict,
    proxy_raw: str | None,
    saved_cookies: dict | None,
    conf: dict,
    op: str,
    report: ProgressFn | None = None,
) -> None:
    if op not in ("allow", "cancel"):
        raise ValueError("op must be allow or cancel")
    report = report or _noop_progress
    total = 4
    fields = _mafile_fields(mafile)
    storage = BaseCookieStorage()

    report(1, total, "conf_step_init")
    if saved_cookies:
        report(2, total, "conf_step_restore")
        await storage.set(login=login, cookies=saved_cookies)
    else:
        report(2, total, "conf_step_restore_skip")

    steam = Steam(
        login=login,
        password=password,
        steamid=fields["steamid"],
        shared_secret=fields["shared_secret"],
        identity_secret=fields["identity_secret"],
        device_id=fields["device_id"],
        cookie_storage=storage,
        request_strategy=ProxyRequestStrategy(_proxy_url(proxy_raw)),
    )
    report(3, total, "conf_step_auth_check")
    if not await steam.is_authorized():
        await steam.login_to_steam()

    key = "conf_step_confirm_allow" if op == "allow" else "conf_step_confirm_deny"
    report(4, total, key)
    tag = "allow" if op == "allow" else "reject"
    params = _conf_params(mafile, tag)
    params.update({
        "op": op,
        "cid": str(conf["id"]),
        "ck": str(conf["nonce"]),
    })
    headers = {"X-Requested-With": "XMLHttpRequest"}
    body = await steam.request(
        "https://steamcommunity.com/mobileconf/ajaxop",
        params=params,
        headers=headers,
    )
    js = json.loads(body)
    if not js.get("success"):
        raise RuntimeError(js.get("message") or "ajaxop failed")


async def confirm_all(
    login: str,
    password: str,
    mafile: dict,
    proxy_raw: str | None,
    saved_cookies: dict | None,
    confs: list,
    report: ProgressFn | None = None,
) -> None:
    report = report or _noop_progress
    total = len(confs)
    for i, c in enumerate(confs, 1):
        report(i, total, "conf_step_confirm_item")
        await confirm_one(login, password, mafile, proxy_raw, saved_cookies, c, "allow", _noop_progress)


def run_async(coro):
    return asyncio.run(coro)
