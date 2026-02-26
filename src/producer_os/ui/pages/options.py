from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.dialogs.icon_picker import IconPickerDialog
from producer_os.ui.theme import (
    ACCENT_MODE_CHOICES,
    ACCENT_MODE_LABELS,
    ACCENT_PRESET_CHOICES,
    ACCENT_PRESET_LABELS,
    THEME_PRESET_CHOICES,
    THEME_PRESET_LABELS,
    UI_DENSITY_CHOICES,
    UI_DENSITY_LABELS,
    build_theme_preview_card_style,
    normalize_accent_color,
    normalize_accent_mode,
    normalize_accent_preset,
    normalize_theme_name,
    normalize_ui_density,
)
from producer_os.ui.widgets import AnimatedPanel, NoWheelComboBox, ThemePreviewCard, set_widget_role


class OptionsPage(BaseWizardPage):
    fileTypeChanged = Signal(str, bool)
    preserveVendorChanged = Signal(bool)
    loopSafetyChanged = Signal(bool)
    themeChanged = Signal(str)
    uiDensityChanged = Signal(str)
    accentModeChanged = Signal(str)
    accentPresetChanged = Signal(str)
    accentColorChanged = Signal(str)
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
        ui_density: str,
        ui_accent_mode: str,
        ui_accent_preset: str,
        ui_accent_color: str,
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
        self.theme_combo = NoWheelComboBox()
        for theme_value in THEME_PRESET_CHOICES:
            self.theme_combo.addItem(THEME_PRESET_LABELS.get(theme_value, theme_value), theme_value)
        idx = self.theme_combo.findData(normalize_theme_name(theme))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(
            lambda _idx: self.themeChanged.emit(str(self.theme_combo.currentData() or "system"))
        )
        form.addRow("Theme:", self.theme_combo)

        self.density_combo = NoWheelComboBox()
        for density_value in UI_DENSITY_CHOICES:
            self.density_combo.addItem(UI_DENSITY_LABELS.get(density_value, density_value), density_value)
        density_idx = self.density_combo.findData(normalize_ui_density(ui_density))
        if density_idx >= 0:
            self.density_combo.setCurrentIndex(density_idx)
        self.density_combo.currentIndexChanged.connect(
            lambda _idx: self.uiDensityChanged.emit(str(self.density_combo.currentData() or "comfortable"))
        )
        form.addRow("Density:", self.density_combo)

        self.accent_mode_combo = NoWheelComboBox()
        for mode_value in ACCENT_MODE_CHOICES:
            self.accent_mode_combo.addItem(ACCENT_MODE_LABELS.get(mode_value, mode_value), mode_value)
        accent_mode_idx = self.accent_mode_combo.findData(normalize_accent_mode(ui_accent_mode))
        if accent_mode_idx >= 0:
            self.accent_mode_combo.setCurrentIndex(accent_mode_idx)
        self.accent_mode_combo.currentIndexChanged.connect(self._on_accent_mode_combo_changed)
        form.addRow("Accent source:", self.accent_mode_combo)

        self.accent_preset_combo = NoWheelComboBox()
        for preset_value in ACCENT_PRESET_CHOICES:
            self.accent_preset_combo.addItem(ACCENT_PRESET_LABELS.get(preset_value, preset_value), preset_value)
        accent_preset_idx = self.accent_preset_combo.findData(normalize_accent_preset(ui_accent_preset))
        if accent_preset_idx >= 0:
            self.accent_preset_combo.setCurrentIndex(accent_preset_idx)
        self.accent_preset_combo.currentIndexChanged.connect(self._on_accent_preset_combo_changed)
        form.addRow("Accent preset:", self.accent_preset_combo)

        accent_custom_row = QWidget()
        accent_custom_layout = QHBoxLayout(accent_custom_row)
        accent_custom_layout.setContentsMargins(0, 0, 0, 0)
        accent_custom_layout.setSpacing(8)
        self.accent_custom_preview = QLabel("      ")
        self.accent_custom_preview.setObjectName("ColorSwatchPreview")
        self.accent_custom_preview.setMinimumWidth(40)
        self.accent_custom_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        accent_custom_layout.addWidget(self.accent_custom_preview)
        self.accent_custom_value_label = QLabel("")
        self.accent_custom_value_label.setObjectName("FieldHint")
        accent_custom_layout.addWidget(self.accent_custom_value_label, 1)
        self.pick_accent_color_btn = QPushButton("Pick accent...")
        set_widget_role(self.pick_accent_color_btn, "ghost")
        self.pick_accent_color_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.pick_accent_color_btn.clicked.connect(self._pick_custom_accent)
        accent_custom_layout.addWidget(self.pick_accent_color_btn)
        form.addRow("Custom accent:", accent_custom_row)
        appearance_card.body_layout.addLayout(form)

        preview_host = QWidget()
        preview_layout = QGridLayout(preview_host)
        preview_layout.setContentsMargins(0, 2, 0, 0)
        preview_layout.setHorizontalSpacing(8)
        preview_layout.setVerticalSpacing(8)
        self.theme_preview_cards: dict[str, ThemePreviewCard] = {}
        for i, theme_value in enumerate(THEME_PRESET_CHOICES):
            card = ThemePreviewCard(theme_value, THEME_PRESET_LABELS.get(theme_value, theme_value))
            card.clicked.connect(self._on_theme_preview_clicked)
            self.theme_preview_cards[theme_value] = card
            preview_layout.addWidget(card, i // 2, i % 2)
        appearance_card.body_layout.addWidget(preview_host)

        self._accent_custom_color = normalize_accent_color(ui_accent_color)
        self._refresh_accent_controls()
        self.refresh_theme_previews()

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
        self.open_config_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_last_report_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.validate_schema_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
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
        self.tr_open_config_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.tr_open_logs_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.tr_open_last_report_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.verify_audio_deps_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.qt_plugin_check_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
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

        self.bucket_table = QTableWidget(0, 5)
        self.bucket_table.setHorizontalHeaderLabels(["Bucket ID", "Display Name", "Color", "IconIndex", "Preview"])
        self.bucket_table.setAlternatingRowColors(True)
        self.bucket_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bucket_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bucket_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.bucket_table.verticalHeader().setVisible(False)
        self.bucket_table.horizontalHeader().setStretchLastSection(False)
        self.bucket_table.setMinimumHeight(220)
        bucket_card.body_layout.addWidget(self.bucket_table)

        bucket_actions = QHBoxLayout()
        bucket_actions.setContentsMargins(0, 0, 0, 0)
        bucket_actions.setSpacing(8)
        self.pick_bucket_color_btn = QPushButton("Pick color for selected row")
        self.pick_bucket_icon_btn = QPushButton("Pick icon for selected row")
        self.reset_bucket_row_btn = QPushButton("Reset selected row")
        self.reset_bucket_all_btn = QPushButton("Reset all (loaded)")
        self.reload_bucket_custom_btn = QPushButton("Reload bucket customizations")
        self.save_bucket_custom_btn = QPushButton("Save bucket customizations")
        self.pick_bucket_color_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.pick_bucket_icon_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.reset_bucket_row_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserStop))
        self.reset_bucket_all_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserStop))
        self.reload_bucket_custom_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.save_bucket_custom_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        for btn in (
            self.pick_bucket_color_btn,
            self.pick_bucket_icon_btn,
            self.reset_bucket_row_btn,
            self.reset_bucket_all_btn,
            self.reload_bucket_custom_btn,
            self.save_bucket_custom_btn,
        ):
            set_widget_role(btn, "ghost")
            bucket_actions.addWidget(btn)
        bucket_actions.addStretch(1)
        bucket_card.body_layout.addLayout(bucket_actions)

        self.bucket_custom_status_label = QLabel("Bucket customization: not loaded yet")
        self.bucket_custom_status_label.setObjectName("FieldHint")
        self.bucket_custom_status_label.setWordWrap(True)
        bucket_card.body_layout.addWidget(self.bucket_custom_status_label)

        self._bucket_table_updating = False
        self._bucket_loaded_defaults: dict[str, dict[str, str]] = {}
        self.bucket_table.itemChanged.connect(self._on_bucket_table_item_changed)
        self.pick_bucket_color_btn.clicked.connect(self._pick_selected_bucket_color)
        self.pick_bucket_icon_btn.clicked.connect(self._pick_selected_bucket_icon)
        self.reset_bucket_row_btn.clicked.connect(self._reset_selected_bucket_row)
        self.reset_bucket_all_btn.clicked.connect(self._reset_all_bucket_rows)
        self.reload_bucket_custom_btn.clicked.connect(self.bucketCustomizationReloadRequested.emit)
        self.save_bucket_custom_btn.clicked.connect(self._emit_bucket_customization_save)

    def _on_dev_tools_toggled(self, checked: bool) -> None:
        self.dev_tools_panel.set_expanded(checked, animate=True)
        self.developerToolsChanged.emit(checked)

    def set_theme_value(self, theme: str) -> None:
        idx = self.theme_combo.findData(normalize_theme_name(theme))
        if idx < 0:
            return
        with QSignalBlocker(self.theme_combo):
            self.theme_combo.setCurrentIndex(idx)
        self.refresh_theme_previews()

    def set_ui_density_value(self, density: str) -> None:
        density = normalize_ui_density(density)
        idx = self.density_combo.findData(density)
        if idx >= 0:
            with QSignalBlocker(self.density_combo):
                self.density_combo.setCurrentIndex(idx)
        self.refresh_theme_previews()

    def set_accent_settings(self, mode: str, preset: str, color: str) -> None:
        mode = normalize_accent_mode(mode)
        preset = normalize_accent_preset(preset)
        color = normalize_accent_color(color)
        mode_idx = self.accent_mode_combo.findData(mode)
        if mode_idx >= 0:
            with QSignalBlocker(self.accent_mode_combo):
                self.accent_mode_combo.setCurrentIndex(mode_idx)
        preset_idx = self.accent_preset_combo.findData(preset)
        if preset_idx >= 0:
            with QSignalBlocker(self.accent_preset_combo):
                self.accent_preset_combo.setCurrentIndex(preset_idx)
        self._accent_custom_color = color
        self._refresh_accent_controls()
        self.refresh_theme_previews()

    def _on_theme_preview_clicked(self, theme_id: str) -> None:
        self.themeChanged.emit(str(theme_id or "system"))

    def _on_accent_mode_combo_changed(self, _idx: int) -> None:
        self._refresh_accent_controls()
        self.refresh_theme_previews()
        self.accentModeChanged.emit(str(self.accent_mode_combo.currentData() or "theme_default"))

    def _on_accent_preset_combo_changed(self, _idx: int) -> None:
        self.refresh_theme_previews()
        self.accentPresetChanged.emit(str(self.accent_preset_combo.currentData() or "cyan"))

    def _pick_custom_accent(self) -> None:
        current = QColor(self._accent_custom_color or "#56C8FF")
        chosen = QColorDialog.getColor(current, self, "Select Accent Color")
        if not chosen.isValid():
            return
        self._accent_custom_color = chosen.name().upper()
        self._refresh_accent_controls()
        self.refresh_theme_previews()
        self.accentColorChanged.emit(self._accent_custom_color)

    def _refresh_accent_controls(self) -> None:
        mode = normalize_accent_mode(str(self.accent_mode_combo.currentData() or "theme_default"))
        self.accent_preset_combo.setEnabled(mode == "preset")
        self.pick_accent_color_btn.setEnabled(mode == "custom")
        color_text = normalize_accent_color(self._accent_custom_color)
        if not color_text:
            self.accent_custom_value_label.setText("No custom color selected")
            self.accent_custom_preview.setStyleSheet("")
            self.accent_custom_preview.setText("      ")
        else:
            self.accent_custom_value_label.setText(color_text)
            fg = "#0F172A" if QColor(color_text).lightness() > 150 else "#F8FAFC"
            self.accent_custom_preview.setText("")
            self.accent_custom_preview.setStyleSheet(
                f"background:{color_text}; border:1px solid rgba(0,0,0,0.18); border-radius:6px; color:{fg};"
            )

    def refresh_theme_previews(self) -> None:
        density = str(self.density_combo.currentData() or "comfortable")
        accent_mode = str(self.accent_mode_combo.currentData() or "theme_default")
        accent_preset = str(self.accent_preset_combo.currentData() or "cyan")
        accent_color = self._accent_custom_color
        theme_selected = str(self.theme_combo.currentData() or "system")
        density_label = UI_DENSITY_LABELS.get(normalize_ui_density(density), density.title())
        from PySide6.QtWidgets import QApplication

        qapp = QApplication.instance()
        for theme_id, card in self.theme_preview_cards.items():
            card.apply_density(density)
            card.set_density_text(density_label)
            card.set_selected(theme_id == theme_selected)
            card.setStyleSheet(
                build_theme_preview_card_style(
                    theme_id,
                    density=density,
                    accent_mode=accent_mode,
                    accent_preset=accent_preset,
                    accent_color=accent_color,
                    selected=(theme_id == theme_selected),
                    app=qapp if isinstance(qapp, QApplication) else None,
                )
            )

    def apply_density(self, density: str) -> None:  # type: ignore[override]
        super().apply_density(density)
        compact = normalize_ui_density(density) == "compact"
        row_height = 26 if compact else 32
        self.bucket_table.verticalHeader().setDefaultSectionSize(row_height)
        if hasattr(self, "theme_preview_cards"):
            for card in self.theme_preview_cards.values():
                card.apply_density(density)
                card.set_density_text(UI_DENSITY_LABELS.get(normalize_ui_density(density), density.title()))
        self.refresh_theme_previews()

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
            self._bucket_loaded_defaults = {}
            for row, bucket_id in enumerate(bucket_ids):
                display_name = str((bucket_names or {}).get(bucket_id, bucket_id) or bucket_id)
                style = dict((bucket_styles or {}).get(bucket_id) or {})
                color_text = str(style.get("Color", "$7F7F7F") or "$7F7F7F")
                icon_value = style.get("IconIndex", 0)
                icon_text = str(icon_value if icon_value is not None else 0)
                self._bucket_loaded_defaults[str(bucket_id)] = {
                    "display_name": display_name,
                    "color": color_text,
                    "icon": icon_text,
                }

                id_item = QTableWidgetItem(bucket_id)
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.bucket_table.setItem(row, 0, id_item)

                self.bucket_table.setItem(row, 1, QTableWidgetItem(display_name))
                self.bucket_table.setItem(row, 2, QTableWidgetItem(color_text))
                self.bucket_table.setItem(row, 3, QTableWidgetItem(icon_text))
                preview_item = QTableWidgetItem("")
                preview_item.setFlags(preview_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.bucket_table.setItem(row, 4, preview_item)
                self._refresh_bucket_color_cell(row)
                self._refresh_bucket_icon_preview_cell(row)
        finally:
            self._bucket_table_updating = False

        self.bucket_table.resizeColumnsToContents()
        self.bucket_table.horizontalHeader().setStretchLastSection(False)
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
        elif item.column() == 3:
            self._refresh_bucket_icon_preview_cell(item.row())

    def _refresh_bucket_color_cell(self, row: int) -> None:
        item = self.bucket_table.item(row, 2)
        if item is None:
            return
        color = self._qcolor_from_text(item.text())
        if color is None:
            item.setBackground(QColor())
            return
        item.setBackground(color)
        item.setForeground(QColor("#0F172A") if color.lightness() > 150 else QColor("#F8FAFC"))

    def _refresh_bucket_icon_preview_cell(self, row: int) -> None:
        icon_item = self.bucket_table.item(row, 3)
        preview_item = self.bucket_table.item(row, 4)
        if preview_item is None:
            preview_item = QTableWidgetItem("")
            preview_item.setFlags(preview_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.bucket_table.setItem(row, 4, preview_item)

        if icon_item is None:
            preview_item.setText("")
            preview_item.setToolTip("")
            return

        raw = (icon_item.text() or "").strip()
        icon_index = self._parse_icon_index_preview(raw)
        if icon_index is None:
            preview_item.setText("Invalid")
            preview_item.setForeground(QColor("#D97706"))
            preview_item.setToolTip("Invalid IconIndex format")
            return

        glyph = ""
        try:
            if 0 <= icon_index <= 0x10FFFF:
                glyph = chr(icon_index)
        except Exception:
            glyph = ""
        preview_item.setText(f"{glyph}  U+{icon_index:04X}" if glyph else f"U+{icon_index:04X}")
        preview_item.setToolTip(f"IconIndex preview: {raw} -> U+{icon_index:04X}")
        preview_item.setForeground(QColor())

    def _parse_icon_index_preview(self, value: str) -> Optional[int]:
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
            return int(text, base)
        except ValueError:
            return None

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

    def _pick_selected_bucket_icon(self) -> None:
        row = self.bucket_table.currentRow()
        if row < 0:
            self.set_bucket_customization_status("Select a bucket row first to pick an icon.", success=False)
            return
        icon_item = self.bucket_table.item(row, 3)
        current = icon_item.text().strip() if icon_item else ""
        dlg = IconPickerDialog(current_value=current, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        icon_index = dlg.selected_icon_index()
        if icon_index is None:
            self.set_bucket_customization_status("No icon selected.", success=False)
            return
        self._bucket_table_updating = True
        try:
            self._set_table_cell_text(row, 3, str(icon_index))
            self._refresh_bucket_icon_preview_cell(row)
        finally:
            self._bucket_table_updating = False
        self.set_bucket_customization_status("Selected icon updated. Save to persist changes.", success=True)

    def _reset_selected_bucket_row(self) -> None:
        row = self.bucket_table.currentRow()
        if row < 0:
            self.set_bucket_customization_status("Select a bucket row first to reset it.", success=False)
            return
        bucket_item = self.bucket_table.item(row, 0)
        bucket_id = (bucket_item.text().strip() if bucket_item else "").strip()
        if not bucket_id:
            self.set_bucket_customization_status("Selected row does not contain a valid bucket ID.", success=False)
            return
        defaults = self._bucket_loaded_defaults.get(bucket_id)
        if not defaults:
            self.set_bucket_customization_status(f"No loaded defaults found for '{bucket_id}'.", success=False)
            return
        self._bucket_table_updating = True
        try:
            self._set_table_cell_text(row, 1, defaults.get("display_name", bucket_id))
            self._set_table_cell_text(row, 2, defaults.get("color", "$7F7F7F"))
            self._set_table_cell_text(row, 3, defaults.get("icon", "0"))
            self._refresh_bucket_color_cell(row)
            self._refresh_bucket_icon_preview_cell(row)
        finally:
            self._bucket_table_updating = False
        self.set_bucket_customization_status(f"Reset '{bucket_id}' to loaded values. Save to persist.", success=True)

    def _reset_all_bucket_rows(self) -> None:
        if not self._bucket_loaded_defaults:
            self.set_bucket_customization_status("No loaded values available. Reload first.", success=False)
            return
        self._bucket_table_updating = True
        try:
            for row in range(self.bucket_table.rowCount()):
                bucket_item = self.bucket_table.item(row, 0)
                bucket_id = (bucket_item.text().strip() if bucket_item else "").strip()
                defaults = self._bucket_loaded_defaults.get(bucket_id)
                if not defaults:
                    continue
                self._set_table_cell_text(row, 1, defaults.get("display_name", bucket_id))
                self._set_table_cell_text(row, 2, defaults.get("color", "$7F7F7F"))
                self._set_table_cell_text(row, 3, defaults.get("icon", "0"))
                self._refresh_bucket_color_cell(row)
                self._refresh_bucket_icon_preview_cell(row)
        finally:
            self._bucket_table_updating = False
        self.set_bucket_customization_status("Reset all rows to loaded values. Save to persist.", success=True)

    def _set_table_cell_text(self, row: int, col: int, text: str) -> None:
        item = self.bucket_table.item(row, col)
        if item is None:
            item = QTableWidgetItem(text)
            self.bucket_table.setItem(row, col, item)
        else:
            item.setText(text)

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
