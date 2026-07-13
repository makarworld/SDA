# -*- coding: utf-8 -*-
"""Telegram-бот на python-telegram-bot (выдача Steam Guard кодов)."""
import asyncio
import re

import requests
from PyQt6.QtCore import QThread, pyqtSignal
from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.core import generate_one_time_code
from src.i18n import t
from src.settings import get_language, get_pair_code, load_settings, save_settings


def verify_bot_token(token: str, proxy: str | None = None) -> tuple[bool, str]:
    """getMe: (True, username) или (False, текст ошибки)."""
    token = (token or "").strip()
    if not token:
        return False, "пустой токен"
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        r = requests.get(
            "https://api.telegram.org/bot%s/getMe" % token,
            timeout=15,
            proxies=proxies,
        )
        data = r.json()
    except Exception as e:
        return False, str(e)
    if not data.get("ok"):
        return False, data.get("description") or "неверный токен"
    username = (data.get("result") or {}).get("username") or "?"
    return True, username


def command_slug(name: str) -> str:
    """Telegram Bot API: 1–32 символа [a-z0-9_], не начинается с цифры."""
    s = (name or "").lower()
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "account"
    if s[0].isdigit():
        s = "a" + s
    return s[:32]


def assign_slugs(accounts: list[dict]) -> list[dict]:
    """Добавляет уникальный slug к каждому аккаунту (коллизии → _2, _3…)."""
    used: set[str] = set()
    out = []
    for acc in accounts:
        base = command_slug(acc.get("label") or acc.get("name") or "account")
        slug = base
        n = 2
        while slug in used or slug == "start":
            suffix = "_%s" % n
            slug = (base[: max(1, 32 - len(suffix))] + suffix)[:32]
            n += 1
        used.add(slug)
        row = dict(acc)
        row["slug"] = slug
        out.append(row)
    return out


def _lang() -> str:
    return get_language()


def _whitelist() -> list[int]:
    return [int(x) for x in (load_settings().get("whitelist") or [])]


def _is_allowed(user_id: int) -> bool:
    return int(user_id) in _whitelist()


def _accounts(context: ContextTypes.DEFAULT_TYPE) -> list[dict]:
    get_accounts = context.application.bot_data.get("get_accounts")
    raw = get_accounts() if callable(get_accounts) else []
    return assign_slugs(list(raw or []))


async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    text = (update.message.text or "").strip()
    if not text.startswith("/"):
        return
    cmd = text.split()[0].lstrip("/").split("@")[0].lower()
    lang = _lang()

    if cmd == "start":
        if _is_allowed(update.effective_user.id):
            msg = t("bot_start_user", lang)
        else:
            msg = t("bot_start_guest", lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    if not _is_allowed(update.effective_user.id):
        await update.message.reply_text(t("bot_denied", lang))
        return

    accounts = _accounts(context)
    by_slug = {a["slug"]: a for a in accounts}
    acc = by_slug.get(cmd)
    if not acc:
        await update.message.reply_text(t("bot_no_account", lang))
        return
    secret = acc.get("secret")
    if not secret:
        await update.message.reply_text(t("bot_no_secret", lang))
        return
    code = generate_one_time_code(secret)
    await update.message.reply_text(
        "<code>%s</code>" % code,
        parse_mode=ParseMode.HTML,
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Код привязки из настроек → whitelist."""
    if not update.message or not update.effective_user:
        return
    raw = (update.message.text or "").strip()
    if not raw or raw.startswith("/"):
        return

    lang = _lang()
    pair = get_pair_code()
    if not pair or raw.upper() != pair:
        if not _is_allowed(update.effective_user.id):
            await update.message.reply_text(t("bot_need_pair", lang))
        else:
            await update.message.reply_text(t("bot_hint_cmds", lang))
        return

    uid = int(update.effective_user.id)
    wl = list(_whitelist())
    if uid not in wl:
        wl.append(uid)
        settings = load_settings()
        settings["whitelist"] = wl
        save_settings(settings)

    accounts = _accounts(context)
    if accounts:
        await update.message.reply_text(t("bot_paired", lang))
    else:
        await update.message.reply_text(t("bot_paired_empty", lang))


class TelegramBotWorker(QThread):
    status = pyqtSignal(str)
    stopped = pyqtSignal()

    def __init__(self, token: str, get_accounts_fn, parent=None, proxy: str | None = None):
        super().__init__(parent)
        self.token = (token or "").strip()
        self.get_accounts_fn = get_accounts_fn
        self.proxy = (proxy or "").strip() or None
        self._stop = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._app: Application | None = None

    def stop(self):
        self._stop = True
        loop = self._loop
        if loop and loop.is_running():
            # разбудить sleep-цикл сразу
            loop.call_soon_threadsafe(lambda: None)

    def run(self):
        if not self.token:
            self.status.emit(t("bot_offline"))
            self.stopped.emit()
            return

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_main())
        except Exception as e:
            self.status.emit(t("bot_error", err=str(e)))
        finally:
            try:
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            except Exception:
                pass
            self._loop.close()
            self._loop = None
            self.stopped.emit()

    async def _async_main(self):
        lang = _lang()
        self.status.emit(t("bot_connecting", lang))
        builder = Application.builder().token(self.token)
        if self.proxy:
            builder = builder.proxy(self.proxy).get_updates_proxy(self.proxy)
        app = builder.build()
        app.bot_data["get_accounts"] = self.get_accounts_fn
        app.add_handler(MessageHandler(filters.COMMAND, on_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
        self._app = app

        await app.initialize()
        me = await app.bot.get_me()
        accounts = assign_slugs(list(self.get_accounts_fn() or []))
        commands = [BotCommand("start", t("bot_cmd_start", lang))]
        for a in accounts:
            desc = t("bot_cmd_account", lang, label=a.get("label") or a["slug"])
            commands.append(BotCommand(a["slug"], desc[:256]))
        await app.bot.set_my_commands(commands)
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        self.status.emit(t("bot_connected", lang, user=me.username or "?"))

        while not self._stop:
            await asyncio.sleep(0.1)

        # быстрый выход — не ждать сеть
        async def _quiet(coro):
            try:
                await asyncio.wait_for(coro, timeout=0.4)
            except Exception:
                pass

        if app.updater.running:
            await _quiet(app.updater.stop())
        await _quiet(app.stop())
        await _quiet(app.shutdown())
        self._app = None
