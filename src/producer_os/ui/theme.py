from __future__ import annotations

from typing import Any, cast

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

try:
    import qdarktheme  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional runtime dependency
    qdarktheme = None  # type: ignore[assignment]


ThemeName = str


def _dark_tokens() -> dict[str, str]:
    return {
        "bg": "#090d14",
        "panel": "#101722",
        "panel_alt": "#151e2b",
        "elevated": "#1b2635",
        "text_primary": "#eff6ff",
        "text_secondary": "#cbd5e1",
        "text_muted": "#8fa3b8",
        "accent": "#41c5ff",
        "accent_hover": "#68d3ff",
        "accent_active": "#22b2f6",
        "success": "#31d0aa",
        "warning": "#f59e42",
        "danger": "#fb7185",
        "border": "#2a3646",
        "border_strong": "#3a4a60",
        "input_bg": "#0d141e",
        "selection_bg": "rgba(65, 197, 255, 0.18)",
        "shadow": "rgba(0,0,0,0.35)",
    }


def _light_tokens() -> dict[str, str]:
    return {
        "bg": "#eef2f7",
        "panel": "#ffffff",
        "panel_alt": "#f8fafc",
        "elevated": "#ffffff",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "accent": "#0ea5e9",
        "accent_hover": "#0284c7",
        "accent_active": "#0369a1",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "border": "#d7dee8",
        "border_strong": "#c3cfdb",
        "input_bg": "#ffffff",
        "selection_bg": "rgba(14, 165, 233, 0.12)",
        "shadow": "rgba(15,23,42,0.08)",
    }


def _system_tokens(app: QApplication) -> dict[str, str]:
    palette = app.palette()

    def color(role: QPalette.ColorRole) -> str:
        return palette.color(role).name()

    return {
        "bg": color(QPalette.ColorRole.Window),
        "panel": color(QPalette.ColorRole.Base),
        "panel_alt": color(QPalette.ColorRole.AlternateBase),
        "elevated": color(QPalette.ColorRole.Base),
        "text_primary": color(QPalette.ColorRole.WindowText),
        "text_secondary": color(QPalette.ColorRole.Text),
        "text_muted": "#6b7280",
        "accent": "#0ea5e9",
        "accent_hover": "#0284c7",
        "accent_active": "#0369a1",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "border": "#d0d7e2",
        "border_strong": "#bcc8d6",
        "input_bg": color(QPalette.ColorRole.Base),
        "selection_bg": "rgba(14, 165, 233, 0.12)",
        "shadow": "rgba(15,23,42,0.06)",
    }


def _fallback_palette(app: QApplication, theme: ThemeName) -> None:
    app.setStyle("Fusion")
    if theme == "system":
        app.setPalette(app.style().standardPalette())
        return

    palette = QPalette()
    roles = QPalette.ColorRole
    if theme == "dark":
        palette.setColor(roles.Window, QColor(15, 23, 35))
        palette.setColor(roles.WindowText, QColor("white"))
        palette.setColor(roles.Base, QColor(13, 20, 30))
        palette.setColor(roles.AlternateBase, QColor(23, 30, 43))
        palette.setColor(roles.ToolTipBase, QColor("white"))
        palette.setColor(roles.ToolTipText, QColor("black"))
        palette.setColor(roles.Text, QColor("white"))
        palette.setColor(roles.Button, QColor(23, 30, 43))
        palette.setColor(roles.ButtonText, QColor("white"))
        palette.setColor(roles.BrightText, QColor("red"))
        palette.setColor(roles.Link, QColor(65, 197, 255))
        palette.setColor(roles.Highlight, QColor(44, 151, 255))
        palette.setColor(roles.HighlightedText, QColor("white"))
    else:
        palette.setColor(roles.Window, QColor("white"))
        palette.setColor(roles.WindowText, QColor("black"))
        palette.setColor(roles.Base, QColor("white"))
        palette.setColor(roles.AlternateBase, QColor(241, 245, 249))
        palette.setColor(roles.ToolTipBase, QColor("white"))
        palette.setColor(roles.ToolTipText, QColor("black"))
        palette.setColor(roles.Text, QColor("black"))
        palette.setColor(roles.Button, QColor(248, 250, 252))
        palette.setColor(roles.ButtonText, QColor("black"))
        palette.setColor(roles.BrightText, QColor("red"))
        palette.setColor(roles.Link, QColor(14, 165, 233))
        palette.setColor(roles.Highlight, QColor(14, 165, 233))
        palette.setColor(roles.HighlightedText, QColor("white"))
    app.setPalette(palette)


def _custom_qss(tokens: dict[str, str]) -> str:
    return f"""
QMainWindow#AppWindow {{
    background: {tokens['bg']};
}}
QWidget#RootShell {{
    background: {tokens['bg']};
}}
QFrame#TopBar, QFrame#FooterBar, QFrame#SidebarCard, QFrame#ContentSurface {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border']};
    border-radius: 14px;
}}
QFrame#SidebarCard {{
    background: {tokens['panel_alt']};
}}
QFrame#FooterBar {{
    background: {tokens['panel_alt']};
}}
QFrame#CardFrame {{
    background: {tokens['elevated']};
    border: 1px solid {tokens['border']};
    border-radius: 14px;
}}
QLabel#AppTitle {{
    color: {tokens['text_primary']};
    font-size: 18px;
    font-weight: 700;
}}
QLabel#AppSubtitle {{
    color: {tokens['text_muted']};
    font-size: 11px;
}}
QLabel#PageTitle {{
    color: {tokens['text_primary']};
    font-size: 24px;
    font-weight: 700;
}}
QLabel#PageSubtitle {{
    color: {tokens['text_secondary']};
    font-size: 12px;
}}
QLabel#SectionTitle {{
    color: {tokens['text_primary']};
    font-size: 14px;
    font-weight: 600;
}}
QLabel#MutedLabel, QLabel#FieldHint {{
    color: {tokens['text_muted']};
    font-size: 11px;
}}
QLabel#WarningBanner {{
    color: {tokens['warning']};
    background: transparent;
    font-weight: 600;
}}
QLabel#StatusBadge {{
    border: 1px solid {tokens['border_strong']};
    background: {tokens['panel_alt']};
    color: {tokens['text_secondary']};
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#StatusBadge[badgeKind="running"], QLabel#StatusBadge[badgeKind="analyzing"] {{
    background: rgba(65, 197, 255, 0.10);
    border-color: rgba(65, 197, 255, 0.45);
    color: {tokens['accent']};
}}
QLabel#StatusBadge[badgeKind="success"] {{
    background: rgba(49, 208, 170, 0.10);
    border-color: rgba(49, 208, 170, 0.45);
    color: {tokens['success']};
}}
QLabel#StatusBadge[badgeKind="warning"] {{
    background: rgba(245, 158, 66, 0.10);
    border-color: rgba(245, 158, 66, 0.45);
    color: {tokens['warning']};
}}
QLabel#StatusBadge[badgeKind="danger"] {{
    background: rgba(251, 113, 133, 0.10);
    border-color: rgba(251, 113, 133, 0.45);
    color: {tokens['danger']};
}}
QLabel#StatValue {{
    color: {tokens['text_primary']};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#StatLabel {{
    color: {tokens['text_muted']};
    font-size: 11px;
}}
QFrame#StatChip {{
    background: {tokens['panel_alt']};
    border: 1px solid {tokens['border']};
    border-radius: 12px;
}}
QLineEdit, QComboBox, QTextEdit {{
    background: {tokens['input_bg']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: {tokens['selection_bg']};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border-color: {tokens['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QPushButton {{
    background: {tokens['panel_alt']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {tokens['border_strong']};
}}
QPushButton:disabled {{
    color: {tokens['text_muted']};
}}
QPushButton[role="primary"] {{
    background: {tokens['accent']};
    border-color: {tokens['accent']};
    color: #06131d;
}}
QPushButton[role="primary"]:hover {{
    background: {tokens['accent_hover']};
    border-color: {tokens['accent_hover']};
}}
QPushButton[role="primary"]:pressed {{
    background: {tokens['accent_active']};
    border-color: {tokens['accent_active']};
}}
QPushButton[role="ghost"] {{
    background: transparent;
}}
QPushButton[segmented="true"] {{
    border-radius: 10px;
    padding: 10px 14px;
}}
QPushButton[segmented="true"][checked="true"] {{
    background: rgba(65, 197, 255, 0.14);
    border-color: rgba(65, 197, 255, 0.55);
    color: {tokens['accent']};
}}
QFrame#SegmentedGroup {{
    background: {tokens['panel_alt']};
    border: 1px solid {tokens['border']};
    border-radius: 12px;
}}
QCheckBox {{
    color: {tokens['text_primary']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {tokens['border_strong']};
    background: {tokens['input_bg']};
}}
QCheckBox::indicator:checked {{
    background: {tokens['accent']};
    border-color: {tokens['accent']};
}}
QTextEdit#LogOutput {{
    font-family: Consolas, 'Courier New', monospace;
    font-size: 11px;
}}
QProgressBar {{
    border: 1px solid {tokens['border']};
    border-radius: 8px;
    background: {tokens['panel_alt']};
    text-align: center;
    color: {tokens['text_secondary']};
}}
QProgressBar::chunk {{
    background: {tokens['accent']};
    border-radius: 6px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {tokens['border_strong']};
    min-height: 24px;
    border-radius: 6px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QFrame#StepItem {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
}}
QFrame#StepItem:hover {{
    background: rgba(255,255,255,0.02);
}}
QFrame#StepItem[stepState="current"] {{
    background: rgba(65, 197, 255, 0.10);
    border-color: rgba(65, 197, 255, 0.26);
}}
QFrame#StepItem[stepState="done"] {{
    border-color: rgba(49, 208, 170, 0.20);
}}
QFrame#StepItem[stepState="invalid"] {{
    border-color: rgba(245, 158, 66, 0.35);
    background: rgba(245, 158, 66, 0.06);
}}
QLabel#StepIndex {{
    color: {tokens['text_muted']};
    font-size: 11px;
    font-weight: 700;
}}
QLabel#StepItemTitle {{
    color: {tokens['text_primary']};
    font-size: 13px;
    font-weight: 600;
}}
QLabel#StepItemDesc {{
    color: {tokens['text_muted']};
    font-size: 11px;
}}
QFrame#StepHighlight {{
    background: {tokens['accent']};
    border-radius: 4px;
}}
"""


def apply_app_theme(app: QApplication, theme: ThemeName) -> None:
    theme = theme if theme in {"system", "dark", "light"} else "system"

    base_sheet = ""
    if theme in {"dark", "light"} and qdarktheme is not None:
        qdt = cast(Any, qdarktheme)
        try:
            if hasattr(qdt, "setup_theme"):
                qdt.setup_theme(theme)
                base_sheet = app.styleSheet()
            elif hasattr(qdt, "load_stylesheet"):
                # Compatibility with older qdarktheme releases that expose
                # stylesheet/palette helpers instead of setup_theme().
                if hasattr(qdt, "load_palette"):
                    app.setPalette(qdt.load_palette(theme))
                base_sheet = str(qdt.load_stylesheet(theme))
            else:
                _fallback_palette(app, theme)
                base_sheet = ""
        except Exception:
            _fallback_palette(app, theme)
            base_sheet = ""
    else:
        _fallback_palette(app, theme)
        base_sheet = ""

    tokens = _system_tokens(app) if theme == "system" else (_dark_tokens() if theme == "dark" else _light_tokens())
    app.setStyleSheet(base_sheet + "\n" + _custom_qss(tokens))
