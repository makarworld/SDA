# -*- coding: utf-8 -*-
"""Окно подтверждений Steam."""
import os

from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.i18n import t
from src.proxy_parse import check_proxy
from src.sessions_vault import load_account_blob, save_account_blob
from src.steam_online import confirm_all, confirm_one, open_confirmations_flow, run_async


class _AsyncWorker(QThread):
    finished_ok = pyqtSignal(object)
    finished_err = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, coro_fn=None, parent=None):
        super().__init__(parent)
        self._coro_fn = coro_fn

    def run(self):
        try:
            self.finished_ok.emit(run_async(self._coro_fn()))
        except Exception as e:
            self.finished_err.emit(str(e))


class _SyncWorker(QThread):
    finished_ok = pyqtSignal(object)
    finished_err = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, fn=None, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.finished_ok.emit(self._fn())
        except Exception as e:
            self.finished_err.emit(str(e))


class ConfirmationsDialog(QDialog):
    def __init__(
        self,
        owner,
        login: str,
        mafile: dict,
        mafile_name: str,
        sessions_password: str,
        icon_path: str = "",
    ):
        super().__init__(None)
        from src.gui_app import TitleBar, lang

        self._lang = lang
        self._owner = owner
        self._login = login
        self._mafile = mafile
        self._mafile_name = mafile_name
        self._sessions_password = sessions_password
        self._cookies: dict = {}
        self._confs: list = []
        self._worker = None
        self._closing = False

        self.setObjectName("settingsDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setMinimumWidth(360)
        if icon_path and os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(
            TitleBar(
                self,
                title=t("conf_title", lang()),
                show_max=False,
                show_min=False,
                on_close=self._safe_close,
            )
        )

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        lay.addWidget(QLabel(t("conf_login", lang())))
        self.login_edit = QLineEdit(login)
        self.login_edit.setReadOnly(True)
        lay.addWidget(self.login_edit)

        lay.addWidget(QLabel(t("conf_password", lang())))
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.pass_edit)

        lay.addWidget(QLabel(t("conf_proxy", lang())))
        proxy_row = QHBoxLayout()
        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText(t("proxy_placeholder", lang()))
        self.proxy_check_btn = QPushButton(t("conf_check_proxy", lang()))
        self.proxy_check_btn.clicked.connect(self._check_proxy)
        proxy_row.addWidget(self.proxy_edit, 1)
        proxy_row.addWidget(self.proxy_check_btn)
        lay.addLayout(proxy_row)

        self.proxy_status = QLabel("")
        self.proxy_status.setObjectName("hint")
        self.proxy_status.setWordWrap(True)
        lay.addWidget(self.proxy_status)

        self.proxy_warn = QLabel(t("conf_proxy_warn", lang()))
        self.proxy_warn.setObjectName("error")
        self.proxy_warn.setWordWrap(True)
        lay.addWidget(self.proxy_warn)

        self.open_btn = QPushButton(t("conf_open", lang()))
        self.open_btn.setObjectName("primary")
        self.open_btn.clicked.connect(self._open_confirmations)
        lay.addWidget(self.open_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("hint")
        self.status_label.setWordWrap(True)
        lay.addWidget(self.status_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMinimumHeight(160)
        self.list_host = QWidget()
        self.list_lay = QVBoxLayout(self.list_host)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(6)
        self.list_lay.addStretch(1)
        self.scroll.setWidget(self.list_host)
        lay.addWidget(self.scroll, 1)

        self.confirm_all_btn = QPushButton(t("conf_confirm_all", lang()))
        self.confirm_all_btn.setObjectName("primary")
        self.confirm_all_btn.setEnabled(False)
        self.confirm_all_btn.clicked.connect(self._confirm_all)
        lay.addWidget(self.confirm_all_btn)

        close_row = QHBoxLayout()
        self.close_btn = QPushButton(t("close", lang()))
        self.close_btn.clicked.connect(self._safe_close)
        close_row.addStretch(1)
        close_row.addWidget(self.close_btn)
        lay.addLayout(close_row)

        root.addWidget(body)
        self._load_vault()
        self._fit_to_owner()

    def _L(self):
        return self._lang()

    def _step_text(self, step: int, total: int, action_key: str) -> str:
        L = self._L()
        action = t(action_key, L, step=step, total=total)
        return t("conf_step", L, step=step, total=total, action=action)

    def _set_status(self, step: int, total: int, action_key: str, target: QLabel | None = None):
        lbl = target or self.status_label
        lbl.setObjectName("hint")
        lbl.setText(self._step_text(step, total, action_key))
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def _on_progress(self, step: int, total: int, action_key: str):
        self._set_status(step, total, action_key)

    def _on_proxy_progress(self, step: int, total: int, action_key: str):
        self._set_status(step, total, action_key, self.proxy_status)

    def _load_vault(self):
        blob = load_account_blob(self._login, self._sessions_password)
        if not blob:
            return
        if blob.get("steam_password"):
            self.pass_edit.setText(blob["steam_password"])
        if blob.get("proxy"):
            self.proxy_edit.setText(blob["proxy"])
        self._cookies = blob.get("cookies") or {}

    def _save_vault(self, cookies: dict | None = None):
        save_account_blob(
            self._login,
            self._sessions_password,
            steam_password=self.pass_edit.text(),
            proxy=self.proxy_edit.text().strip(),
            cookies=cookies if cookies is not None else self._cookies,
        )
        if cookies is not None:
            self._cookies = cookies

    def _fit_to_owner(self):
        owner = self._owner
        w = owner.width() if owner is not None else 380
        self.resize(w, min(620, owner.height() - 40 if owner else 620))
        if owner is not None:
            self.move(owner.frameGeometry().topLeft() + QPoint(32, 48))

    def _safe_close(self):
        if self._closing:
            return
        self._closing = True
        self._stop_worker()
        if self.pass_edit.text().strip():
            self._save_vault()
        QTimer.singleShot(0, lambda: QDialog.done(self, int(QDialog.DialogCode.Rejected)))

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        event.ignore()
        self._safe_close()

    def _stop_worker(self):
        w = self._worker
        self._worker = None
        if w is None:
            return
        try:
            w.finished_ok.disconnect()
            w.finished_err.disconnect()
            w.progress.disconnect()
        except (TypeError, RuntimeError):
            pass
        if w.isRunning():
            w.wait(500)

    def _set_busy(self, busy: bool):
        self.open_btn.setEnabled(not busy)
        self.proxy_check_btn.setEnabled(not busy)
        self.confirm_all_btn.setEnabled(not busy and bool(self._confs))

    def _check_proxy(self):
        raw = self.proxy_edit.text().strip()
        if not raw:
            self.proxy_status.setObjectName("error")
            self.proxy_status.setText(t("conf_proxy_empty", self._L()))
            return
        self._stop_worker()
        self._set_busy(True)
        worker = _SyncWorker(parent=self)

        def job():
            def report(step, total, key):
                worker.progress.emit(step, total, key)

            return check_proxy(raw, report=report)

        worker._fn = job
        self._worker = worker
        worker.progress.connect(self._on_proxy_progress)
        worker.finished_ok.connect(self._on_proxy_ok)
        worker.finished_err.connect(self._on_proxy_err)
        worker.start()

    def _on_proxy_ok(self, result):
        self._worker = None
        self._set_busy(False)
        ok, msg = result
        if ok:
            self.proxy_status.setObjectName("ok")
            self.proxy_status.setText(t("conf_proxy_ok", self._L(), ip=msg))
        else:
            self.proxy_status.setObjectName("error")
            key = "conf_proxy_invalid" if msg == "invalid" else "conf_proxy_fail"
            self.proxy_status.setText(t(key, self._L(), err=msg))

    def _on_proxy_err(self, err: str):
        self._worker = None
        self._set_busy(False)
        self.proxy_status.setObjectName("error")
        self.proxy_status.setText(t("conf_proxy_fail", self._L(), err=err))

    def _open_confirmations(self):
        pwd = self.pass_edit.text()
        if not pwd:
            QMessageBox.warning(self, t("conf_title", self._L()), t("conf_need_password", self._L()))
            return
        self._set_busy(True)
        self._stop_worker()
        proxy = self.proxy_edit.text().strip()
        cookies = self._cookies or None
        mafile = self._mafile
        login = self._login
        worker = _AsyncWorker(parent=self)

        async def job():
            def report(step, total, key):
                worker.progress.emit(step, total, key)

            return await open_confirmations_flow(
                login, pwd, mafile, proxy or None, cookies, report
            )

        worker._coro_fn = job
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._on_fetched)
        worker.finished_err.connect(self._on_fetch_err)
        worker.start()

    def _on_fetched(self, result):
        self._worker = None
        self._set_busy(False)
        cookies, confs = result
        self._save_vault(cookies)
        self._confs = confs
        self._render_list()
        if confs:
            self.status_label.setObjectName("ok")
            self.status_label.setText(t("conf_count", self._L(), n=len(confs)))
            self.confirm_all_btn.setEnabled(True)
        else:
            self.status_label.setObjectName("hint")
            self.status_label.setText(t("conf_empty", self._L()))

    def _on_fetch_err(self, err: str):
        self._worker = None
        self._set_busy(False)
        self.status_label.setObjectName("error")
        self.status_label.setText(err)

    def _clear_list(self):
        while self.list_lay.count() > 1:
            item = self.list_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _render_list(self):
        self._clear_list()
        L = self._L()
        for conf in self._confs:
            row = QFrame()
            row.setObjectName("codeCard")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            text = conf.get("headline") or conf.get("type_name") or str(conf.get("id"))
            sub = conf.get("type_name") or ""
            lbl = QLabel("%s\n%s" % (text, sub) if sub and sub != text else text)
            lbl.setWordWrap(True)
            rl.addWidget(lbl, 1)
            allow_btn = QPushButton(t("conf_allow", L))
            allow_btn.setObjectName("primary")
            deny_btn = QPushButton(t("conf_deny", L))
            allow_btn.clicked.connect(lambda _=False, c=conf: self._confirm_one(c, "allow"))
            deny_btn.clicked.connect(lambda _=False, c=conf: self._confirm_one(c, "cancel"))
            rl.addWidget(allow_btn)
            rl.addWidget(deny_btn)
            self.list_lay.insertWidget(self.list_lay.count() - 1, row)

    def _confirm_one(self, conf: dict, op: str):
        self._set_busy(True)
        pwd = self.pass_edit.text()
        proxy = self.proxy_edit.text().strip()
        login = self._login
        mafile = self._mafile
        cookies = self._cookies or None
        worker = _AsyncWorker(parent=self)

        async def job():
            def report(step, total, key):
                worker.progress.emit(step, total, key)

            await confirm_one(login, pwd, mafile, proxy or None, cookies, conf, op, report)

        worker._coro_fn = job
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(lambda _: self._after_one(conf))
        worker.finished_err.connect(self._on_action_err)
        worker.start()

    def _after_one(self, conf: dict):
        self._worker = None
        self._confs = [c for c in self._confs if c.get("id") != conf.get("id")]
        self._render_list()
        self._set_busy(False)
        self.confirm_all_btn.setEnabled(bool(self._confs))
        if not self._confs:
            self.status_label.setText(t("conf_empty", self._L()))

    def _confirm_all(self):
        if not self._confs:
            return
        self._set_busy(True)
        pwd = self.pass_edit.text()
        proxy = self.proxy_edit.text().strip()
        confs = list(self._confs)
        login = self._login
        mafile = self._mafile
        cookies = self._cookies or None
        worker = _AsyncWorker(parent=self)

        async def job():
            def report(step, total, key):
                worker.progress.emit(step, total, key)

            await confirm_all(login, pwd, mafile, proxy or None, cookies, confs, report)

        worker._coro_fn = job
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._after_all)
        worker.finished_err.connect(self._on_action_err)
        worker.start()

    def _after_all(self):
        self._worker = None
        self._confs = []
        self._render_list()
        self._set_busy(False)
        self.confirm_all_btn.setEnabled(False)
        self.status_label.setText(t("conf_all_done", self._L()))

    def _on_action_err(self, err: str):
        self._worker = None
        self._set_busy(False)
        QMessageBox.warning(self, t("conf_title", self._L()), err)
