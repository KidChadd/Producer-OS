from __future__ import annotations

from typing import Any, cast

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

try:
    import qdarktheme  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional runtime dependency
    qdarktheme = None  # type: ignore[assignment]


ThemeName = str
THEME_PRESET_CHOICES: tuple[str, ...] = ("system", "studio_dark", "paper_light", "midnight_blue")
THEME_PRESET_LABELS: dict[str, str] = {
    "system": "System",
    "studio_dark": "Studio Dark",
    "paper_light": "Paper Light",
    "midnight_blue": "Midnight Blue",
}
_THEME_ALIASES: dict[str, str] = {
    "system": "system",
    "dark": "studio_dark",
    "light": "paper_light",
    "studio_dark": "studio_dark",
    "paper_light": "paper_light",
    "midnight_blue": "midnight_blue",
}
UI_DENSITY_CHOICES: tuple[str, ...] = ("comfortable", "compact")
UI_DENSITY_LABELS: dict[str, str] = {
    "comfortable": "Comfortable",
    "compact": "Compact",
}
ACCENT_MODE_CHOICES: tuple[str, ...] = ("theme_default", "preset", "custom")
ACCENT_MODE_LABELS: dict[str, str] = {
    "theme_default": "Theme Default",
    "preset": "Preset",
    "custom": "Custom",
}
ACCENT_PRESET_COLORS: dict[str, str] = {
    "cyan": "#56C8FF",
    "blue": "#4F8CFF",
    "emerald": "#38D39F",
    "amber": "#F6AE53",
    "rose": "#FB738F",
}
ACCENT_PRESET_CHOICES: tuple[str, ...] = tuple(ACCENT_PRESET_COLORS.keys())
ACCENT_PRESET_LABELS: dict[str, str] = {
    "cyan": "Cyan",
    "blue": "Blue",
    "emerald": "Emerald",
    "amber": "Amber",
    "rose": "Rose",
}


def normalize_theme_name(theme: str) -> str:
    return _THEME_ALIASES.get(str(theme or "").strip().lower(), "system")


def normalize_ui_density(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in UI_DENSITY_CHOICES else "comfortable"


def normalize_accent_mode(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in ACCENT_MODE_CHOICES else "theme_default"


def normalize_accent_preset(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in ACCENT_PRESET_CHOICES else "cyan"


def normalize_accent_color(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if not text.startswith("#"):
        text = f"#{text}"
    color = QColor(text)
    if not color.isValid():
        return ""
    return color.name().upper()


def _studio_dark_tokens() -> dict[str, str]:
    return {
        "theme_name": "Studio Dark",
        "bg": "#0A0E15",
        "bg_layer": "#0E1420",
        "panel": "#101827",
        "panel_alt": "#141E2F",
        "elevated": "#182437",
        "card": "#121C2B",
        "card_alt": "#182336",
        "header_grad_start": "#182436",
        "header_grad_end": "#121B2A",
        "text_primary": "#EEF4FF",
        "text_secondary": "#CAD6E8",
        "text_tertiary": "#AFC0D9",
        "text_muted": "#8EA1BA",
        "accent": "#56C8FF",
        "accent_hover": "#7FD7FF",
        "accent_active": "#33B5F3",
        "accent_soft": "rgba(86, 200, 255, 0.13)",
        "success": "#33D19F",
        "success_soft": "rgba(51, 209, 159, 0.12)",
        "warning": "#F6AE53",
        "warning_soft": "rgba(246, 174, 83, 0.13)",
        "danger": "#FB738F",
        "danger_soft": "rgba(251, 115, 143, 0.13)",
        "border_soft": "#253245",
        "border": "#2B3A4F",
        "border_strong": "#39506D",
        "input_bg": "#0C121C",
        "input_bg_alt": "#111A28",
        "selection_bg": "rgba(86, 200, 255, 0.18)",
        "table_hover": "rgba(255,255,255,0.025)",
        "table_selected": "rgba(86, 200, 255, 0.16)",
        "table_header": "#172235",
        "table_header_border": "#30435F",
        "low_conf_tint": "rgba(246, 174, 83, 0.06)",
        "shadow": "rgba(2, 6, 23, 0.42)",
        "font_ui": "'Segoe UI Variable Text', 'Segoe UI', 'Noto Sans', Arial",
        "font_mono": "'Cascadia Mono', Consolas, 'Courier New', monospace",
    }


def _paper_light_tokens() -> dict[str, str]:
    return {
        "theme_name": "Paper Light",
        "bg": "#EFF2F6",
        "bg_layer": "#E8EDF4",
        "panel": "#FFFFFF",
        "panel_alt": "#F7FAFD",
        "elevated": "#FFFFFF",
        "card": "#FFFFFF",
        "card_alt": "#F8FBFE",
        "header_grad_start": "#FFFFFF",
        "header_grad_end": "#F2F7FD",
        "text_primary": "#101827",
        "text_secondary": "#2E3E52",
        "text_tertiary": "#445A73",
        "text_muted": "#637A95",
        "accent": "#1583D8",
        "accent_hover": "#0D72C6",
        "accent_active": "#0A5EA4",
        "accent_soft": "rgba(21, 131, 216, 0.11)",
        "success": "#0F9C6E",
        "success_soft": "rgba(15, 156, 110, 0.10)",
        "warning": "#D4831C",
        "warning_soft": "rgba(212, 131, 28, 0.12)",
        "danger": "#D6475A",
        "danger_soft": "rgba(214, 71, 90, 0.10)",
        "border_soft": "#E0E7F0",
        "border": "#D1DAE6",
        "border_strong": "#B9C8D9",
        "input_bg": "#FFFFFF",
        "input_bg_alt": "#F5F8FC",
        "selection_bg": "rgba(21, 131, 216, 0.12)",
        "table_hover": "rgba(21, 131, 216, 0.03)",
        "table_selected": "rgba(21, 131, 216, 0.10)",
        "table_header": "#F3F7FC",
        "table_header_border": "#CBD6E3",
        "low_conf_tint": "rgba(212, 131, 28, 0.06)",
        "shadow": "rgba(15, 23, 42, 0.07)",
        "font_ui": "'Segoe UI Variable Text', 'Segoe UI', 'Noto Sans', Arial",
        "font_mono": "'Cascadia Mono', Consolas, 'Courier New', monospace",
    }


def _midnight_blue_tokens() -> dict[str, str]:
    return {
        "theme_name": "Midnight Blue",
        "bg": "#060A12",
        "bg_layer": "#0A1020",
        "panel": "#0E1730",
        "panel_alt": "#142044",
        "elevated": "#182650",
        "card": "#111B37",
        "card_alt": "#17254C",
        "header_grad_start": "#18284F",
        "header_grad_end": "#101A35",
        "text_primary": "#EEF2FF",
        "text_secondary": "#D1DAF6",
        "text_tertiary": "#B1C0EA",
        "text_muted": "#8CA0CF",
        "accent": "#79B8FF",
        "accent_hover": "#99C9FF",
        "accent_active": "#5DA7F8",
        "accent_soft": "rgba(121, 184, 255, 0.14)",
        "success": "#47D3A7",
        "success_soft": "rgba(71, 211, 167, 0.12)",
        "warning": "#F8BD5E",
        "warning_soft": "rgba(248, 189, 94, 0.13)",
        "danger": "#FF7A9E",
        "danger_soft": "rgba(255, 122, 158, 0.13)",
        "border_soft": "#263762",
        "border": "#304572",
        "border_strong": "#45639D",
        "input_bg": "#0B1327",
        "input_bg_alt": "#101B37",
        "selection_bg": "rgba(121, 184, 255, 0.20)",
        "table_hover": "rgba(121,184,255,0.05)",
        "table_selected": "rgba(121,184,255,0.16)",
        "table_header": "#1A2A52",
        "table_header_border": "#35538A",
        "low_conf_tint": "rgba(248, 189, 94, 0.07)",
        "shadow": "rgba(1, 3, 10, 0.48)",
        "font_ui": "'Segoe UI Variable Text', 'Segoe UI', 'Noto Sans', Arial",
        "font_mono": "'Cascadia Mono', Consolas, 'Courier New', monospace",
    }


def _system_tokens(app: QApplication) -> dict[str, str]:
    palette = app.palette()

    def color(role: QPalette.ColorRole) -> str:
        return palette.color(role).name()

    return {
        "theme_name": "System",
        "bg": color(QPalette.ColorRole.Window),
        "bg_layer": color(QPalette.ColorRole.Window),
        "panel": color(QPalette.ColorRole.Base),
        "panel_alt": color(QPalette.ColorRole.AlternateBase),
        "elevated": color(QPalette.ColorRole.Base),
        "card": color(QPalette.ColorRole.Base),
        "card_alt": color(QPalette.ColorRole.AlternateBase),
        "header_grad_start": color(QPalette.ColorRole.Base),
        "header_grad_end": color(QPalette.ColorRole.AlternateBase),
        "text_primary": color(QPalette.ColorRole.WindowText),
        "text_secondary": color(QPalette.ColorRole.Text),
        "text_tertiary": color(QPalette.ColorRole.Text),
        "text_muted": "#6b7280",
        "accent": "#0ea5e9",
        "accent_hover": "#0284c7",
        "accent_active": "#0369a1",
        "accent_soft": "rgba(14, 165, 233, 0.10)",
        "success": "#059669",
        "success_soft": "rgba(5, 150, 105, 0.10)",
        "warning": "#d97706",
        "warning_soft": "rgba(217, 119, 6, 0.10)",
        "danger": "#dc2626",
        "danger_soft": "rgba(220, 38, 38, 0.10)",
        "border_soft": "#e2e8f0",
        "border": "#d0d7e2",
        "border_strong": "#bcc8d6",
        "input_bg": color(QPalette.ColorRole.Base),
        "input_bg_alt": color(QPalette.ColorRole.AlternateBase),
        "selection_bg": "rgba(14, 165, 233, 0.12)",
        "table_hover": "rgba(14, 165, 233, 0.03)",
        "table_selected": "rgba(14, 165, 233, 0.10)",
        "table_header": color(QPalette.ColorRole.AlternateBase),
        "table_header_border": "#bcc8d6",
        "low_conf_tint": "rgba(217, 119, 6, 0.06)",
        "shadow": "rgba(15,23,42,0.06)",
        "font_ui": "'Segoe UI Variable Text', 'Segoe UI', 'Noto Sans', Arial",
        "font_mono": "'Cascadia Mono', Consolas, 'Courier New', monospace",
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
QWidget {{
    font-family: {tokens['font_ui']};
    font-size: 10.5pt;
}}
QMainWindow#AppWindow {{
    background: {tokens['bg']};
}}
QWidget#RootShell {{
    background: {tokens['bg']};
}}
QFrame#TopBar, QFrame#FooterBar, QFrame#SidebarCard, QFrame#ContentSurface {{
    background: {tokens['panel']};
    border: 1px solid {tokens['border']};
    border-radius: 16px;
}}
QFrame#SidebarCard {{
    background: {tokens['panel_alt']};
}}
QFrame#FooterBar {{
    background: {tokens['panel_alt']};
}}
QFrame#TopBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {tokens['header_grad_start']}, stop:1 {tokens['header_grad_end']});
}}
QFrame#CardFrame {{
    background: {tokens['card']};
    border: 1px solid {tokens['border_soft']};
    border-radius: 15px;
}}
QLabel#AppTitle {{
    color: {tokens['text_primary']};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
QLabel#AppSubtitle {{
    color: {tokens['text_muted']};
    font-size: 11px;
    font-weight: 500;
}}
QLabel#PageTitle {{
    color: {tokens['text_primary']};
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
QLabel#PageSubtitle {{
    color: {tokens['text_tertiary']};
    font-size: 12px;
    line-height: 1.25;
}}
QLabel#SectionTitle {{
    color: {tokens['text_primary']};
    font-size: 15px;
    font-weight: 650;
}}
QLabel#MutedLabel, QLabel#FieldHint {{
    color: {tokens['text_muted']};
    font-size: 11px;
}}
QLabel#FieldHint[statusKind="success"], QLabel#MutedLabel[state="success"] {{
    color: {tokens['success']};
}}
QLabel#FieldHint[statusKind="warning"], QLabel#MutedLabel[state="warning"] {{
    color: {tokens['warning']};
}}
QLabel#WarningBanner {{
    color: {tokens['warning']};
    background: {tokens['warning_soft']};
    border: 1px solid rgba(245, 158, 66, 0.28);
    border-radius: 10px;
    padding: 8px 10px;
    font-weight: 600;
}}
QLabel#StatusBadge {{
    border: 1px solid {tokens['border_strong']};
    background: {tokens['card_alt']};
    color: {tokens['text_secondary']};
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#StatusBadge[badgeKind="running"], QLabel#StatusBadge[badgeKind="analyzing"] {{
    background: {tokens['accent_soft']};
    border-color: rgba(65, 197, 255, 0.45);
    color: {tokens['accent']};
}}
QLabel#StatusBadge[badgeKind="success"] {{
    background: {tokens['success_soft']};
    border-color: rgba(49, 208, 170, 0.45);
    color: {tokens['success']};
}}
QLabel#StatusBadge[badgeKind="warning"] {{
    background: {tokens['warning_soft']};
    border-color: rgba(245, 158, 66, 0.45);
    color: {tokens['warning']};
}}
QLabel#StatusBadge[badgeKind="danger"] {{
    background: {tokens['danger_soft']};
    border-color: rgba(251, 113, 133, 0.45);
    color: {tokens['danger']};
}}
QLabel#StatValue {{
    color: {tokens['text_primary']};
    font-size: 24px;
    font-weight: 700;
}}
QLabel#StatLabel {{
    color: {tokens['text_muted']};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.4px;
}}
QFrame#StatChip {{
    background: {tokens['card_alt']};
    border: 1px solid {tokens['border_soft']};
    border-radius: 14px;
}}
QLabel#TimelineStep {{
    color: {tokens['text_muted']};
    background: {tokens['panel_alt']};
    border: 1px solid {tokens['border_soft']};
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 10px;
    font-weight: 650;
}}
QLabel#TimelineStep[state="active"] {{
    color: {tokens['accent']};
    background: {tokens['accent_soft']};
    border-color: rgba(65, 197, 255, 0.45);
}}
QLabel#TimelineStep[state="done"] {{
    color: {tokens['success']};
    background: {tokens['success_soft']};
    border-color: rgba(49, 208, 170, 0.35);
}}
QLabel#TimelineStep[state="pending"] {{
    color: {tokens['text_muted']};
}}
QLabel#PathPreview {{
    color: {tokens['text_secondary']};
    background: {tokens['panel_alt']};
    border: 1px solid {tokens['border_soft']};
    border-radius: 12px;
    padding: 10px 12px;
    font-family: {tokens['font_mono']};
    font-size: 10px;
}}
QLabel#InlinePill {{
    border-radius: 999px;
    border: 1px solid {tokens['border_soft']};
    background: {tokens['panel_alt']};
    color: {tokens['text_secondary']};
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}}
QLineEdit, QComboBox, QTextEdit {{
    background: {tokens['input_bg']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: 11px;
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
    background: {tokens['card_alt']};
    color: {tokens['text_primary']};
    border: 1px solid {tokens['border']};
    border-radius: 11px;
    padding: 8px 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {tokens['border_strong']};
    background: {tokens['panel_alt']};
}}
QPushButton:disabled {{
    color: {tokens['text_muted']};
    border-color: {tokens['border_soft']};
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
    font-family: {tokens['font_mono']};
    font-size: 10.5pt;
}}
QProgressBar {{
    border: 1px solid {tokens['border']};
    border-radius: 9px;
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
QTabWidget::pane {{
    border: 1px solid {tokens['border_soft']};
    background: {tokens['panel']};
    border-radius: 12px;
    top: -1px;
}}
QTabBar::tab {{
    color: {tokens['text_muted']};
    background: transparent;
    border: 1px solid transparent;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 7px 12px;
    margin-right: 4px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {tokens['text_primary']};
    background: {tokens['panel']};
    border-color: {tokens['border_soft']};
    border-bottom-color: {tokens['panel']};
}}
QTableWidget, QTableView {{
    background: {tokens['panel']};
    alternate-background-color: {tokens['panel_alt']};
    color: {tokens['text_primary']};
    gridline-color: {tokens['border_soft']};
    border: 1px solid {tokens['border_soft']};
    border-radius: 12px;
    selection-background-color: {tokens['table_selected']};
    selection-color: {tokens['text_primary']};
}}
QTableView::item, QTableWidget::item {{
    padding: 5px 6px;
}}
QTableView::item:hover, QTableWidget::item:hover {{
    background: {tokens['table_hover']};
}}
QHeaderView::section {{
    background: {tokens['table_header']};
    color: {tokens['text_secondary']};
    border: 0px;
    border-right: 1px solid {tokens['table_header_border']};
    border-bottom: 1px solid {tokens['table_header_border']};
    padding: 8px 8px;
    font-size: 10px;
    font-weight: 700;
}}
QTableCornerButton::section {{
    background: {tokens['table_header']};
    border: 0px;
    border-right: 1px solid {tokens['table_header_border']};
    border-bottom: 1px solid {tokens['table_header_border']};
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
    background: {tokens['table_hover']};
}}
QFrame#StepItem[stepState="current"] {{
    background: {tokens['accent_soft']};
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
QFrame#ToastMessage {{
    background: {tokens['elevated']};
    border: 1px solid {tokens['border']};
    border-radius: 12px;
}}
QFrame#ToastMessage[toastKind="success"] {{
    border-color: {tokens['success']};
    background: {tokens['success_soft']};
}}
QFrame#ToastMessage[toastKind="warning"] {{
    border-color: {tokens['warning']};
    background: {tokens['warning_soft']};
}}
QFrame#ToastMessage[toastKind="error"] {{
    border-color: {tokens['danger']};
    background: {tokens['danger_soft']};
}}
QLabel#ToastIcon {{
    color: {tokens['text_secondary']};
    font-weight: 700;
}}
QLabel#ToastText {{
    color: {tokens['text_primary']};
}}
"""


def _rgba(color: QColor, alpha: float) -> str:
    alpha = max(0.0, min(1.0, float(alpha)))
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.3f})"


def _apply_accent_override(
    tokens: dict[str, str],
    *,
    accent_mode: str,
    accent_preset: str,
    accent_color: str,
) -> None:
    accent_mode = normalize_accent_mode(accent_mode)
    if accent_mode == "theme_default":
        return

    if accent_mode == "preset":
        accent_hex = ACCENT_PRESET_COLORS.get(normalize_accent_preset(accent_preset), "")
    else:
        accent_hex = normalize_accent_color(accent_color)

    if not accent_hex:
        return

    accent = QColor(accent_hex)
    if not accent.isValid():
        return

    bg = QColor(tokens.get("bg", "#101010"))
    is_light = bg.lightness() >= 128
    hover = QColor(accent)
    active = QColor(accent)
    if is_light:
        hover = hover.darker(108)
        active = active.darker(124)
        soft_alpha = 0.12
        selection_alpha = 0.12
        table_sel_alpha = 0.10
    else:
        hover = hover.lighter(114)
        active = active.darker(114)
        soft_alpha = 0.14
        selection_alpha = 0.20
        table_sel_alpha = 0.16

    tokens["accent"] = accent.name().upper()
    tokens["accent_hover"] = hover.name().upper()
    tokens["accent_active"] = active.name().upper()
    tokens["accent_soft"] = _rgba(accent, soft_alpha)
    tokens["selection_bg"] = _rgba(accent, selection_alpha)
    tokens["table_selected"] = _rgba(accent, table_sel_alpha)


def _density_override_qss(density: str) -> str:
    density = normalize_ui_density(density)
    if density == "compact":
        return """
QWidget { font-size: 9.75pt; }
QPushButton, QLineEdit, QComboBox, QTextEdit {
    padding-top: 5px;
    padding-bottom: 5px;
}
QTabBar::tab { padding: 6px 10px; }
QHeaderView::section { padding: 6px 7px; font-size: 9px; }
QTableView::item, QTableWidget::item { padding: 3px 5px; }
QScrollBar:vertical { width: 10px; }
QFrame#TopBar { margin: 0px; }
"""
    return """
QWidget { font-size: 10.5pt; }
QPushButton, QLineEdit, QComboBox, QTextEdit {
    padding-top: 7px;
    padding-bottom: 7px;
}
QTabBar::tab { padding: 8px 12px; }
QHeaderView::section { padding: 8px 8px; font-size: 10px; }
QTableView::item, QTableWidget::item { padding: 5px 6px; }
QScrollBar:vertical { width: 12px; }
"""


def get_theme_tokens(
    app: QApplication | None,
    theme: ThemeName,
    *,
    density: str = "comfortable",
    accent_mode: str = "theme_default",
    accent_preset: str = "cyan",
    accent_color: str = "",
) -> dict[str, str]:
    theme = normalize_theme_name(theme)
    density = normalize_ui_density(density)
    accent_mode = normalize_accent_mode(accent_mode)
    accent_preset = normalize_accent_preset(accent_preset)
    accent_color = normalize_accent_color(accent_color)

    if theme == "system":
        if app is not None:
            tokens = _system_tokens(app)
        else:
            tokens = _paper_light_tokens()
            tokens["theme_name"] = "System"
    elif theme == "midnight_blue":
        tokens = _midnight_blue_tokens()
    elif theme == "paper_light":
        tokens = _paper_light_tokens()
    else:
        tokens = _studio_dark_tokens()

    _apply_accent_override(
        tokens,
        accent_mode=accent_mode,
        accent_preset=accent_preset,
        accent_color=accent_color,
    )
    tokens["ui_density"] = density
    tokens["accent_mode"] = accent_mode
    tokens["accent_preset"] = accent_preset
    tokens["accent_color"] = accent_color
    return tokens


def build_theme_preview_card_style(
    theme: ThemeName,
    *,
    density: str = "comfortable",
    accent_mode: str = "theme_default",
    accent_preset: str = "cyan",
    accent_color: str = "",
    selected: bool = False,
    app: QApplication | None = None,
) -> str:
    tokens = get_theme_tokens(
        app,
        theme,
        density=density,
        accent_mode=accent_mode,
        accent_preset=accent_preset,
        accent_color=accent_color,
    )
    border = tokens["accent"] if selected else tokens["border"]
    return (
        "QFrame#ThemePreviewCard{"
        f"background:{tokens['card']};"
        f"border:1px solid {border};"
        "border-radius:12px;"
        "}"
        "QFrame#ThemePreviewCard:hover{"
        f"border-color:{tokens['border_strong']};"
        "}"
        "QLabel#ThemePreviewTitle{"
        f"color:{tokens['text_primary']};font-weight:600;"
        "}"
        "QLabel#ThemePreviewMeta{"
        f"color:{tokens['text_muted']};font-size:10px;"
        "}"
        "QFrame#ThemePreviewStrip{"
        f"background:{tokens['header_grad_start']};"
        f"border:1px solid {tokens['border_soft']};"
        "border-radius:8px;"
        "}"
        "QFrame#ThemePreviewAccent{"
        f"background:{tokens['accent']};"
        "border-radius:5px;"
        "}"
        "QFrame#ThemePreviewChip{"
        f"background:{tokens['accent_soft']};"
        f"border:1px solid {tokens['border_soft']};"
        "border-radius:7px;"
        "}"
        "QLabel#ThemePreviewChipText{"
        f"color:{tokens['text_secondary']};font-size:9px;font-weight:600;"
        "}"
    )


def apply_app_theme(
    app: QApplication,
    theme: ThemeName,
    *,
    density: str = "comfortable",
    accent_mode: str = "theme_default",
    accent_preset: str = "cyan",
    accent_color: str = "",
) -> None:
    theme = normalize_theme_name(theme)
    density = normalize_ui_density(density)
    base_mode = "system" if theme == "system" else ("light" if theme == "paper_light" else "dark")

    base_sheet = ""
    if base_mode in {"dark", "light"} and qdarktheme is not None:
        qdt = cast(Any, qdarktheme)
        try:
            if hasattr(qdt, "setup_theme"):
                qdt.setup_theme(base_mode)
                base_sheet = app.styleSheet()
            elif hasattr(qdt, "load_stylesheet"):
                # Compatibility with older qdarktheme releases that expose
                # stylesheet/palette helpers instead of setup_theme().
                if hasattr(qdt, "load_palette"):
                    app.setPalette(qdt.load_palette(base_mode))
                base_sheet = str(qdt.load_stylesheet(base_mode))
            else:
                _fallback_palette(app, base_mode)
                base_sheet = ""
        except Exception:
            _fallback_palette(app, base_mode)
            base_sheet = ""
    else:
        _fallback_palette(app, base_mode)
        base_sheet = ""

    tokens = get_theme_tokens(
        app,
        theme,
        density=density,
        accent_mode=accent_mode,
        accent_preset=accent_preset,
        accent_color=accent_color,
    )
    app.setStyleSheet(base_sheet + "\n" + _custom_qss(tokens) + "\n" + _density_override_qss(density))
