from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import SegmentedControl, set_widget_role


class HubPage(BaseWizardPage):
    browseRequested = Signal()
    hubPathChanged = Signal(str)
    actionChanged = Signal(str)

    def __init__(self, hub_path: str, action: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            "Step 2 - Hub Destination",
            "Choose the destination hub and whether files should be copied or moved.",
            parent,
        )

        path_card = self.add_card("Hub Folder", "The destination hub receives sorted files and run logs.")
        self.hub_edit = QLineEdit(hub_path)
        self.hub_edit.setPlaceholderText(r"C:\Path\To\Hub")
        self.hub_edit.textChanged.connect(self.hubPathChanged.emit)

        browse_btn = QPushButton("Browse...")
        set_widget_role(browse_btn, "primary")
        browse_btn.clicked.connect(self.browseRequested.emit)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.hub_edit, 1)
        row.addWidget(browse_btn)
        path_card.body_layout.addLayout(row)

        action_card = self.add_card("Transfer Mode", "Copy is non-destructive. Move is logged and can be undone.")
        self.action_control = SegmentedControl(values=["move", "copy"], current=action)
        self.action_control.valueChanged.connect(self.actionChanged.emit)
        action_card.body_layout.addWidget(self.action_control)

        warn_card = self.add_card("Routing Validation", "Producer-OS checks for common path mistakes before running.")
        self.warning_label = QLabel("No routing issues detected.")
        self.warning_label.setWordWrap(True)
        self.warning_label.setObjectName("MutedLabel")
        warn_card.body_layout.addWidget(self.warning_label)

    def set_hub_path(self, path: str) -> None:
        with QSignalBlocker(self.hub_edit):
            self.hub_edit.setText(path)

    def set_action(self, action: str) -> None:
        self.action_control.set_value(action, emit=False)

    def set_warning(self, warning: str) -> None:
        if warning:
            self.warning_label.setObjectName("WarningBanner")
            self.warning_label.setText(warning)
        else:
            self.warning_label.setObjectName("MutedLabel")
            self.warning_label.setText("No routing issues detected.")
        from producer_os.ui.widgets import repolish

        repolish(self.warning_label)
