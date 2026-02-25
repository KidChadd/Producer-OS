from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import StatChip, set_widget_role


class InboxPage(BaseWizardPage):
    browseRequested = Signal()
    inboxPathChanged = Signal(str)
    dryRunChanged = Signal(bool)

    def __init__(self, inbox_path: str, dry_run: bool, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            "Step 1 - Inbox Source",
            "Choose the source folder containing packs. Preview updates live as you type.",
            parent,
        )

        path_card = self.add_card("Inbox Folder", "Select the source directory you want Producer-OS to scan.")
        self.inbox_edit = QLineEdit(inbox_path)
        self.inbox_edit.setPlaceholderText(r"C:\Path\To\Inbox")
        self.inbox_edit.textChanged.connect(self.inboxPathChanged.emit)

        browse_btn = QPushButton("Browse...")
        set_widget_role(browse_btn, "primary")
        browse_btn.clicked.connect(self.browseRequested.emit)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.inbox_edit, 1)
        row.addWidget(browse_btn)
        path_card.body_layout.addLayout(row)

        preview_card = self.add_card("Preview", "A quick scan of top-level contents helps validate your source.")
        stats_row = QHBoxLayout()
        stats_row.setContentsMargins(0, 0, 0, 0)
        stats_row.setSpacing(10)
        self.packs_chip = StatChip("Packs", "0")
        self.loose_chip = StatChip("Loose Files", "0")
        stats_row.addWidget(self.packs_chip)
        stats_row.addWidget(self.loose_chip)
        preview_card.body_layout.addLayout(stats_row)

        self.preview_label = QLabel("Preview: 0 pack(s), 0 loose file(s)")
        self.preview_label.setObjectName("MutedLabel")
        preview_card.body_layout.addWidget(self.preview_label)

        safety_card = self.add_card("Safety", "Dry run analyzes routing without moving or copying any files.")
        self.dry_run_checkbox = QCheckBox("Dry run (no file operations)")
        self.dry_run_checkbox.setChecked(dry_run)
        self.dry_run_checkbox.toggled.connect(self.dryRunChanged.emit)
        safety_card.body_layout.addWidget(self.dry_run_checkbox)

        note = QLabel("Recommended for the first pass on a new inbox or ruleset.")
        note.setObjectName("FieldHint")
        safety_card.body_layout.addWidget(note)

    def set_inbox_path(self, path: str) -> None:
        with QSignalBlocker(self.inbox_edit):
            self.inbox_edit.setText(path)

    def set_dry_run(self, enabled: bool) -> None:
        with QSignalBlocker(self.dry_run_checkbox):
            self.dry_run_checkbox.setChecked(enabled)

    def set_preview_counts(self, pack_count: int, loose_count: int) -> None:
        self.packs_chip.set_value(str(pack_count))
        self.loose_chip.set_value(str(loose_count))
        self.preview_label.setText(f"Preview: {pack_count} pack(s), {loose_count} loose file(s)")
