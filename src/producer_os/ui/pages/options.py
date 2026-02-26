from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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
    openLogsRequested = Signal()
    openLastReportRequested = Signal()
    validateSchemasRequested = Signal()
    verifyAudioDependenciesRequested = Signal()
    qtPluginCheckRequested = Signal()
    bucketCustomizationReloadRequested = Signal()
    bucketCustomizationSaveRequested = Signal(object, object, object)

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

        troubleshoot_card = self.add_card("Troubleshooting", "Quick diagnostics and support actions for runtime issues.")
        actions_host = QWidget()
        actions_layout = QVBoxLayout(actions_host)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self.tr_open_config_btn = QPushButton("Open config folder")
        self.tr_open_logs_btn = QPushButton("Open logs folder")
        self.tr_open_last_report_btn = QPushButton("Open last report")
        self.verify_audio_deps_btn = QPushButton("Verify audio dependencies")
        self.qt_plugin_check_btn = QPushButton("Qt plugin check")
        for btn in (
            self.tr_open_config_btn,
            self.tr_open_logs_btn,
            self.tr_open_last_report_btn,
            self.verify_audio_deps_btn,
            self.qt_plugin_check_btn,
        ):
            set_widget_role(btn, "ghost")
            actions_layout.addWidget(btn)

        self.tr_open_config_btn.clicked.connect(self.openConfigRequested.emit)
        self.tr_open_logs_btn.clicked.connect(self.openLogsRequested.emit)
        self.tr_open_last_report_btn.clicked.connect(self.openLastReportRequested.emit)
        self.verify_audio_deps_btn.clicked.connect(self.verifyAudioDependenciesRequested.emit)
        self.qt_plugin_check_btn.clicked.connect(self.qtPluginCheckRequested.emit)

        troubleshoot_card.body_layout.addWidget(actions_host)

        self.portable_mode_label = QLabel("Portable mode: unknown")
        self.portable_mode_label.setObjectName("FieldHint")
        self.portable_mode_label.setWordWrap(True)
        troubleshoot_card.body_layout.addWidget(self.portable_mode_label)

        self.audio_deps_status_label = QLabel("Audio dependencies: not checked yet")
        self.audio_deps_status_label.setObjectName("FieldHint")
        self.audio_deps_status_label.setWordWrap(True)
        troubleshoot_card.body_layout.addWidget(self.audio_deps_status_label)

        self.qt_plugin_status_label = QLabel("Qt plugin check: not checked yet")
        self.qt_plugin_status_label.setObjectName("FieldHint")
        self.qt_plugin_status_label.setWordWrap(True)
        troubleshoot_card.body_layout.addWidget(self.qt_plugin_status_label)

        bucket_card = self.add_card(
            "Bucket Customization",
            "Customize bucket folder names, colors, and FL Studio bucket icons. Changes apply to future runs and style writes.",
        )
        bucket_hint = QLabel(
            "Names are saved to buckets.json. Colors/icons are saved to bucket_styles.json. "
            "IconIndex accepts decimal (10) or hex codes (f129, 0074, 0xF129)."
        )
        bucket_hint.setObjectName("FieldHint")
        bucket_hint.setWordWrap(True)
        bucket_card.body_layout.addWidget(bucket_hint)

        self.bucket_table = QTableWidget(0, 4)
        self.bucket_table.setHorizontalHeaderLabels(["Bucket ID", "Display Name", "Color", "IconIndex"])
        self.bucket_table.setAlternatingRowColors(True)
        self.bucket_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bucket_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bucket_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.bucket_table.verticalHeader().setVisible(False)
        self.bucket_table.horizontalHeader().setStretchLastSection(True)
        self.bucket_table.setMinimumHeight(220)
        bucket_card.body_layout.addWidget(self.bucket_table)

        bucket_actions = QHBoxLayout()
        bucket_actions.setContentsMargins(0, 0, 0, 0)
        bucket_actions.setSpacing(8)
        self.pick_bucket_color_btn = QPushButton("Pick color for selected row")
        self.reload_bucket_custom_btn = QPushButton("Reload bucket customizations")
        self.save_bucket_custom_btn = QPushButton("Save bucket customizations")
        for btn in (self.pick_bucket_color_btn, self.reload_bucket_custom_btn, self.save_bucket_custom_btn):
            set_widget_role(btn, "ghost")
            bucket_actions.addWidget(btn)
        bucket_actions.addStretch(1)
        bucket_card.body_layout.addLayout(bucket_actions)

        self.bucket_custom_status_label = QLabel("Bucket customization: not loaded yet")
        self.bucket_custom_status_label.setObjectName("FieldHint")
        self.bucket_custom_status_label.setWordWrap(True)
        bucket_card.body_layout.addWidget(self.bucket_custom_status_label)

        self._bucket_table_updating = False
        self.bucket_table.itemChanged.connect(self._on_bucket_table_item_changed)
        self.pick_bucket_color_btn.clicked.connect(self._pick_selected_bucket_color)
        self.reload_bucket_custom_btn.clicked.connect(self.bucketCustomizationReloadRequested.emit)
        self.save_bucket_custom_btn.clicked.connect(self._emit_bucket_customization_save)

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

    def set_portable_mode_status(self, enabled: bool) -> None:
        self.portable_mode_label.setText(f"Portable mode: {'enabled' if enabled else 'disabled'}")

    def set_audio_dependencies_status(self, text: str) -> None:
        self.audio_deps_status_label.setText(f"Audio dependencies: {text}")

    def set_qt_plugin_status(self, text: str) -> None:
        self.qt_plugin_status_label.setText(f"Qt plugin check: {text}")

    # ------------------------------------------------------------------
    # Bucket customization editor (names + colors)
    def set_bucket_customizations(
        self,
        bucket_ids: list[str],
        bucket_names: dict[str, str],
        bucket_styles: dict[str, dict[str, object]],
    ) -> None:
        self._bucket_table_updating = True
        try:
            self.bucket_table.clearContents()
            self.bucket_table.setRowCount(len(bucket_ids))
            for row, bucket_id in enumerate(bucket_ids):
                display_name = str((bucket_names or {}).get(bucket_id, bucket_id) or bucket_id)
                style = dict((bucket_styles or {}).get(bucket_id) or {})
                color_text = str(style.get("Color", "$7F7F7F") or "$7F7F7F")
                icon_value = style.get("IconIndex", 0)
                icon_text = str(icon_value if icon_value is not None else 0)

                id_item = QTableWidgetItem(bucket_id)
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.bucket_table.setItem(row, 0, id_item)

                self.bucket_table.setItem(row, 1, QTableWidgetItem(display_name))
                self.bucket_table.setItem(row, 2, QTableWidgetItem(color_text))
                self.bucket_table.setItem(row, 3, QTableWidgetItem(icon_text))
                self._refresh_bucket_color_cell(row)
        finally:
            self._bucket_table_updating = False

        self.bucket_table.resizeColumnsToContents()
        self.bucket_table.horizontalHeader().setStretchLastSection(True)
        self.set_bucket_customization_status("Loaded bucket names/colors from current config.", success=True)

    def set_bucket_customization_status(self, text: str, success: bool = True) -> None:
        prefix = "Bucket customization: "
        if not text.lower().startswith("bucket customization:"):
            text = prefix + text
        self.bucket_custom_status_label.setText(text)
        self.bucket_custom_status_label.setProperty("statusKind", "success" if success else "warning")

    def _on_bucket_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._bucket_table_updating:
            return
        if item.column() == 2:
            self._refresh_bucket_color_cell(item.row())

    def _refresh_bucket_color_cell(self, row: int) -> None:
        item = self.bucket_table.item(row, 2)
        if item is None:
            return
        color = self._qcolor_from_text(item.text())
        if color is None:
            item.setBackground(QColor())
            return
        item.setBackground(color)

    def _qcolor_from_text(self, value: str) -> Optional[QColor]:
        text = (value or "").strip()
        if not text:
            return None
        if text.startswith("$"):
            text = "#" + text[1:]
        elif not text.startswith("#"):
            text = "#" + text
        if len(text) != 7:
            return None
        color = QColor(text)
        return color if color.isValid() else None

    def _pick_selected_bucket_color(self) -> None:
        row = self.bucket_table.currentRow()
        if row < 0:
            self.set_bucket_customization_status("Select a bucket row first to pick a color.", success=False)
            return
        current_item = self.bucket_table.item(row, 2)
        current_color = self._qcolor_from_text(current_item.text() if current_item else "")
        if current_color is None:
            current_color = QColor("#7F7F7F")
        chosen = QColorDialog.getColor(current_color, self, "Select Bucket Color")
        if not chosen.isValid():
            return
        color_text = f"${chosen.name()[1:].upper()}"
        self._bucket_table_updating = True
        try:
            if current_item is None:
                current_item = QTableWidgetItem(color_text)
                self.bucket_table.setItem(row, 2, current_item)
            else:
                current_item.setText(color_text)
            self._refresh_bucket_color_cell(row)
        finally:
            self._bucket_table_updating = False
        self.set_bucket_customization_status("Selected color updated. Save to persist changes.", success=True)

    def _emit_bucket_customization_save(self) -> None:
        names: dict[str, str] = {}
        colors: dict[str, str] = {}
        icons: dict[str, str] = {}
        for row in range(self.bucket_table.rowCount()):
            bucket_item = self.bucket_table.item(row, 0)
            name_item = self.bucket_table.item(row, 1)
            color_item = self.bucket_table.item(row, 2)
            icon_item = self.bucket_table.item(row, 3)
            if bucket_item is None:
                continue
            bucket_id = bucket_item.text().strip()
            if not bucket_id:
                continue
            names[bucket_id] = (name_item.text().strip() if name_item else bucket_id) or bucket_id
            colors[bucket_id] = (color_item.text().strip() if color_item else "").strip()
            icons[bucket_id] = (icon_item.text().strip() if icon_item else "").strip()
        self.bucketCustomizationSaveRequested.emit(names, colors, icons)
