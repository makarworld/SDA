# -*- coding: utf-8 -*-
"""
SDA Codes — вертикальный GUI Steam Guard.
Frameless + кастомные кнопки, авто-обновление mafiles/, импорт (в т.ч. SDA encrypted).
"""
import os
import sys
import time

from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QGuiApplication, QIcon, QMouseEvent, QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core import (
    MAFILES_DIR,
    ROOT_DIR,
    account_label,
    ensure_mafiles_dir,
    find_mafiles_in_dir,
    folder_needs_password,
    generate_one_time_code,
    get_mafiles,
    import_mafile,
    is_encrypted_folder,
    open_mafiles,
    steam_id_from_data,
    verify_passkey,
)
from src.sessions_vault import (
    sessions_configured,
    set_sessions_password,
    verify_sessions_password,
)
from src.i18n import t
from src.settings import (
    get_pair_code,
    load_settings,
    proxy_url,
    save_settings,
    set_pair_code,
)
from src.telegram_bot import TelegramBotWorker, assign_slugs, verify_bot_token

ICON_PATH = os.path.join(ROOT_DIR, "icon.ico")

UI_FONT = '"Bahnschrift", "Segoe UI Variable", "Segoe UI", sans-serif'
CODE_FONT = '"Cascadia Code", "Cascadia Mono", "Consolas", monospace'

COLORS = {
    "bg": "#0E1621",
    "panel": "#1B2838",
    "panel_alt": "#16202D",
    "border": "#2A475E",
    "text": "#C7D5E0",
    "muted": "#8B9BB4",
    "accent": "#66C0F4",
    "code": "#A4D007",
    "warn": "#E05A46",
    "btn": "#2A475E",
    "btn_hover": "#3D6A8A",
    "scroll": "#3D6A8A",
    "scroll_hover": "#66C0F4",
}

STYLESHEET = f"""
QMainWindow, QWidget#central, QDialog#settingsDialog, QDialog#aboutDialog {{
    background: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: {UI_FONT};
    font-size: 13px;
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QFrame#titleBar {{
    background: {COLORS['panel']};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
QFrame#navBar {{
    background: {COLORS['panel_alt']};
    border-bottom: 1px solid {COLORS['border']};
}}
QPushButton#navBtn {{
    background: transparent;
    border: none;
    border-radius: 0;
    color: {COLORS['muted']};
    font-size: 12px;
    font-weight: 500;
    padding: 0 8px;
    min-height: 34px;
    max-height: 34px;
}}
QPushButton#navBtn:hover {{
    background: {COLORS['btn_hover']};
    color: {COLORS['text']};
    border: none;
}}
QPushButton#navBtn:pressed {{
    background: {COLORS['border']};
    border: none;
}}
QMenu {{
    background: {COLORS['panel']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 18px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {COLORS['btn_hover']};
}}
QMenu::item:disabled {{
    color: {COLORS['accent']};
}}
QLabel#winTitle {{
    color: {COLORS['accent']};
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#winBtn, QPushButton#winClose {{
    background: transparent;
    border: none;
    color: {COLORS['muted']};
    padding: 0;
    border-radius: 4px;
    min-width: 40px;
    max-width: 40px;
    min-height: 30px;
    max-height: 30px;
}}
QPushButton#winBtn:hover {{
    background: {COLORS['btn_hover']};
    color: {COLORS['text']};
}}
QPushButton#winClose:hover {{
    background: {COLORS['warn']};
    color: #FFFFFF;
}}
QLabel#accountName {{
    color: {COLORS['text']};
    font-size: 16px;
    font-weight: 600;
}}
QPushButton#onlineBtn {{
    background: rgba(102, 192, 244, 0.10);
    color: {COLORS['accent']};
    border: 1px solid rgba(102, 192, 244, 0.45);
    border-radius: 11px;
    padding: 3px 11px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
    min-height: 22px;
    max-height: 22px;
}}
QPushButton#onlineBtn:hover {{
    background: {COLORS['accent']};
    color: #0E1621;
    border: 1px solid {COLORS['accent']};
}}
QPushButton#onlineBtn:disabled {{
    background: transparent;
    color: {COLORS['muted']};
    border: 1px solid {COLORS['border']};
}}
QLabel#codeLabel {{
    color: {COLORS['code']};
    font-family: {CODE_FONT};
    font-size: 48px;
    font-weight: 700;
    letter-spacing: 8px;
    padding: 4px 0;
}}
QLabel#pairCode {{
    color: {COLORS['accent']};
    font-family: {CODE_FONT};
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 12px;
}}
QLabel#hint {{
    color: {COLORS['muted']};
    font-size: 11px;
}}
QLabel#error {{
    color: {COLORS['warn']};
    font-size: 11px;
}}
QLabel#ok {{
    color: {COLORS['accent']};
    font-size: 11px;
}}
QLabel#toast {{
    color: {COLORS['accent']};
    font-size: 12px;
    font-weight: 500;
}}
QLabel#section {{
    color: {COLORS['muted']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}}
QComboBox {{
    background: {COLORS['panel']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-family: {UI_FONT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['panel']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    outline: none;
    padding: 0;
    selection-background-color: {COLORS['border']};
    selection-color: {COLORS['accent']};
}}
QComboBox QListView {{
    background: {COLORS['panel']};
    border: none;
    outline: none;
    padding: 0;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 24px;
    background: {COLORS['panel']};
    color: {COLORS['text']};
}}
QComboBox QAbstractItemView::item:selected {{
    background: {COLORS['border']};
    color: {COLORS['accent']};
}}
QListWidget {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    color: {COLORS['text']};
    padding: 10px 12px;
    margin: 2px 4px;
    border-radius: 6px;
}}
QListWidget::item:hover {{
    background: {COLORS['panel_alt']};
}}
QListWidget::item:selected {{
    background: {COLORS['border']};
    color: {COLORS['accent']};
}}
QScrollBar:vertical {{
    background: {COLORS['panel_alt']};
    width: 10px;
    margin: 4px 2px 4px 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['scroll']};
    min-height: 28px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['scroll_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
}}
QProgressBar {{
    border: none;
    background: {COLORS['panel_alt']};
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
}}
QProgressBar::chunk {{
    background: {COLORS['accent']};
    border-radius: 3px;
}}
QPushButton {{
    background: {COLORS['btn']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 10px 14px;
    font-weight: 500;
    min-height: 20px;
}}
QPushButton:hover {{
    background: {COLORS['btn_hover']};
    border-color: {COLORS['accent']};
}}
QPushButton:pressed {{
    background: {COLORS['border']};
}}
QPushButton#primary {{
    background: {COLORS['accent']};
    color: #0E1621;
    border: none;
    font-weight: 600;
    padding: 10px 14px;
}}
QPushButton#primary:hover {{
    background: #8ED3F8;
}}
QFrame#codeCard {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QLineEdit {{
    background: {COLORS['panel']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 10px;
    font-family: {UI_FONT};
}}
QDialog {{
    background: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: {UI_FONT};
}}
QDialog QLabel {{
    color: {COLORS['text']};
}}
"""


def lang() -> str:
    return load_settings().get("language") or "ru"


class WinIconButton(QPushButton):
    """Кнопки окна с нарисованными иконками (не битые unicode)."""

    MINIMIZE = "min"
    MAXIMIZE = "max"
    RESTORE = "restore"
    CLOSE = "close"

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setObjectName("winClose" if kind == self.CLOSE else "winBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 30)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#FFFFFF" if self.underMouse() and self.kind == self.CLOSE else COLORS["muted"])
        if self.underMouse() and self.kind != self.CLOSE:
            color = QColor(COLORS["text"])
        pen = QPen(color, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        cx, cy = self.width() / 2, self.height() / 2
        if self.kind == self.MINIMIZE:
            p.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))
        elif self.kind == self.MAXIMIZE:
            p.drawRect(int(cx - 5), int(cy - 5), 10, 10)
        elif self.kind == self.RESTORE:
            p.drawRect(int(cx - 3), int(cy - 6), 8, 8)
            p.drawRect(int(cx - 6), int(cy - 3), 8, 8)
        elif self.kind == self.CLOSE:
            p.drawLine(int(cx - 4), int(cy - 4), int(cx + 4), int(cy + 4))
            p.drawLine(int(cx + 4), int(cy - 4), int(cx - 4), int(cy + 4))
        p.end()


class TitleBar(QFrame):
    def __init__(
        self,
        window,
        title: str = "SDA Codes",
        show_max: bool = True,
        show_min: bool = True,
        on_close=None,
    ):
        super().__init__()
        self._window = window
        self._drag_pos: QPoint | None = None
        self.setObjectName("titleBar")
        self.setFixedHeight(40)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 6, 0)
        lay.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("winTitle")
        lay.addWidget(self.title_lbl)
        lay.addStretch(1)

        self.min_btn = None
        if show_min:
            self.min_btn = WinIconButton(WinIconButton.MINIMIZE)
            self.min_btn.clicked.connect(window.showMinimized)
            lay.addWidget(self.min_btn)

        self.max_btn = None
        if show_max:
            self.max_btn = WinIconButton(WinIconButton.MAXIMIZE)
            self.max_btn.clicked.connect(self._toggle_max)
            lay.addWidget(self.max_btn)

        self.close_btn = WinIconButton(WinIconButton.CLOSE)
        if on_close is not None:
            self.close_btn.clicked.connect(on_close)
        elif isinstance(window, QDialog):
            self.close_btn.clicked.connect(window.reject)
        else:
            self.close_btn.clicked.connect(window.close)
        lay.addWidget(self.close_btn)

    def retranslate(self, title: str):
        self.title_lbl.setText(title)
        if self.min_btn is not None:
            self.min_btn.setToolTip(t("minimize", lang()))
        self.close_btn.setToolTip(t("close", lang()))
        if self.max_btn is not None:
            tip = t("restore", lang()) if self._window.isMaximized() else t("maximize", lang())
            self.max_btn.setToolTip(tip)

    def _toggle_max(self):
        if self.max_btn is None:
            return
        if self._window.isMaximized():
            self._window.showNormal()
            self.max_btn.kind = WinIconButton.MAXIMIZE
            self.max_btn.setToolTip(t("maximize", lang()))
        else:
            self._window.showMaximized()
            self.max_btn.kind = WinIconButton.RESTORE
            self.max_btn.setToolTip(t("restore", lang()))
        self.max_btn.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._window.isMaximized():
                return
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.max_btn is not None:
            self._toggle_max()
            event.accept()


class NavBar(QFrame):
    """Полоска под title bar: Настройки · Справка · Язык."""

    def __init__(self, on_settings, on_about, on_language, parent=None):
        super().__init__(parent)
        self._on_language = on_language
        self.setObjectName("navBar")
        self.setFixedHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.settings_btn = QPushButton(t("settings", lang()))
        self.about_btn = QPushButton(t("about", lang()))
        self.lang_btn = QPushButton(t("language", lang()))
        for btn, slot in (
            (self.settings_btn, on_settings),
            (self.about_btn, on_about),
            (self.lang_btn, None),
        ):
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if slot is not None:
                btn.clicked.connect(slot)
            lay.addWidget(btn, 1)

        self.lang_btn.clicked.connect(self._pick_language)
        self._rebuild_lang_menu()

    def _rebuild_lang_menu(self):
        menu = QMenu(self)
        cur = lang()
        for code, label in (("ru", "🇷🇺  Русский"), ("en", "🇬🇧  English")):
            act = menu.addAction(label)
            act.setEnabled(code != cur)
            act.triggered.connect(lambda _=False, c=code: self._on_language(c))
        self._lang_menu = menu

    def _pick_language(self):
        self._rebuild_lang_menu()
        pos = self.lang_btn.mapToGlobal(self.lang_btn.rect().bottomLeft())
        self._lang_menu.exec(pos)

    def retranslate(self):
        L = lang()
        self.settings_btn.setText(t("settings", L))
        self.about_btn.setText(t("about", L))
        self.lang_btn.setText(t("language", L))
        self._rebuild_lang_menu()



def mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 4:
        return token
    return ("*" * (len(token) - 4)) + token[-4:]


def looks_like_masked_token(text: str, real: str) -> bool:
    return bool(real) and text == mask_token(real)


def _wl_text(wl: list) -> str:
    if not wl:
        return t("whitelist_empty", lang())
    return t("whitelist_label", lang(), ids=", ".join(map(str, wl)))


class TokenCheckWorker(QThread):
    finished_ok = pyqtSignal(str)
    finished_err = pyqtSignal(str)

    def __init__(self, token: str, proxy: str | None, parent=None):
        super().__init__(parent)
        self.token = token
        self.proxy = proxy

    def run(self):
        ok, info = verify_bot_token(self.token, self.proxy)
        if ok:
            self.finished_ok.emit(info)
        else:
            self.finished_err.emit(info)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        # без Qt-parent — закрытие не гасит MainWindow
        super().__init__(None)
        self.setObjectName("aboutDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setMinimumWidth(360)
        if os.path.isfile(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(
            TitleBar(
                self,
                title=t("about_title", lang()),
                show_max=False,
                show_min=False,
                on_close=self.reject,
            )
        )

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        label = QLabel(t("about_text", lang()))
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(label)
        ok = QPushButton("OK")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        lay.addWidget(ok)
        root.addWidget(body)
        self.adjustSize()
        if parent is not None:
            # смещение — иначе X совпадает с X главного окна (click-through)
            self.move(parent.frameGeometry().topLeft() + QPoint(56, 56))


class SettingsDialog(QDialog):
    def __init__(self, owner=None):
        # без Qt-parent: на Windows дочерний Window.close() закрывал всё приложение
        super().__init__(None)
        self._owner = owner
        self.setObjectName("settingsDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setMinimumWidth(320)
        if os.path.isfile(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self._data = load_settings()
        self._token_real = (self._data.get("bot_token") or "").strip()
        self._check_worker: TokenCheckWorker | None = None
        self._save_pending = False
        self._closing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar(
            self,
            title=t("settings_title", lang()),
            show_max=False,
            show_min=False,
            on_close=self._safe_close,
        )
        root.addWidget(self.title_bar)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        form = QFormLayout()
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText(t("token_placeholder", lang()))
        if self._token_real:
            self.token_edit.setText(mask_token(self._token_real))
        self.token_edit.editingFinished.connect(self._check_token_async)
        form.addRow("BOT_TOKEN", self.token_edit)

        proxy_row = QHBoxLayout()
        self.proxy_type = QComboBox()
        self._fill_proxy_types()
        view = self.proxy_type.view()
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setAutoFillBackground(True)
        pal = view.palette()
        pal.setColor(view.backgroundRole(), QColor(COLORS["panel"]))
        view.setPalette(pal)
        cur_type = (self._data.get("proxy_type") or "").strip().lower()
        if cur_type in ("mtproxy", "mtproto"):
            cur_type = ""
        idx = max(0, self.proxy_type.findData(cur_type))
        self.proxy_type.setCurrentIndex(idx)
        self.proxy_type.currentIndexChanged.connect(self._on_proxy_changed)
        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText(t("proxy_placeholder", lang()))
        self.proxy_edit.setText((self._data.get("proxy") or "").strip())
        self.proxy_edit.editingFinished.connect(self._check_token_async)
        proxy_row.addWidget(self.proxy_type)
        proxy_row.addWidget(self.proxy_edit, 1)
        self.proxy_label = QLabel(t("proxy", lang()))
        form.addRow(self.proxy_label, proxy_row)
        lay.addLayout(form)

        self.help_lbl = QLabel(t("settings_help", lang()))
        self.help_lbl.setObjectName("hint")
        self.help_lbl.setWordWrap(True)
        lay.addWidget(self.help_lbl)

        self.sessions_section = QLabel(t("sessions_pwd_section", lang()))
        self.sessions_section.setObjectName("section")
        lay.addWidget(self.sessions_section)

        self.sessions_pwd_edit = QLineEdit()
        self.sessions_pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.sessions_pwd_edit.setPlaceholderText(t("sessions_pwd_placeholder", lang()))
        lay.addWidget(self.sessions_pwd_edit)

        self.sessions_help = QLabel(t("sessions_pwd_help", lang()))
        self.sessions_help.setObjectName("hint")
        self.sessions_help.setWordWrap(True)
        lay.addWidget(self.sessions_help)

        self.conn_label = QLabel("")
        self.conn_label.setObjectName("hint")
        self.conn_label.setWordWrap(True)
        lay.addWidget(self.conn_label)
        self._on_proxy_changed()

        self.pair_section = QLabel(t("pair_section", lang()))
        self.pair_section.setObjectName("section")
        lay.addWidget(self.pair_section)

        self.pair_label = QLabel(get_pair_code())
        self.pair_label.setObjectName("pairCode")
        self.pair_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pair_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.pair_label)

        pair_btns = QHBoxLayout()
        self.copy_btn = QPushButton(t("copy", lang()))
        self.copy_btn.setObjectName("primary")
        self.copy_btn.clicked.connect(self._copy_pair)
        self.regen_btn = QPushButton(t("pair_new", lang()))
        self.regen_btn.clicked.connect(self._regen_pair)
        pair_btns.addWidget(self.copy_btn, 1)
        pair_btns.addWidget(self.regen_btn)
        lay.addLayout(pair_btns)

        self.hint = QLabel(t("pair_hint", lang()))
        self.hint.setObjectName("hint")
        self.hint.setWordWrap(True)
        lay.addWidget(self.hint)

        self.wl_label = QLabel(_wl_text(self._data.get("whitelist") or []))
        self.wl_label.setObjectName("hint")
        self.wl_label.setWordWrap(True)
        lay.addWidget(self.wl_label)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 8, 0, 0)
        self.save_btn = QPushButton(t("save", lang()))
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self._save)
        self.close_btn = QPushButton(t("close", lang()))
        self.close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.save_btn, 1)
        buttons.addWidget(self.close_btn)
        lay.addLayout(buttons)

        root.addWidget(body)
        self.title_bar.retranslate(t("settings_title", lang()))
        self._fit_to_owner()

    def _safe_close(self):
        """Закрыть настройки. Отложенно — иначе mouse release попадает в X главного окна."""
        if self._closing:
            return
        self._closing = True
        # ponytail: click-through при совпадении координат X с MainWindow
        QTimer.singleShot(0, lambda: self._finish_close(False))

    def reject(self):
        self._safe_close()

    def accept(self):
        if self._closing:
            return
        self._closing = True
        QTimer.singleShot(0, lambda: self._finish_close(True))

    def _finish_close(self, saved: bool):
        self._stop_check()
        code = int(QDialog.DialogCode.Accepted if saved else QDialog.DialogCode.Rejected)
        QDialog.done(self, code)

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        event.ignore()
        self._safe_close()

    def _fit_to_owner(self):
        owner = self._owner
        w = owner.width() if owner is not None else 380
        h = max(self.sizeHint().height(), 1)
        self.resize(w, h)
        if owner is not None:
            # смещение вправо-вниз, чтобы крестики окон не совпадали
            self.move(owner.frameGeometry().topLeft() + QPoint(56, 56))

    def _fill_proxy_types(self):
        self.proxy_type.clear()
        L = lang()
        for key, label_key in (("", "proxy_none"), ("http", "proxy_http"), ("socks5", "proxy_socks")):
            self.proxy_type.addItem(t(label_key, L), key)

    def showEvent(self, event):
        super().showEvent(event)
        fresh = load_settings()
        self._data = fresh
        self._token_real = (fresh.get("bot_token") or "").strip()
        self.pair_label.setText(get_pair_code())
        self.wl_label.setText(_wl_text(fresh.get("whitelist") or []))
        self._fit_to_owner()
        if self._token_real:
            QTimer.singleShot(0, self._check_token_async)

    def _copy_pair(self):
        QGuiApplication.clipboard().setText(self.pair_label.text().strip().upper())

    def _regen_pair(self):
        self.pair_label.setText(set_pair_code())

    def _on_proxy_changed(self):
        self.proxy_edit.setEnabled(bool(self.proxy_type.currentData()))

    def _resolve_token(self) -> str:
        typed = self.token_edit.text().strip()
        if looks_like_masked_token(typed, self._token_real):
            return self._token_real
        return typed

    def _proxy_settings(self) -> dict:
        return {
            "proxy_type": self.proxy_type.currentData() or "",
            "proxy": self.proxy_edit.text().strip(),
        }

    def _set_conn(self, text: str, kind: str = "hint"):
        self.conn_label.setText(text)
        self.conn_label.setObjectName(kind)
        self.conn_label.style().unpolish(self.conn_label)
        self.conn_label.style().polish(self.conn_label)

    def _stop_check(self):
        worker = self._check_worker
        self._check_worker = None
        if worker is None:
            return
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            if worker.isRunning():
                worker.wait(300)
        except RuntimeError:
            pass

    def _check_token_async(self):
        token = self._resolve_token()
        if not token:
            self._set_conn("")
            return
        self._set_conn(t("checking", lang()), "hint")
        self._stop_check()
        worker = TokenCheckWorker(token, proxy_url(self._proxy_settings()), self)
        self._check_worker = worker
        worker.finished_ok.connect(self._on_check_ok)
        worker.finished_err.connect(self._on_check_err)
        worker.finished.connect(self._on_check_finished)
        worker.start()

    def _on_check_finished(self):
        self._check_worker = None

    def _on_check_ok(self, username: str):
        self._check_worker = None
        if self._closing:
            return
        self._set_conn(t("bot_connected", lang(), user=username), "ok")
        if self._save_pending:
            self._save_pending = False
            self._do_save()

    def _on_check_err(self, err: str):
        self._check_worker = None
        if self._closing:
            return
        self._set_conn(t("bot_error", lang(), err=err), "error")
        if self._save_pending:
            self._save_pending = False
            self.save_btn.setEnabled(True)
            self.close_btn.setEnabled(True)
            QMessageBox.warning(self, "BOT_TOKEN", t("token_bad", lang(), err=err))

    def _save(self):
        token = self._resolve_token()
        if token:
            self._save_pending = True
            self.save_btn.setEnabled(False)
            self.close_btn.setEnabled(False)
            self._check_token_async()
            return
        self._do_save()

    def _do_save(self):
        token = self._resolve_token()
        px = self._proxy_settings()
        fresh = load_settings()
        fresh["bot_token"] = token
        fresh["proxy_type"] = px["proxy_type"]
        fresh["proxy"] = px["proxy"]
        sessions_pwd = self.sessions_pwd_edit.text()
        if sessions_pwd:
            set_sessions_password(sessions_pwd, fresh)
            fresh = load_settings()
            if self._owner is not None:
                self._owner.sessions_password = sessions_pwd
        set_pair_code(self.pair_label.text().strip().upper())
        # whitelist / pair_code не пишем в файл
        save_settings(fresh)
        self.save_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title", lang()))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        if os.path.isfile(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(380, 640)
        self.setMinimumSize(320, 520)

        self.mafiles = []
        self.mafiles_dict = {}
        self.current_file = None
        self.passkey: str | None = None
        self.sessions_password: str | None = None
        self._toast_until = 0
        self._bucket = None
        self._folder_sig = None
        self._bot: TelegramBotWorker | None = None
        self._ignore_close_until = 0.0
        self.bot_accounts: list = []

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar(
            self,
            title=t("app_title", lang()),
            show_max=True,
        )
        root.addWidget(self.title_bar)

        self.nav_bar = NavBar(
            on_settings=self._show_settings,
            on_about=self._show_about,
            on_language=self._set_language,
        )
        root.addWidget(self.nav_bar)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 16, 16, 16)
        body_lay.setSpacing(12)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(10)
        head.addStretch(1)
        self.account_name = QLabel(t("select_account", lang()))
        self.account_name.setObjectName("accountName")
        self.account_name.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        head.addWidget(self.account_name, 0, Qt.AlignmentFlag.AlignVCenter)
        self.online_btn = QPushButton(t("online", lang()))
        self.online_btn.setObjectName("onlineBtn")
        self.online_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.online_btn.setEnabled(False)
        self.online_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.online_btn.clicked.connect(self._show_online)
        head.addWidget(self.online_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addStretch(1)
        body_lay.addLayout(head)

        card = QFrame()
        card.setObjectName("codeCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 22, 20, 18)
        card_lay.setSpacing(10)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.code_label = QLabel("-----")
        self.code_label.setObjectName("codeLabel")
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.code_label.mousePressEvent = self._copy_code  # type: ignore[method-assign]
        card_lay.addWidget(self.code_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 30000)
        self.progress.setValue(30000)
        self.progress.setTextVisible(False)
        card_lay.addWidget(self.progress)

        self.hint = QLabel(t("code_hint", lang()))
        self.hint.setObjectName("hint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        card_lay.addWidget(self.hint)

        self.toast = QLabel("")
        self.toast.setObjectName("toast")
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.setFixedHeight(16)
        card_lay.addWidget(self.toast)
        body_lay.addWidget(card)

        # равный зазор: код ↔ копировать ↔ аккаунты
        body_lay.addSpacing(10)
        self.copy_btn = QPushButton(t("copy", lang()))
        self.copy_btn.setObjectName("primary")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_code)
        body_lay.addWidget(self.copy_btn)
        body_lay.addSpacing(10)

        self.section = QLabel(t("accounts", lang()))
        self.section.setObjectName("section")
        body_lay.addWidget(self.section)

        self.list = QListWidget()
        self.list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list.currentItemChanged.connect(self._on_select)
        body_lay.addWidget(self.list, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.add_btn = QPushButton(t("add_mafile", lang()))
        self.add_btn.clicked.connect(self._import_mafile)
        bottom.addWidget(self.add_btn, 1)
        body_lay.addLayout(bottom)

        self.bot_status = QLabel("")
        self.bot_status.setObjectName("hint")
        body_lay.addWidget(self.bot_status)

        root.addWidget(body, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

        self.watch_timer = QTimer(self)
        self.watch_timer.timeout.connect(self._watch_folder)
        self.watch_timer.start(1000)

        ensure_mafiles_dir()
        self._ensure_passkey()
        self.reload_accounts(quiet=True)
        self._tick()
        self.title_bar.retranslate(t("app_title", lang()))
        # бот — после show(), не блокирует старт
        QTimer.singleShot(0, self._restart_bot)

    def _set_language(self, code: str):
        if code == lang():
            return
        s = load_settings()
        s["language"] = code
        save_settings(s)
        self._retranslate_ui()
        # бот читает язык на лету; полный рестарт не нужен (меню обновится при след. подключении)

    def _retranslate_ui(self):
        L = lang()
        self.setWindowTitle(t("app_title", L))
        self.title_bar.retranslate(t("app_title", L))
        self.nav_bar.retranslate()
        if not self.current_file:
            self.account_name.setText(t("select_account", L) if self.mafiles else t("no_mafile", L))
        self.hint.setText(t("code_hint", L))
        self.copy_btn.setText(t("copy", L))
        self.section.setText(t("accounts", L))
        self.add_btn.setText(t("add_mafile", L))
        self.online_btn.setText(t("online", L))
        if not (load_settings().get("bot_token") or "").strip():
            self.bot_status.setText(t("bot_offline", L))

    def _folder_signature(self):
        ensure_mafiles_dir()
        items = []
        for name in os.listdir(MAFILES_DIR):
            path = os.path.join(MAFILES_DIR, name)
            if not os.path.isfile(path):
                continue
            if not (name.endswith(".maFile") or name == "manifest.json"):
                continue
            try:
                items.append((name, os.path.getmtime(path), os.path.getsize(path)))
            except OSError:
                continue
        return tuple(sorted(items))

    def _watch_folder(self):
        sig = self._folder_signature()
        if sig != self._folder_sig:
            self._folder_sig = sig
            self.reload_accounts(quiet=True)

    def _ask_password(self, title_key="enc_title") -> str | None:
        L = lang()
        text, ok = QInputDialog.getText(
            self,
            t(title_key, L),
            t("enc_prompt", L),
            QLineEdit.EchoMode.Password,
        )
        if not ok or not text:
            return None
        return text

    def _ensure_passkey(self) -> bool:
        if not folder_needs_password():
            return True
        if self.passkey and (not is_encrypted_folder() or verify_passkey(self.passkey)):
            return True
        pwd = self._ask_password()
        if not pwd:
            QMessageBox.warning(self, t("enc_warn_title", lang()), t("enc_warn_body", lang()))
            return False
        if is_encrypted_folder() and not verify_passkey(pwd):
            QMessageBox.warning(self, t("enc_warn_title", lang()), t("enc_bad", lang()))
            return False
        self.passkey = pwd
        return True

    def reload_accounts(self, quiet: bool = False):
        prev = self.current_file
        self.list.clear()
        self._folder_sig = self._folder_signature()
        L = lang()

        names = get_mafiles()
        if not names:
            old_slugs = [a.get("slug") for a in self.bot_accounts]
            self.mafiles = []
            self.mafiles_dict = {}
            self.current_file = None
            self.account_name.setText(t("no_mafile", L))
            self.code_label.setText("-----")
            self.copy_btn.setEnabled(False)
            self.online_btn.setEnabled(False)
            self._refresh_bot_accounts()
            if self._bot and old_slugs != [a.get("slug") for a in self.bot_accounts]:
                self._restart_bot()
            return

        if folder_needs_password() and not self.passkey:
            if not quiet:
                self._ensure_passkey()
            if not self.passkey:
                self.mafiles = []
                self.mafiles_dict = {}
                return

        try:
            data = open_mafiles(names, password=self.passkey)
        except ValueError as e:
            if "парол" in str(e).lower() or "Неверный" in str(e):
                self.passkey = None
                if not quiet and self._ensure_passkey():
                    return self.reload_accounts(quiet=quiet)
            if not quiet:
                QMessageBox.warning(self, "mafiles", str(e))
            self.mafiles = []
            self.mafiles_dict = {}
            return

        self.mafiles = names
        self.mafiles_dict = data

        # дедуп по (login, steamid) — только UI, файлы на диске не трогаем
        seen: set[tuple] = set()
        unique_names = []
        unique_data = {}
        for name in names:
            row = data.get(name) or {}
            login = (row.get("account_name") or account_label(name, row)).lower().strip()
            sid = steam_id_from_data(row) or 0
            key = (login, sid)
            if key in seen:
                continue
            seen.add(key)
            unique_names.append(name)
            unique_data[name] = row
        self.mafiles = unique_names
        self.mafiles_dict = unique_data

        select_row = 0
        for i, name in enumerate(self.mafiles):
            label = account_label(name, self.mafiles_dict[name])
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.list.addItem(item)
            if name == prev:
                select_row = i

        if self.mafiles:
            self.list.setCurrentRow(select_row)

        old_slugs = [a.get("slug") for a in self.bot_accounts]
        self._refresh_bot_accounts()
        if self._bot and old_slugs != [a.get("slug") for a in self.bot_accounts]:
            self._restart_bot()

    def _import_mafile(self):
        L = lang()
        box = QMessageBox(self)
        box.setWindowTitle(t("import_title", L))
        box.setText(t("import_pick", L))
        files_btn = box.addButton(t("import_files", L), QMessageBox.ButtonRole.AcceptRole)
        folder_btn = box.addButton(t("import_folder", L), QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked == files_btn:
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                t("import_title", L),
                "",
                "maFile (*.maFile);;All files (*.*)",
            )
        elif clicked == folder_btn:
            folder = QFileDialog.getExistingDirectory(self, t("import_folder_title", L))
            paths = find_mafiles_in_dir(folder) if folder else []
            if folder and not paths:
                QMessageBox.warning(self, t("import_title", L), t("import_empty", L))
                return
        else:
            return
        if not paths:
            return
        self._import_paths(paths)

    def _import_paths(self, paths: list):
        L = lang()
        import_password = None
        vault_password = self.passkey
        ok_names = []
        errors = []

        def _need_pwd(msg: str) -> bool:
            return any(
                x in msg.lower()
                for x in ("зашифрован", "парол", "passkey", "salt", "manifest", "нужен")
            )

        def _ensure_passwords() -> bool:
            nonlocal import_password, vault_password
            if import_password is None:
                import_password = self._ask_password("enc_import_src")
                if not import_password:
                    return False
            if is_encrypted_folder() and not vault_password:
                vault_password = self._ask_password("enc_import_vault")
                if not vault_password:
                    return False
                if not verify_passkey(vault_password):
                    QMessageBox.warning(self, t("import_title", L), t("enc_vault_bad", L))
                    return False
            elif not vault_password:
                vault_password = import_password
            self.passkey = vault_password
            return True

        for path in paths:
            try:
                dest = import_mafile(path, import_password=import_password, vault_password=vault_password)
                ok_names.append(dest)
                continue
            except ValueError as e:
                msg = str(e)
                if not _need_pwd(msg):
                    errors.append("%s: %s" % (os.path.basename(path), msg))
                    continue
                if not _ensure_passwords():
                    return
                try:
                    dest = import_mafile(
                        path,
                        import_password=import_password,
                        vault_password=vault_password,
                    )
                    ok_names.append(dest)
                except Exception as e2:
                    errors.append("%s: %s" % (os.path.basename(path), e2))
            except Exception as e:
                errors.append("%s: %s" % (os.path.basename(path), e))

        if ok_names:
            if len(ok_names) == 1:
                self.toast.setText(t("import_ok", L, name=ok_names[0]))
            else:
                self.toast.setText(t("import_ok_many", L, n=len(ok_names)))
            self._toast_until = time.time() + 3.0
            self.reload_accounts(quiet=True)
        if errors:
            QMessageBox.warning(
                self,
                t("import_title", L),
                "\n".join(errors[:12]) + ("\n…" if len(errors) > 12 else ""),
            )

    def _show_about(self):
        AboutDialog(self).exec()

    def _show_settings(self):
        dlg = SettingsDialog(self)
        result = dlg.exec()
        # click-through: release после закрытия настроек не должен нажать наш X
        self._ignore_close_until = time.time() + 0.35
        if result == QDialog.DialogCode.Accepted:
            self._restart_bot()

    def closeEvent(self, event):
        if time.time() < self._ignore_close_until:
            event.ignore()
            return
        if self._bot is not None:
            self._bot.stop()
            if not self._bot.wait(800):
                self._bot.terminate()
                self._bot.wait(200)
            self._bot = None
        super().closeEvent(event)

    def _refresh_bot_accounts(self):
        rows = []
        for name in self.mafiles:
            data = self.mafiles_dict.get(name) or {}
            secret = data.get("shared_secret")
            if not secret:
                continue
            rows.append({
                "name": name,
                "label": account_label(name, data),
                "secret": secret,
            })
        self.bot_accounts = assign_slugs(rows)

    def _restart_bot(self):
        old = self._bot
        self._bot = None
        if old is not None:
            try:
                old.status.disconnect()
                old.stopped.disconnect()
            except TypeError:
                pass
            old.stop()
            if not old.wait(800):
                old.terminate()
                old.wait(200)

        s = load_settings()
        token = (s.get("bot_token") or "").strip()
        if not token:
            self.bot_status.setText(t("bot_offline", lang()))
            return

        # без синхронного verify — окно не блокируется
        self.bot_status.setText(t("bot_connecting", lang()))
        self._refresh_bot_accounts()
        self._bot = TelegramBotWorker(token, self.accounts_for_bot, self, proxy=proxy_url(s))
        self._bot.status.connect(self.bot_status.setText)
        self._bot.start()

    def accounts_for_bot(self) -> list:
        return list(self.bot_accounts)

    def _on_select(self, current: QListWidgetItem, _previous):
        if current is None:
            self.current_file = None
            self.account_name.setText(t("select_account", lang()))
            self.code_label.setText("-----")
            self.copy_btn.setEnabled(False)
            self.online_btn.setEnabled(False)
            return
        self.current_file = current.data(Qt.ItemDataRole.UserRole)
        self.account_name.setText(current.text())
        self.copy_btn.setEnabled(True)
        self.online_btn.setEnabled(True)
        self._refresh_code()

    def _ensure_sessions_password(self) -> bool:
        if self.sessions_password and verify_sessions_password(self.sessions_password):
            return True
        L = lang()
        text, ok = QInputDialog.getText(
            self,
            t("sessions_pwd_title", L),
            t("sessions_pwd_prompt", L),
            QLineEdit.EchoMode.Password,
        )
        if not ok or not text:
            return False
        if not verify_sessions_password(text):
            QMessageBox.warning(self, t("sessions_pwd_title", L), t("sessions_pwd_bad", L))
            return False
        self.sessions_password = text
        return True

    def _show_online(self):
        if not self.current_file:
            return
        L = lang()
        if not sessions_configured():
            QMessageBox.warning(self, t("online", L), t("sessions_pwd_required", L))
            return
        if not self._ensure_sessions_password():
            return
        data = self.mafiles_dict.get(self.current_file) or {}
        login = data.get("account_name") or account_label(self.current_file, data)
        if not data.get("shared_secret") or not data.get("identity_secret"):
            QMessageBox.warning(self, t("online", L), t("conf_no_secrets", L))
            return
        from src.confirmations_dialog import ConfirmationsDialog

        dlg = ConfirmationsDialog(
            self,
            login,
            data,
            self.current_file,
            self.sessions_password,
            ICON_PATH,
        )
        dlg.exec()
        self._ignore_close_until = time.time() + 0.35

    def _refresh_code(self):
        if not self.current_file:
            self._refresh_bot_accounts()
            return
        data = self.mafiles_dict.get(self.current_file)
        if not data or "shared_secret" not in data:
            self.code_label.setText("ERR")
            return
        self.code_label.setText(generate_one_time_code(data["shared_secret"]))
        self._refresh_bot_accounts()

    def _tick(self):
        now = time.time()
        self.progress.setValue(int((30.0 - (now % 30.0)) * 1000))
        if self.current_file:
            now_bucket = int(now) // 30
            if self._bucket != now_bucket:
                self._bucket = now_bucket
                self._refresh_code()
        else:
            self._refresh_bot_accounts()
        if now > self._toast_until and self.toast.text():
            self.toast.setText("")

    def _copy_code(self, _event=None):
        code = self.code_label.text().strip()
        if not code or code in ("-----", "ERR") or not self.current_file:
            return
        QGuiApplication.clipboard().setText(code)
        self.toast.setText(t("copied", lang()))
        self._toast_until = time.time() + 2.0


def main():
    set_pair_code()  # новый код на сессию, не в settings.json

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Bahnschrift", 10))
    app.setStyleSheet(STYLESHEET)
    if os.path.isfile(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
