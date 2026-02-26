from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QStyle, QWidget

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import SegmentedControl, set_widget_role


class HubPage(BaseWizardPage):
    browseRequested = Signal()
    hubPathChanged = Signal(str)
    outputFolderNameChanged = Signal(str)
    actionChanged = Signal(str)

    def __init__(self, hub_path: str, output_folder_name: str, action: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            "Step 2 - Destination",
            "Choose the destination root, organized folder name, and whether files should be copied or moved.",
            parent,
        )

        path_card = self.add_card(
            "Destination Folder",
            "Logs are written here. Sorted folders are written into the organized folder name below.",
        )
        self.hub_edit = QLineEdit(hub_path)
        self.hub_edit.setPlaceholderText(r"C:\Path\To\Destination")
        self.hub_edit.textChanged.connect(self._on_hub_path_changed)

        self.browse_btn = QPushButton("Browse...")
        set_widget_role(self.browse_btn, "primary")
        self.browse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.browse_btn.clicked.connect(self.browseRequested.emit)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.hub_edit, 1)
        row.addWidget(self.browse_btn)
        path_card.body_layout.addLayout(row)

        name_card = self.add_card(
            "Organized Folder Name",
            "Creates a folder beside logs (for example: Hub, Outbox, Destination).",
        )
        self.output_folder_name_edit = QLineEdit(output_folder_name or "Hub")
        self.output_folder_name_edit.setPlaceholderText("Hub")
        self.output_folder_name_edit.textChanged.connect(self._on_output_folder_name_changed)
        name_card.body_layout.addWidget(self.output_folder_name_edit)

        preview_card = self.add_card(
            "Output Structure Preview",
            "This shows where logs and the organized sample folders will be written.",
        )
        self.output_preview_label = QLabel()
        self.output_preview_label.setObjectName("PathPreview")
        self.output_preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.output_preview_label.setWordWrap(True)
        preview_card.body_layout.addWidget(self.output_preview_label)

        action_card = self.add_card("Transfer Mode", "Copy is non-destructive. Move is logged and can be undone.")
        self.action_control = SegmentedControl(values=["move", "copy"], current=action)
        self.action_control.valueChanged.connect(self.actionChanged.emit)
        action_card.body_layout.addWidget(self.action_control)

        warn_card = self.add_card("Routing Validation", "Producer-OS checks for common path mistakes before running.")
        self.warning_label = QLabel("No routing issues detected.")
        self.warning_label.setWordWrap(True)
        self.warning_label.setObjectName("MutedLabel")
        warn_card.body_layout.addWidget(self.warning_label)

        self._update_output_preview()

    def set_hub_path(self, path: str) -> None:
        with QSignalBlocker(self.hub_edit):
            self.hub_edit.setText(path)
        self._update_output_preview()

    def set_output_folder_name(self, name: str) -> None:
        with QSignalBlocker(self.output_folder_name_edit):
            self.output_folder_name_edit.setText(name)
        self._update_output_preview()

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

    def _on_hub_path_changed(self, path: str) -> None:
        self._update_output_preview()
        self.hubPathChanged.emit(path)

    def _on_output_folder_name_changed(self, name: str) -> None:
        self._update_output_preview()
        self.outputFolderNameChanged.emit(name)

    def _update_output_preview(self) -> None:
        root = (self.hub_edit.text() or "").strip() or r"C:\Destination"
        folder_name = (self.output_folder_name_edit.text() or "").strip() or "Hub"
        lines = [
            root,
            "  ├─ logs\\",
            f"  └─ {folder_name}\\",
            "      ├─ Samples\\",
            "      ├─ Loops\\",
            "      ├─ Samples.nfo",
            "      └─ Loops.nfo",
        ]
        self.output_preview_label.setText("\n".join(lines))

    def apply_density(self, density: str) -> None:  # type: ignore[override]
        super().apply_density(density)
        compact = str(density or "").strip().lower() == "compact"
        self.output_preview_label.setStyleSheet(
            "padding: 6px 8px;" if compact else "padding: 10px 12px;"
        )
