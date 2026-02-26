from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from producer_os.ui.data.fl_icon_favorites import FL_ICON_FAVORITES


def parse_icon_index(value: str) -> Optional[int]:
    text = (value or "").strip()
    if not text:
        return None
    base = 10
    if text.lower().startswith("0x"):
        text = text[2:]
        base = 16
    elif text.startswith("$"):
        text = text[1:]
        base = 16
    elif any(ch in "ABCDEFabcdef" for ch in text):
        base = 16
    elif len(text) == 4 and all(ch in "0123456789ABCDEFabcdef" for ch in text):
        base = 16
    if not text:
        return None
    try:
        parsed = int(text, base)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


class IconPickerDialog(QDialog):
    def __init__(self, current_value: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pick FL Bucket Icon")
        self.resize(560, 460)
        self._selected_icon_index: Optional[int] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        hint = QLabel(
            "Search curated FL icon favorites, or type a manual IconIndex (decimal or hex like f129 / 0xF129 / $F129)."
        )
        hint.setWordWrap(True)
        hint.setObjectName("FieldHint")
        root.addWidget(hint)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search label, tags, decimal, or hex...")
        self.search_edit.textChanged.connect(self._refresh_list)
        root.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_list_selection_changed)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.accept())
        root.addWidget(self.list_widget, 1)

        manual_row = QHBoxLayout()
        manual_row.setContentsMargins(0, 0, 0, 0)
        manual_row.setSpacing(8)
        self.manual_edit = QLineEdit(current_value)
        self.manual_edit.setPlaceholderText("Manual IconIndex (optional)")
        self.manual_edit.textChanged.connect(self._update_preview)
        manual_row.addWidget(QLabel("Manual:"))
        manual_row.addWidget(self.manual_edit, 1)
        root.addLayout(manual_row)

        preview_row = QHBoxLayout()
        preview_row.setContentsMargins(0, 0, 0, 0)
        preview_row.setSpacing(8)
        self.preview_glyph = QLabel(" ")
        self.preview_glyph.setObjectName("PreviewGlyph")
        self.preview_glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_glyph.setMinimumWidth(54)
        self.preview_glyph.setStyleSheet("border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px;")
        preview_row.addWidget(self.preview_glyph)
        self.preview_label = QLabel("Select an icon or type a manual value.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setObjectName("FieldHint")
        preview_row.addWidget(self.preview_label, 1)
        root.addLayout(preview_row)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

        self._refresh_list()
        self._prime_selection(current_value)
        self._update_preview()

    def selected_icon_index(self) -> Optional[int]:
        return self._selected_icon_index

    def _refresh_list(self) -> None:
        query = (self.search_edit.text() or "").strip().lower()
        current_selected = self._selected_icon_index
        self.list_widget.clear()
        for entry in FL_ICON_FAVORITES:
            hay = " ".join(
                [
                    entry["label"],
                    entry["code_hex"],
                    str(entry["icon_index"]),
                    *entry.get("tags", []),
                ]
            ).lower()
            if query and query not in hay:
                continue
            icon_index = int(entry["icon_index"])
            glyph = chr(icon_index) if 0 <= icon_index <= 0x10FFFF else ""
            text = f"{glyph}  {entry['label']}  (U+{icon_index:04X} / {icon_index})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, icon_index)
            item.setToolTip(", ".join(entry.get("tags", [])))
            if current_selected is not None and icon_index == current_selected:
                item.setSelected(True)
            self.list_widget.addItem(item)

    def _prime_selection(self, current_value: str) -> None:
        parsed = parse_icon_index(current_value)
        if parsed is None:
            return
        self._selected_icon_index = parsed
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if int(item.data(Qt.ItemDataRole.UserRole) or -1) == parsed:
                self.list_widget.setCurrentItem(item)
                break

    def _on_list_selection_changed(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        icon_index = int(item.data(Qt.ItemDataRole.UserRole) or 0)
        self._selected_icon_index = icon_index
        self.manual_edit.blockSignals(True)
        self.manual_edit.setText(f"{icon_index}")
        self.manual_edit.blockSignals(False)
        self._update_preview()

    def _update_preview(self) -> None:
        parsed = parse_icon_index(self.manual_edit.text())
        if parsed is None:
            self.preview_glyph.setText("?")
            self.preview_glyph.setStyleSheet(
                "border:1px solid rgba(217,119,6,0.45); border-radius:8px; padding:6px; color:#D97706;"
            )
            self.preview_label.setText("Invalid IconIndex format. Use decimal or hex (f129, 0xF129, $F129).")
            self._selected_icon_index = None
            return
        self._selected_icon_index = parsed
        glyph = chr(parsed) if 0 <= parsed <= 0x10FFFF else ""
        self.preview_glyph.setText(glyph or "·")
        self.preview_glyph.setStyleSheet(
            "border:1px solid rgba(125,125,125,0.35); border-radius:8px; padding:6px;"
        )
        self.preview_label.setText(f"Preview: U+{parsed:04X} ({parsed})")

    def accept(self) -> None:  # type: ignore[override]
        parsed = parse_icon_index(self.manual_edit.text())
        if parsed is None:
            QMessageBox.warning(self, "Icon picker", "Please select a valid icon or enter a valid IconIndex value.")
            return
        self._selected_icon_index = parsed
        super().accept()
