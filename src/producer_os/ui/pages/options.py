from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import AnimatedPanel, set_widget_role


class OptionsPage(BaseWizardPage):
    fileTypeChanged = Signal(str, bool)
    preserveVendorChanged = Signal(bool)
    loopSafetyChanged = Signal(bool)
    themeChanged = Signal(str)
    developerToolsChanged = Signal(bool)
    openConfigRequested = Signal()
    openLastReportRequested = Signal()
    validateSchemasRequested = Signal()

    def __init__(
        self,
        file_types: dict[str, bool],
        preserve_vendor: bool,
        loop_safety: bool,
        theme: str,
        developer_tools: bool,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            "Step 3 - Options",
            "Tune file handling, safety behaviors, theme appearance, and developer utilities.",
            parent,
        )

        file_card = self.add_card("File Types", "Select which audio formats Producer-OS should process.")
        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(16)
        self.file_type_checkboxes: dict[str, QCheckBox] = {}
        for ext, label in [("wav", "WAV"), ("mp3", "MP3"), ("flac", "FLAC")]:
            cb = QCheckBox(label)
            cb.setChecked(bool(file_types.get(ext, False)))
            cb.toggled.connect(lambda checked, e=ext: self.fileTypeChanged.emit(e, checked))
            self.file_type_checkboxes[ext] = cb
            file_row.addWidget(cb)
        file_row.addStretch(1)
        file_card.body_layout.addLayout(file_row)

        routing_card = self.add_card("Routing & Safety")
        self.vendor_checkbox = QCheckBox("Preserve vendor structure (keep original folder layout)")
        self.vendor_checkbox.setChecked(preserve_vendor)
        self.vendor_checkbox.toggled.connect(self.preserveVendorChanged.emit)
        routing_card.body_layout.addWidget(self.vendor_checkbox)

        self.loop_checkbox = QCheckBox("Avoid reprocessing duplicate loops (prevent '(2)' spam)")
        self.loop_checkbox.setChecked(loop_safety)
        self.loop_checkbox.toggled.connect(self.loopSafetyChanged.emit)
        routing_card.body_layout.addWidget(self.loop_checkbox)

        routing_hint = QLabel(
            "FL Studio styling writes sidecar .nfo files next to folders and relies on IconIndex metadata."
        )
        routing_hint.setObjectName("FieldHint")
        routing_hint.setWordWrap(True)
        routing_card.body_layout.addWidget(routing_hint)

        appearance_card = self.add_card("Appearance", "Theme changes apply immediately and are saved to config.")
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "dark", "light"])
        idx = self.theme_combo.findText(theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentTextChanged.connect(self.themeChanged.emit)
        form.addRow("Theme:", self.theme_combo)
        appearance_card.body_layout.addLayout(form)

        dev_card = self.add_card("Developer Tools", "Utility actions for diagnostics and configuration maintenance.")
        self.dev_checkbox = QCheckBox("Enable developer tools")
        self.dev_checkbox.setChecked(developer_tools)
        self.dev_checkbox.toggled.connect(self._on_dev_tools_toggled)
        dev_card.body_layout.addWidget(self.dev_checkbox)

        dev_buttons_host = QWidget()
        dev_buttons_layout = QVBoxLayout(dev_buttons_host)
        dev_buttons_layout.setContentsMargins(0, 4, 0, 0)
        dev_buttons_layout.setSpacing(8)

        self.open_config_btn = QPushButton("Open config folder")
        self.open_last_report_btn = QPushButton("Open last report")
        self.validate_schema_btn = QPushButton("Validate schemas")
        for btn in (self.open_config_btn, self.open_last_report_btn, self.validate_schema_btn):
            set_widget_role(btn, "ghost")
            dev_buttons_layout.addWidget(btn)

        self.open_config_btn.clicked.connect(self.openConfigRequested.emit)
        self.open_last_report_btn.clicked.connect(self.openLastReportRequested.emit)
        self.validate_schema_btn.clicked.connect(self.validateSchemasRequested.emit)

        self.dev_tools_panel = AnimatedPanel(dev_buttons_host, expanded=developer_tools)
        dev_card.body_layout.addWidget(self.dev_tools_panel)

    def _on_dev_tools_toggled(self, checked: bool) -> None:
        self.dev_tools_panel.set_expanded(checked, animate=True)
        self.developerToolsChanged.emit(checked)

    def set_theme_value(self, theme: str) -> None:
        idx = self.theme_combo.findText(theme)
        if idx < 0:
            return
        with QSignalBlocker(self.theme_combo):
            self.theme_combo.setCurrentIndex(idx)

    def set_developer_tools_visible(self, enabled: bool, animate: bool = True) -> None:
        with QSignalBlocker(self.dev_checkbox):
            self.dev_checkbox.setChecked(enabled)
        self.dev_tools_panel.set_expanded(enabled, animate=animate)
