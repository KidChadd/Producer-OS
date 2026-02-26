from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import NoWheelComboBox, StatChip, StatusBadge, repolish, set_widget_role

_TOKEN_SPLIT_RE = re.compile(r"[ _-]+")
_REVIEW_WIDGET_THRESHOLD = 500

_PHASE_LABELS: list[tuple[str, str]] = [
    ("scan", "Scanning"),
    ("classify", "Classifying"),
    ("route", "Routing"),
    ("write", "Writing"),
]


class _BucketBadgeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore[override]
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = str(opt.text or "")
        draw_text = text.removeprefix("\u25cf ").strip()
        fg = opt.palette.text().color()
        if opt.palette is not None:
            fg = opt.palette.text().color()
        custom_fg = index.data(Qt.ItemDataRole.ForegroundRole)
        if isinstance(custom_fg, QColor):
            fg = custom_fg
        elif hasattr(custom_fg, "color"):
            try:
                fg = custom_fg.color()
            except Exception:
                pass

        style = opt.widget.style() if opt.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, opt.widget)

        painter.save()
        rect = opt.rect.adjusted(8, 2, -6, -2)
        dot_size = 8
        dot_y = rect.center().y() - dot_size // 2
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fg)
        painter.drawEllipse(rect.left(), dot_y, dot_size, dot_size)
        painter.setPen(QPen(opt.palette.text().color()))
        text_rect = rect.adjusted(dot_size + 8, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, draw_text)
        painter.restore()


class _ConfidenceChipDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore[override]
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, opt.widget)

        bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        fg_brush = index.data(Qt.ItemDataRole.ForegroundRole)
        bg = QColor(80, 80, 80, 40)
        fg = opt.palette.text().color()
        try:
            if hasattr(bg_brush, "color"):
                bg = bg_brush.color()
            if hasattr(fg_brush, "color"):
                fg = fg_brush.color()
        except Exception:
            pass

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        chip_rect = opt.rect.adjusted(6, 4, -6, -4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(chip_rect, 8, 8)
        painter.setPen(QPen(fg))
        painter.drawText(chip_rect, Qt.AlignmentFlag.AlignCenter, str(index.data() or ""))
        painter.restore()


class _Top3BadgeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore[override]
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, opt.widget)
        text = str(index.data() or "")
        parts = [p for p in text.split("] ") if p]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        x = opt.rect.left() + 6
        y = opt.rect.top() + 4
        max_right = opt.rect.right() - 6
        fm = painter.fontMetrics()
        for i, raw in enumerate(parts[:3]):
            part = raw if raw.endswith("]") else f"{raw}]"
            w = fm.horizontalAdvance(part) + 12
            h = max(18, fm.height() + 4)
            if x + w > max_right:
                ellipsis = "..."
                painter.setPen(QPen(opt.palette.mid().color()))
                painter.drawText(opt.rect.adjusted(x - opt.rect.left(), 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, ellipsis)
                break
            rect = option.rect.adjusted(x - option.rect.left(), y - option.rect.top(), 0, 0)
            rect.setWidth(w)
            rect.setHeight(h)
            painter.setPen(QPen(opt.palette.mid().color()))
            painter.setBrush(QColor(255, 255, 255, 0))
            painter.drawRoundedRect(rect, 7, 7)
            painter.setPen(QPen(opt.palette.text().color()))
            painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, part)
            x += w + 6
        painter.restore()


class RunPage(BaseWizardPage):
    analyzeRequested = Signal()
    runRequested = Signal()
    saveReportRequested = Signal()
    hintSaveRequested = Signal(str, str, str, str)  # source, kind(filename|folder), bucket, token

    def __init__(self, action: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            "Step 4 - Run & Review",
            "Analyze or execute routing, then inspect the results, review low-confidence items, and export the run report.",
            parent,
        )
        self._action_name = action
        self._report: dict[str, Any] = {}
        self._rows_all: list[dict[str, Any]] = []
        self._row_index_by_source: dict[str, dict[str, Any]] = {}
        self._bucket_choices: list[str] = []
        self._manual_overrides: dict[str, dict[str, Any]] = {}
        self._saved_hints: list[dict[str, Any]] = []
        self._preview_stale = False
        self._has_live_logs = False
        self._review_table_widget_mode = True
        self._bucket_color_map: dict[str, str] = {}
        self._timeline_labels: list[QLabel] = []
        self._timeline_phase_keys: list[str] = []
        self._phase_progress: dict[str, dict[str, Any]] = {}
        self._active_mode: str | None = None
        self._reset_phase_progress()

        action_card = self.add_card("Execution Controls", "Run an analysis first to verify routing before moving files.")
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        self.analyze_btn = QPushButton("Analyze")
        set_widget_role(self.analyze_btn, "ghost")
        self.analyze_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.analyze_btn.clicked.connect(self.analyzeRequested.emit)
        action_row.addWidget(self.analyze_btn)

        self.run_btn = QPushButton(self._run_button_label(action))
        set_widget_role(self.run_btn, "primary")
        self.run_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.run_btn.clicked.connect(self.runRequested.emit)
        action_row.addWidget(self.run_btn)
        action_row.addStretch(1)

        self.status_badge = StatusBadge("Ready")
        action_row.addWidget(self.status_badge)
        action_card.body_layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        action_card.body_layout.addWidget(self.progress_bar)

        review_card = self.add_card("Results Review", "Summary, pack breakdown, and low-confidence review queue.")
        self.tabs = QTabWidget()
        review_card.body_layout.addWidget(self.tabs)

        self._build_summary_tab()
        self._build_review_tab()
        self._build_preview_tab()

        export_card = self.add_card("Report Export")
        export_row = QHBoxLayout()
        export_row.setContentsMargins(0, 0, 0, 0)
        export_row.setSpacing(8)
        self.save_report_btn = QPushButton("Save run report...")
        set_widget_role(self.save_report_btn, "ghost")
        self.save_report_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_report_btn.setVisible(False)
        self.save_report_btn.clicked.connect(self.saveReportRequested.emit)
        export_row.addWidget(self.save_report_btn)

        self.review_feedback_label = QLabel("")
        self.review_feedback_label.setObjectName("MutedLabel")
        self.review_feedback_label.setWordWrap(True)
        export_row.addWidget(self.review_feedback_label, 1)
        export_card.body_layout.addLayout(export_row)

    # ------------------------------------------------------------------
    # UI construction
    def _build_summary_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.timeline_row = QHBoxLayout()
        self.timeline_row.setContentsMargins(0, 0, 0, 0)
        self.timeline_row.setSpacing(8)
        for phase_key, phase_label in _PHASE_LABELS:
            chip = QLabel(phase_label)
            chip.setObjectName("TimelineStep")
            chip.setProperty("state", "pending")
            chip.setProperty("phaseKey", phase_key)
            chip.setToolTip(phase_label)
            self.timeline_row.addWidget(chip)
            self._timeline_labels.append(chip)
            self._timeline_phase_keys.append(phase_key)
        self.timeline_row.addStretch(1)
        layout.addLayout(self.timeline_row)

        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(10)
        self.processed_chip = StatChip("Processed", "0")
        self.moved_chip = StatChip("Moved", "0")
        self.copied_chip = StatChip("Copied", "0")
        self.unsorted_chip = StatChip("Unsorted", "0")
        for chip in (self.processed_chip, self.moved_chip, self.copied_chip, self.unsorted_chip):
            stats.addWidget(chip)
        layout.addLayout(stats)

        self.summary_label = QLabel("No results yet.")
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.run_legend_label = QLabel(
            "Confidence: high (green), medium (blue), low (amber). Top-3 candidates are shown as compact tags."
        )
        self.run_legend_label.setObjectName("FieldHint")
        self.run_legend_label.setWordWrap(True)
        layout.addWidget(self.run_legend_label)

        self.log_edit = QTextEdit()
        self.log_edit.setObjectName("LogOutput")
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(240)
        layout.addWidget(self.log_edit, 1)

        self.tabs.addTab(tab, "Summary")

    def _build_review_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        self.review_search = QLineEdit()
        self.review_search.setPlaceholderText("Filter by file, pack, bucket, or token...")
        self.review_search.textChanged.connect(self._apply_review_filters)
        filter_row.addWidget(self.review_search, 1)

        self.review_bucket_filter = NoWheelComboBox()
        self.review_bucket_filter.addItem("All buckets")
        self.review_bucket_filter.currentTextChanged.connect(self._apply_review_filters)
        filter_row.addWidget(self.review_bucket_filter)

        self.review_pack_filter = NoWheelComboBox()
        self.review_pack_filter.addItem("All packs")
        self.review_pack_filter.currentTextChanged.connect(self._apply_review_filters)
        filter_row.addWidget(self.review_pack_filter)

        self.review_low_only = QCheckBox("Low confidence only")
        self.review_low_only.setChecked(True)
        self.review_low_only.toggled.connect(self._apply_review_filters)
        filter_row.addWidget(self.review_low_only)
        layout.addLayout(filter_row)

        self.review_count_label = QLabel("No review rows.")
        self.review_count_label.setObjectName("MutedLabel")
        self.review_count_label.setWordWrap(True)
        layout.addWidget(self.review_count_label)

        self.review_filter_hint_label = QLabel(
            "Tip: bucket/pack filters narrow the review queue and re-enable inline override controls on large audits."
        )
        self.review_filter_hint_label.setObjectName("FieldHint")
        self.review_filter_hint_label.setWordWrap(True)
        layout.addWidget(self.review_filter_hint_label)

        self.review_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.review_splitter.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.review_table = QTableWidget(0, 8)
        self.review_table.setHorizontalHeaderLabels(
            ["Pack", "File", "Chosen", "Confidence", "Margin", "Top 3", "Override", "Hint Action"]
        )
        self.review_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.review_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.review_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.review_table.setAlternatingRowColors(True)
        # Sorting a QTableWidget with thousands of rows plus per-row cell widgets
        # (combo boxes/buttons) is unstable and very slow on Windows. Keep review
        # filtering fast/stable and leave sorting disabled here.
        self.review_table.setSortingEnabled(False)
        header = self.review_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, header.ResizeMode.Stretch)
        header.setSectionResizeMode(6, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, header.ResizeMode.ResizeToContents)
        self.review_table.itemSelectionChanged.connect(self._update_review_details)
        left_layout.addWidget(self.review_table, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.review_selected_file_label = QLabel("Select a row to inspect details.")
        self.review_selected_file_label.setObjectName("SectionTitle")
        self.review_selected_file_label.setWordWrap(True)
        right_layout.addWidget(self.review_selected_file_label)

        self.review_selected_meta_label = QLabel("")
        self.review_selected_meta_label.setObjectName("FieldHint")
        self.review_selected_meta_label.setWordWrap(True)
        right_layout.addWidget(self.review_selected_meta_label)

        detail_controls = QHBoxLayout()
        detail_controls.setContentsMargins(0, 0, 0, 0)
        detail_controls.setSpacing(6)
        self.review_detail_override_combo = NoWheelComboBox()
        self.review_detail_override_combo.setEnabled(False)
        self.review_detail_override_combo.currentTextChanged.connect(self._on_detail_override_changed)
        detail_controls.addWidget(self.review_detail_override_combo, 1)
        self.review_detail_filename_hint_btn = QPushButton("Add filename hint…")
        set_widget_role(self.review_detail_filename_hint_btn, "ghost")
        self.review_detail_filename_hint_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.review_detail_filename_hint_btn.setEnabled(False)
        self.review_detail_filename_hint_btn.clicked.connect(lambda: self._open_selected_hint_menu("filename"))
        detail_controls.addWidget(self.review_detail_filename_hint_btn)
        self.review_detail_folder_hint_btn = QPushButton("Add folder hint…")
        set_widget_role(self.review_detail_folder_hint_btn, "ghost")
        self.review_detail_folder_hint_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.review_detail_folder_hint_btn.setEnabled(False)
        self.review_detail_folder_hint_btn.clicked.connect(lambda: self._open_selected_hint_menu("folder"))
        detail_controls.addWidget(self.review_detail_folder_hint_btn)
        right_layout.addLayout(detail_controls)

        self.review_details = QTextEdit()
        self.review_details.setObjectName("LogOutput")
        self.review_details.setReadOnly(True)
        self.review_details.setMinimumHeight(180)
        right_layout.addWidget(self.review_details, 1)

        self.review_splitter.addWidget(left_panel)
        self.review_splitter.addWidget(right_panel)
        self.review_splitter.setStretchFactor(0, 3)
        self.review_splitter.setStretchFactor(1, 2)
        self.review_splitter.setSizes([760, 360])
        layout.addWidget(self.review_splitter, 1)

        self._review_bucket_delegate = _BucketBadgeDelegate(self.review_table)
        self._review_conf_delegate = _ConfidenceChipDelegate(self.review_table)
        self._review_top3_delegate = _Top3BadgeDelegate(self.review_table)
        self.review_table.setItemDelegateForColumn(2, self._review_bucket_delegate)
        self.review_table.setItemDelegateForColumn(3, self._review_conf_delegate)
        self.review_table.setItemDelegateForColumn(5, self._review_top3_delegate)

        self.tabs.addTab(tab, "Low Confidence Review")

    def _build_preview_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.preview_stale_label = QLabel("Preview reflects the latest analyze/dry-run report.")
        self.preview_stale_label.setObjectName("MutedLabel")
        self.preview_stale_label.setWordWrap(True)
        layout.addWidget(self.preview_stale_label)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        self.preview_search = QLineEdit()
        self.preview_search.setPlaceholderText("Filter preview by file, pack, bucket, destination...")
        self.preview_search.textChanged.connect(self._apply_preview_filters)
        filter_row.addWidget(self.preview_search, 1)

        self.preview_bucket_filter = NoWheelComboBox()
        self.preview_bucket_filter.addItem("All buckets")
        self.preview_bucket_filter.currentTextChanged.connect(self._apply_preview_filters)
        filter_row.addWidget(self.preview_bucket_filter)

        self.preview_pack_filter = NoWheelComboBox()
        self.preview_pack_filter.addItem("All packs")
        self.preview_pack_filter.currentTextChanged.connect(self._apply_preview_filters)
        filter_row.addWidget(self.preview_pack_filter)

        self.preview_low_only = QCheckBox("Low confidence only")
        self.preview_low_only.setChecked(False)
        self.preview_low_only.toggled.connect(self._apply_preview_filters)
        filter_row.addWidget(self.preview_low_only)

        self.preview_changed_only = QCheckBox("Changed by user only")
        self.preview_changed_only.setChecked(False)
        self.preview_changed_only.toggled.connect(self._apply_preview_filters)
        filter_row.addWidget(self.preview_changed_only)
        layout.addLayout(filter_row)

        self.preview_table = QTableWidget(0, 8)
        self.preview_table.setHorizontalHeaderLabels(
            ["Pack", "File", "Bucket", "Category", "Action", "Low?", "Destination Preview", "Source"]
        )
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSortingEnabled(True)
        header = self.preview_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, header.ResizeMode.Stretch)
        header.setSectionResizeMode(7, header.ResizeMode.Stretch)
        layout.addWidget(self.preview_table, 1)

        self._preview_bucket_delegate = _BucketBadgeDelegate(self.preview_table)
        self.preview_table.setItemDelegateForColumn(2, self._preview_bucket_delegate)

        self.tabs.addTab(tab, "Apply Preview")

    # ------------------------------------------------------------------
    # Public page API
    def _run_button_label(self, action: str) -> str:
        action = action.lower().strip()
        return "Run (Move)" if action == "move" else "Run (Copy)"

    def set_action(self, action: str) -> None:
        self._action_name = action
        self.run_btn.setText(self._run_button_label(action))

    def set_busy(self, busy: bool, mode: str | None = None) -> None:
        self._active_mode = mode if busy else None
        self.analyze_btn.setEnabled(not busy)
        self.run_btn.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        self.progress_bar.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress_bar.setValue(0)
            self.status_badge.set_status("Ready", kind="neutral", pulsing=False)
            if not self._report:
                self._reset_phase_progress()
                self._refresh_timeline_labels()
                self._set_timeline_state(active_index=None, completed_upto=None)
            self._update_preview_stale_state()
            return
        self._reset_phase_progress()
        self._refresh_timeline_labels()
        if mode == "analyze":
            self.status_badge.set_status("Analyzing", kind="analyzing", pulsing=True)
        else:
            self.status_badge.set_status("Running", kind="running", pulsing=True)
        self._set_timeline_state(active_index=0, completed_upto=-1)

    def clear_results(self) -> None:
        for chip in (self.processed_chip, self.moved_chip, self.copied_chip, self.unsorted_chip):
            chip.set_value("0")
        self.summary_label.setText("Working...")
        self.log_edit.clear()
        self.review_details.clear()
        self.review_count_label.setText("No review rows.")
        self.review_table.setRowCount(0)
        self.preview_table.setRowCount(0)
        self._report = {}
        self._rows_all = []
        self._row_index_by_source = {}
        self._manual_overrides = {}
        self._saved_hints = []
        self._preview_stale = False
        self._has_live_logs = False
        self._reset_phase_progress()
        self.review_feedback_label.setText("")
        self.save_report_btn.setVisible(False)
        self.status_badge.set_status("Working", kind="running", pulsing=True)
        self.preview_stale_label.setText("Preview reflects the latest analyze/dry-run report.")
        self.review_details.setPlainText("No review rows available yet. Run Analyze to populate the review queue.")
        self._refresh_timeline_labels()
        self._set_timeline_state(active_index=0, completed_upto=-1)

    def append_log_line(self, line: str) -> None:
        text = str(line or "").rstrip("\r\n")
        if not text:
            return
        self.log_edit.append(text)
        self._has_live_logs = True
        self._advance_timeline_from_log(text)

    def set_results(
        self,
        report: dict,
        log_lines: list[str],
        bucket_choices: Optional[list[str]] = None,
        bucket_colors: Optional[dict[str, str]] = None,
    ) -> None:
        self._report = dict(report or {})
        self._bucket_color_map = {str(k): str(v) for k, v in (bucket_colors or {}).items()}
        self.processed_chip.set_value(str(self._report.get("files_processed", 0)))
        self.moved_chip.set_value(str(self._report.get("files_moved", 0)))
        self.copied_chip.set_value(str(self._report.get("files_copied", 0)))
        self.unsorted_chip.set_value(str(self._report.get("unsorted", 0)))

        self._rows_all = self._flatten_rows(self._report)
        self._row_index_by_source = {str(row.get("source", "")): row for row in self._rows_all}

        self._bucket_choices = sorted(
            set(bucket_choices or [])
            | {str(row.get("chosen_bucket", "")) for row in self._rows_all if row.get("chosen_bucket")}
            | {
                str(c.get("bucket"))
                for row in self._rows_all
                for c in (row.get("top_3_candidates") or [])
                if isinstance(c, dict) and c.get("bucket")
            }
        )
        self._refresh_bucket_filter()
        self._refresh_pack_filters()

        self._update_summary_label()
        if not self._has_live_logs:
            self._rebuild_pack_breakdown()
        self._apply_review_filters()
        self._apply_preview_filters()
        self._update_preview_stale_state()
        self.save_report_btn.setVisible(True)
        self.status_badge.set_status("Completed", kind="success", pulsing=False)
        self._phase_progress["classify"].update(
            {"event": "done", "files_done": int(self._report.get("files_processed", 0) or 0)}
        )
        self._phase_progress["route"].update(
            {
                "event": "done",
                "moved": int(self._report.get("files_moved", 0) or 0),
                "copied": int(self._report.get("files_copied", 0) or 0),
                "unsorted": int(self._report.get("unsorted", 0) or 0),
            }
        )
        self._phase_progress["write"].update({"event": "done", "message": "Completed"})
        self._refresh_timeline_labels()
        self._set_timeline_state(active_index=None, completed_upto=len(self._timeline_labels) - 1)

    def get_manual_review_overlay(self) -> dict[str, Any]:
        if not self._manual_overrides and not self._saved_hints:
            return {}
        return {
            "version": 1,
            "overrides": sorted(
                self._manual_overrides.values(),
                key=lambda row: (str(row.get("source", "")), str(row.get("override_bucket", ""))),
            ),
            "saved_hints": list(self._saved_hints),
        }

    def set_review_feedback(self, message: str, success: bool = True) -> None:
        self.review_feedback_label.setText(message)
        self.review_feedback_label.setProperty("state", "success" if success else "warning")
        repolish(self.review_feedback_label)

    def record_saved_hint(self, source: str, kind: str, bucket: str, token: str) -> None:
        entry = {
            "kind": kind,
            "bucket": bucket,
            "token": token,
            "source": source,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        if any(
            h.get("kind") == kind and h.get("bucket") == bucket and h.get("token") == token and h.get("source") == source
            for h in self._saved_hints
        ):
            return
        self._saved_hints.append(entry)
        self._preview_stale = True
        self._apply_preview_filters()
        self._update_summary_label()
        self._update_preview_stale_state()

    # ------------------------------------------------------------------
    # Timeline / visual helpers
    def _set_timeline_state(self, active_index: int | None, completed_upto: int | None) -> None:
        if not self._timeline_labels:
            return
        for idx, label in enumerate(self._timeline_labels):
            if completed_upto is None and active_index is None:
                state = "pending"
            elif completed_upto is not None and idx <= completed_upto:
                state = "done"
            elif active_index is not None and idx == active_index:
                state = "active"
            else:
                state = "pending"
            if label.property("state") != state:
                label.setProperty("state", state)
                repolish(label)
        self._refresh_timeline_labels()

    def _advance_timeline_from_log(self, text: str) -> None:
        if not self._timeline_labels:
            return
        lower = text.strip().lower()
        if not lower:
            return
        if "processing pack:" in lower:
            self._set_timeline_state(active_index=1, completed_upto=0)
            return
        if "finished pack:" in lower:
            if (self._active_mode or "").lower() == "analyze":
                self._set_timeline_state(active_index=1, completed_upto=1)
            else:
                self._set_timeline_state(active_index=2, completed_upto=1)
            return
        if "run_report.json" in lower or "feature_cache" in lower:
            self._set_timeline_state(active_index=3, completed_upto=2)

    def _reset_phase_progress(self) -> None:
        self._phase_progress = {
            phase: {
                "phase": phase,
                "event": "pending",
                "packs_total": 0,
                "packs_done": 0,
                "files_total": 0,
                "files_done": 0,
                "moved": 0,
                "copied": 0,
                "unsorted": 0,
                "message": "",
            }
            for phase, _ in _PHASE_LABELS
        }

    def _format_timeline_suffix(self, phase: str) -> str:
        info = self._phase_progress.get(phase) or {}
        event = str(info.get("event", "pending") or "pending")
        packs_total = int(info.get("packs_total", 0) or 0)
        packs_done = int(info.get("packs_done", 0) or 0)
        files_total = int(info.get("files_total", 0) or 0)
        files_done = int(info.get("files_done", 0) or 0)

        if phase == "scan":
            if packs_total:
                return f" · {packs_done}/{packs_total}"
            if event == "done":
                return " · done"
            return ""

        if phase == "classify":
            if files_total:
                return f" · {files_done}/{files_total}"
            if files_done:
                return f" · {files_done}"
            if packs_total:
                return f" · packs {packs_done}/{packs_total}"
            if event == "done":
                return " · done"
            return ""

        if phase == "route":
            moved = int(info.get("moved", 0) or 0)
            copied = int(info.get("copied", 0) or 0)
            unsorted = int(info.get("unsorted", 0) or 0)
            if moved or copied or unsorted or event == "done":
                return f" · M{moved} C{copied} U{unsorted}"
            return ""

        if phase == "write":
            message = str(info.get("message", "") or "").strip()
            if message:
                return f" · {message}"
            if event == "done":
                return " · done"
            return ""

        return ""

    def _refresh_timeline_labels(self) -> None:
        if not self._timeline_labels:
            return
        label_map = {phase: label for phase, label in zip(self._timeline_phase_keys, self._timeline_labels)}
        for phase_key, phase_label in _PHASE_LABELS:
            label = label_map.get(phase_key)
            if label is None:
                continue
            text = f"{phase_label}{self._format_timeline_suffix(phase_key)}"
            if label.text() != text:
                label.setText(text)

    def update_progress_event(self, payload: dict[str, Any]) -> None:
        phase = str((payload or {}).get("phase") or "").strip().lower()
        event = str((payload or {}).get("event") or "").strip().lower()
        if phase not in {p for p, _ in _PHASE_LABELS} or not event:
            return

        info = self._phase_progress.setdefault(phase, {})
        info.update({k: v for k, v in dict(payload or {}).items() if k != "phase"})
        info["phase"] = phase
        info["event"] = event
        self._refresh_timeline_labels()

        idx_map = {key: idx for idx, key in enumerate(self._timeline_phase_keys)}
        idx = idx_map.get(phase)
        if idx is None:
            return
        if event in {"start", "progress"}:
            self._set_timeline_state(active_index=idx, completed_upto=idx - 1)
            return
        if event == "done":
            if idx >= len(self._timeline_labels) - 1:
                self._set_timeline_state(active_index=None, completed_upto=idx)
            else:
                self._set_timeline_state(active_index=idx + 1, completed_upto=idx)

    def apply_density(self, density: str) -> None:
        super().apply_density(density)
        compact = str(density).strip().lower() == "compact"
        row_h = 26 if compact else 30
        for table in (self.review_table, self.preview_table):
            try:
                table.verticalHeader().setDefaultSectionSize(row_h)
                table.setIconSize(table.iconSize())  # force style refresh on some platforms
            except Exception:
                pass
        try:
            self.log_edit.setMinimumHeight(200 if compact else 240)
            self.review_details.setMinimumHeight(150 if compact else 180)
        except Exception:
            pass

    def _qcolor_from_style_text(self, value: str) -> Optional[QColor]:
        text = (value or "").strip()
        if not text:
            return None
        if text.startswith("$"):
            text = "#" + text[1:]
        elif not text.startswith("#"):
            text = "#" + text
        color = QColor(text)
        return color if color.isValid() else None

    def _bucket_color(self, bucket: str) -> Optional[QColor]:
        return self._qcolor_from_style_text(self._bucket_color_map.get(str(bucket), ""))

    def _apply_bucket_label_style(self, item: QTableWidgetItem, bucket: str) -> None:
        color = self._bucket_color(bucket)
        if color is None:
            item.setText(str(bucket))
            return
        item.setText(f"\u25cf {bucket}")
        item.setForeground(color)
        item.setToolTip(f"{bucket} ({self._bucket_color_map.get(bucket, '')})")

    def _style_confidence_item(self, item: QTableWidgetItem, ratio: float, low_confidence: bool) -> None:
        ratio = float(ratio or 0.0)
        if low_confidence or ratio < 0.50:
            label = "LOW"
            bg = QColor(245, 158, 66, 38)
            fg = QColor(235, 144, 33)
        elif ratio < 0.80:
            label = "MED"
            bg = QColor(86, 200, 255, 34)
            fg = QColor(86, 200, 255)
        else:
            label = "HIGH"
            bg = QColor(49, 208, 170, 34)
            fg = QColor(49, 208, 170)
        item.setText(f"{label} {ratio:.3f}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setBackground(bg)
        item.setForeground(fg)

    def _style_margin_item(self, item: QTableWidgetItem) -> None:
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def _top3_compact_text(self, row: dict[str, Any]) -> str:
        parts: list[str] = []
        for c in row.get("top_3_candidates", []) or []:
            if not isinstance(c, dict):
                continue
            bucket = str(c.get("bucket") or "")
            score = float(c.get("score", 0.0) or 0.0)
            if not bucket:
                continue
            parts.append(f"[{bucket} {score:.0f}]")
        return " ".join(parts)

    def _style_top3_item(self, item: QTableWidgetItem, row: dict[str, Any]) -> None:
        item.setText(self._top3_compact_text(row))
        item.setToolTip(self._top3_text(row) or "No candidate scores")

    def _apply_low_conf_tint_to_item(self, item: Optional[QTableWidgetItem]) -> None:
        if item is None:
            return
        item.setBackground(QColor(245, 158, 66, 18))

    # ------------------------------------------------------------------
    # Review row handling
    def _flatten_rows(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for pack in report.get("packs", []) or []:
            pack_name = str((pack or {}).get("pack", ""))
            for f in (pack or {}).get("files", []) or []:
                if not isinstance(f, dict):
                    continue
                source = str(f.get("source", ""))
                chosen = str(f.get("chosen_bucket") or f.get("bucket") or "UNSORTED")
                row = {
                    "pack": pack_name,
                    "source": source,
                    "dest": str(f.get("dest", "")),
                    "category": str(f.get("category", "")),
                    "action": str(f.get("action", "")),
                    "file": Path(source).name if source else "",
                    "chosen_bucket": chosen,
                    "original_bucket": chosen,
                    "override_bucket": "",
                    "effective_bucket": chosen,
                    "confidence_ratio": float(f.get("confidence_ratio", f.get("confidence", 0.0)) or 0.0),
                    "confidence_margin": float(f.get("confidence_margin", 0.0) or 0.0),
                    "low_confidence": bool(f.get("low_confidence", False)),
                    "top_3_candidates": list(f.get("top_3_candidates") or f.get("top_candidates") or []),
                    "folder_matches": list(f.get("folder_matches") or []),
                    "filename_matches": list(f.get("filename_matches") or []),
                    "audio_summary": dict(f.get("audio_summary") or {}),
                    "pitch_summary": dict(f.get("pitch_summary") or {}),
                    "glide_summary": dict(f.get("glide_summary") or {}),
                }
                rows.append(row)
        return rows

    def _refresh_bucket_filter(self) -> None:
        for combo, all_label in (
            (self.review_bucket_filter, "All buckets"),
            (self.preview_bucket_filter, "All buckets"),
        ):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_label)
            for bucket in self._bucket_choices:
                if bucket:
                    combo.addItem(bucket)
            idx = combo.findText(current)
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)

    def _refresh_pack_filters(self) -> None:
        packs = sorted({str(row.get("pack", "")) for row in self._rows_all if row.get("pack")})
        for combo, all_label in ((self.review_pack_filter, "All packs"), (self.preview_pack_filter, "All packs")):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_label)
            for pack in packs:
                combo.addItem(pack)
            idx = combo.findText(current)
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)

    def _apply_review_filters(self) -> None:
        query = (self.review_search.text() or "").strip().lower()
        bucket_filter = self.review_bucket_filter.currentText()
        pack_filter = self.review_pack_filter.currentText()
        low_only = self.review_low_only.isChecked()

        filtered: list[dict[str, Any]] = []
        for row in self._rows_all:
            effective_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
            if low_only and not bool(row.get("low_confidence", False)):
                continue
            if bucket_filter and bucket_filter != "All buckets" and effective_bucket != bucket_filter:
                continue
            if pack_filter and pack_filter != "All packs" and str(row.get("pack", "")) != pack_filter:
                continue
            if query:
                hay = " ".join(
                    [
                        str(row.get("pack", "")),
                        str(row.get("file", "")),
                        str(row.get("chosen_bucket", "")),
                        str(effective_bucket),
                        " ".join(str(c.get("bucket", "")) for c in (row.get("top_3_candidates") or []) if isinstance(c, dict)),
                    ]
                ).lower()
                if query not in hay:
                    continue
            filtered.append(row)

        self._render_review_table(filtered)
        total = len(self._rows_all)
        low_total = sum(1 for r in self._rows_all if bool(r.get("low_confidence", False)))
        self.review_count_label.setText(
            f"Showing {len(filtered)} row(s). Total files: {total}. Low-confidence: {low_total}. "
            f"Manual overrides: {len(self._manual_overrides)}."
        )
        if len(filtered) > _REVIEW_WIDGET_THRESHOLD:
            self.review_feedback_label.setText(
                "Large review set detected. Row edit controls are temporarily disabled to keep the UI stable. "
                f"Narrow the review filters to {_REVIEW_WIDGET_THRESHOLD} rows or fewer to enable per-row overrides and hints."
            )
            self.review_feedback_label.setProperty("state", "warning")
        elif self.review_feedback_label.text().startswith("Large review set detected."):
            self.review_feedback_label.setText("")
            self.review_feedback_label.setProperty("state", None)

    def _apply_preview_filters(self) -> None:
        query = (self.preview_search.text() or "").strip().lower()
        bucket_filter = self.preview_bucket_filter.currentText()
        pack_filter = self.preview_pack_filter.currentText()
        low_only = self.preview_low_only.isChecked()
        changed_only = self.preview_changed_only.isChecked()

        rows: list[dict[str, Any]] = []
        for row in self._rows_all:
            source = str(row.get("source", ""))
            effective_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
            if low_only and not bool(row.get("low_confidence", False)):
                continue
            if changed_only and source not in self._manual_overrides:
                continue
            if bucket_filter and bucket_filter != "All buckets" and effective_bucket != bucket_filter:
                continue
            if pack_filter and pack_filter != "All packs" and str(row.get("pack", "")) != pack_filter:
                continue
            if query:
                hay = " ".join(
                    [
                        str(row.get("pack", "")),
                        str(row.get("file", "")),
                        effective_bucket,
                        str(row.get("category", "")),
                        str(row.get("dest", "")),
                        str(row.get("source", "")),
                    ]
                ).lower()
                if query not in hay:
                    continue
            rows.append(row)

        self._render_preview_table(rows)

    def _render_review_table(self, rows: list[dict[str, Any]]) -> None:
        table = self.review_table
        widget_mode = len(rows) <= _REVIEW_WIDGET_THRESHOLD
        self._review_table_widget_mode = widget_mode
        prev_updates = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        table.blockSignals(True)
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        try:
            for r, row in enumerate(rows):
                source = str(row.get("source", ""))
                effective_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")

                items = [
                    QTableWidgetItem(str(row.get("pack", ""))),
                    QTableWidgetItem(str(row.get("file", ""))),
                    QTableWidgetItem(effective_bucket),
                    QTableWidgetItem(f"{float(row.get('confidence_ratio', 0.0) or 0.0):.4f}"),
                    QTableWidgetItem(f"{float(row.get('confidence_margin', 0.0) or 0.0):.2f}"),
                    QTableWidgetItem(""),
                ]
                self._apply_bucket_label_style(items[2], effective_bucket)
                self._style_confidence_item(
                    items[3],
                    float(row.get("confidence_ratio", 0.0) or 0.0),
                    bool(row.get("low_confidence", False)),
                )
                self._style_margin_item(items[4])
                self._style_top3_item(items[5], row)
                for col, item in enumerate(items):
                    item.setData(Qt.ItemDataRole.UserRole, source)
                    if bool(row.get("low_confidence", False)):
                        item.setData(Qt.ItemDataRole.UserRole + 1, True)
                    table.setItem(r, col, item)
                if bool(row.get("low_confidence", False)):
                    for item in (items[0], items[1], items[2], items[4], items[5]):
                        self._apply_low_conf_tint_to_item(item)

                if widget_mode:
                    override_combo = NoWheelComboBox()
                    override_combo.addItems(self._bucket_choices or [effective_bucket])
                    combo_bucket = effective_bucket
                    idx = override_combo.findText(combo_bucket)
                    override_combo.setCurrentIndex(max(0, idx))
                    override_combo.setProperty("source", source)
                    override_combo.currentTextChanged.connect(
                        lambda value, cb=override_combo: self._on_override_combo_changed(
                            str(cb.property("source") or ""), value
                        )
                    )
                    table.setCellWidget(r, 6, override_combo)

                    hint_btn = QPushButton("Hints…")
                    set_widget_role(hint_btn, "ghost")
                    hint_btn.setProperty("source", source)
                    hint_btn.clicked.connect(lambda _=False, btn=hint_btn: self._open_hint_menu(btn))
                    table.setCellWidget(r, 7, hint_btn)
                else:
                    override_item = QTableWidgetItem("Narrow filter to edit")
                    override_item.setData(Qt.ItemDataRole.UserRole, source)
                    if bool(row.get("low_confidence", False)):
                        self._apply_low_conf_tint_to_item(override_item)
                    table.setItem(r, 6, override_item)
                    hint_item = QTableWidgetItem("Narrow filter to use hints")
                    hint_item.setData(Qt.ItemDataRole.UserRole, source)
                    if bool(row.get("low_confidence", False)):
                        self._apply_low_conf_tint_to_item(hint_item)
                    table.setItem(r, 7, hint_item)
        finally:
            table.blockSignals(False)
            table.setUpdatesEnabled(prev_updates)

        if table.rowCount() > 0:
            table.selectRow(0)
        else:
            self.review_details.setPlainText("No rows match the current filter.")

    def _render_preview_table(self, rows: list[dict[str, Any]]) -> None:
        table = self.preview_table
        prev_updates = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        table.blockSignals(True)
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            effective_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
            low_conf = bool(row.get("low_confidence", False))
            values = [
                str(row.get("pack", "")),
                str(row.get("file", "")),
                effective_bucket,
                str(row.get("category", "")),
                str(row.get("action", "")),
                "yes" if low_conf else "no",
                str(row.get("dest", "")),
                str(row.get("source", "")),
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c == 2:
                    self._apply_bucket_label_style(item, effective_bucket)
                elif c == 5:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if low_conf and c != 5:
                    self._apply_low_conf_tint_to_item(item)
                table.setItem(r, c, item)
        table.blockSignals(False)
        table.setUpdatesEnabled(prev_updates)
        # Sorting on very large preview tables can make filter toggles feel like crashes.
        if len(rows) <= 2000:
            table.setSortingEnabled(True)

    def _update_preview_stale_state(self) -> None:
        self._preview_stale = bool(self._manual_overrides or self._saved_hints)
        if self._preview_stale:
            self.preview_stale_label.setText(
                "Preview is stale because manual overrides or saved hints changed after the last analyze/run. "
                "Rerun Analyze before copy/move."
            )
            if not self.progress_bar.isVisible():
                self.run_btn.setEnabled(False)
        else:
            self.preview_stale_label.setText("Preview reflects the latest analyze/dry-run report.")
            if not self.progress_bar.isVisible():
                self.run_btn.setEnabled(True)

    def _top3_text(self, row: dict[str, Any]) -> str:
        parts: list[str] = []
        for c in row.get("top_3_candidates", []) or []:
            if not isinstance(c, dict):
                continue
            parts.append(f"{c.get('bucket')}={float(c.get('score', 0.0) or 0.0):.1f}")
        return ", ".join(parts)

    def _on_override_combo_changed(self, source: str, bucket: str) -> None:
        row = self._row_index_by_source.get(source)
        if row is None or not bucket:
            return
        original_bucket = str(row.get("original_bucket") or row.get("chosen_bucket") or "")
        row["override_bucket"] = "" if bucket == original_bucket else bucket
        row["effective_bucket"] = bucket

        if bucket == original_bucket:
            self._manual_overrides.pop(source, None)
        else:
            self._manual_overrides[source] = {
                "source": source,
                "original_bucket": original_bucket,
                "override_bucket": bucket,
                "reason": "user_review",
                "timestamp": datetime.datetime.now().isoformat(),
            }

        self._rewrite_table_bucket_cells()
        self._rebuild_pack_breakdown()
        self._preview_stale = True
        self._apply_preview_filters()
        self._update_summary_label()
        self._update_review_details()
        self._update_preview_stale_state()
        self._sync_review_detail_controls()

    def _rewrite_table_bucket_cells(self) -> None:
        for r in range(self.review_table.rowCount()):
            item = self.review_table.item(r, 2)
            if item is None:
                continue
            source = str(item.data(Qt.ItemDataRole.UserRole) or "")
            row = self._row_index_by_source.get(source)
            if row is None:
                continue
            self._apply_bucket_label_style(item, str(row.get("effective_bucket") or row.get("chosen_bucket") or ""))

    def _open_hint_menu(self, button: QPushButton) -> None:
        source = str(button.property("source") or "")
        row = self._row_index_by_source.get(source)
        if row is None:
            return

        target_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
        menu = QMenu(button)
        filename_menu = menu.addMenu("Add filename hint")
        folder_menu = menu.addMenu("Add folder hint")

        filename_tokens = self._filename_tokens(row)
        folder_tokens = self._folder_tokens(row)
        if not filename_tokens:
            act = filename_menu.addAction("(No tokens)")
            act.setEnabled(False)
        else:
            for token in filename_tokens:
                act = filename_menu.addAction(token)
                act.triggered.connect(
                    lambda checked=False, s=source, b=target_bucket, t=token: self.hintSaveRequested.emit(
                        s, "filename", b, t
                    )
                )

        if not folder_tokens:
            act = folder_menu.addAction("(No tokens)")
            act.setEnabled(False)
        else:
            for token in folder_tokens:
                act = folder_menu.addAction(token)
                act.triggered.connect(
                    lambda checked=False, s=source, b=target_bucket, t=token: self.hintSaveRequested.emit(s, "folder", b, t)
                )

        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _open_selected_hint_menu(self, kind: str) -> None:
        row = self._selected_row()
        if row is None:
            return
        source = str(row.get("source", ""))
        target_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
        tokens = self._filename_tokens(row) if kind == "filename" else self._folder_tokens(row)
        button = self.review_detail_filename_hint_btn if kind == "filename" else self.review_detail_folder_hint_btn
        menu = QMenu(button)
        if not tokens:
            act = menu.addAction("(No tokens)")
            act.setEnabled(False)
        else:
            for token in tokens:
                act = menu.addAction(token)
                act.triggered.connect(
                    lambda checked=False, s=source, b=target_bucket, t=token, k=kind: self.hintSaveRequested.emit(
                        s, k, b, t
                    )
                )
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _filename_tokens(self, row: dict[str, Any]) -> list[str]:
        name = Path(str(row.get("file", ""))).stem
        tokens = [t.strip().lower() for t in _TOKEN_SPLIT_RE.split(name) if t.strip()]
        return sorted(set(tokens))

    def _folder_tokens(self, row: dict[str, Any]) -> list[str]:
        source = str(row.get("source", ""))
        if not source:
            return []
        try:
            parent_parts = list(Path(source).parent.parts)[-5:]
        except Exception:
            return []
        tokens: set[str] = set()
        for part in parent_parts:
            for tok in _TOKEN_SPLIT_RE.split(str(part).lower()):
                tok = tok.strip()
                if tok:
                    tokens.add(tok)
        return sorted(tokens)

    def _selected_row(self) -> Optional[dict[str, Any]]:
        items = self.review_table.selectedItems()
        if not items:
            return None
        source = str(items[0].data(Qt.ItemDataRole.UserRole) or "")
        return self._row_index_by_source.get(source)

    def _update_review_details(self) -> None:
        row = self._selected_row()
        if row is None:
            if self.review_table.rowCount() == 0:
                self.review_details.setPlainText("No review rows available.")
                self.review_selected_file_label.setText("No review rows available.")
                self.review_selected_meta_label.setText("")
            self._sync_review_detail_controls(None)
            return

        self.review_selected_file_label.setText(f"{row.get('file', '')}")
        self.review_selected_meta_label.setText(
            " | ".join(
                [
                    f"Pack: {row.get('pack', '')}",
                    f"Bucket: {row.get('effective_bucket') or row.get('chosen_bucket') or 'UNSORTED'}",
                    f"Confidence: {float(row.get('confidence_ratio', 0.0) or 0.0):.3f}",
                    f"Margin: {float(row.get('confidence_margin', 0.0) or 0.0):.2f}",
                    "LOW" if bool(row.get("low_confidence", False)) else "Normal",
                ]
            )
        )

        details = {
            "pack": row.get("pack"),
            "file": row.get("file"),
            "source": row.get("source"),
            "original_bucket": row.get("original_bucket"),
            "effective_bucket": row.get("effective_bucket"),
            "low_confidence": row.get("low_confidence"),
            "confidence_ratio": row.get("confidence_ratio"),
            "confidence_margin": row.get("confidence_margin"),
            "top_3_candidates": row.get("top_3_candidates"),
            "folder_matches": row.get("folder_matches"),
            "filename_matches": row.get("filename_matches"),
            "audio_summary": row.get("audio_summary"),
            "pitch_summary": row.get("pitch_summary"),
            "glide_summary": row.get("glide_summary"),
        }
        self.review_details.setPlainText(json.dumps(details, indent=2))
        self._sync_review_detail_controls(row)

    def _sync_review_detail_controls(self, row: Optional[dict[str, Any]] = None) -> None:
        row = row if row is not None else self._selected_row()
        if row is None:
            with QSignalBlocker(self.review_detail_override_combo):
                self.review_detail_override_combo.clear()
            self.review_detail_override_combo.setEnabled(False)
            self.review_detail_filename_hint_btn.setEnabled(False)
            self.review_detail_folder_hint_btn.setEnabled(False)
            return
        effective_bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "")
        choices = self._bucket_choices or [effective_bucket]
        with QSignalBlocker(self.review_detail_override_combo):
            self.review_detail_override_combo.clear()
            for choice in choices:
                self.review_detail_override_combo.addItem(choice)
            idx = self.review_detail_override_combo.findText(effective_bucket)
            self.review_detail_override_combo.setCurrentIndex(max(0, idx))
        self.review_detail_override_combo.setEnabled(True)
        self.review_detail_filename_hint_btn.setEnabled(True)
        self.review_detail_folder_hint_btn.setEnabled(True)

    def _on_detail_override_changed(self, bucket: str) -> None:
        row = self._selected_row()
        if row is None:
            return
        source = str(row.get("source", ""))
        if not source or not bucket:
            return
        self._on_override_combo_changed(source, bucket)

    def _rebuild_pack_breakdown(self) -> None:
        lines: list[str] = []
        packs: dict[str, dict[str, int]] = {}
        for row in self._rows_all:
            pack = str(row.get("pack", ""))
            bucket = str(row.get("effective_bucket") or row.get("chosen_bucket") or "UNSORTED")
            counts = packs.setdefault(pack, {})
            counts[bucket] = counts.get(bucket, 0) + 1
        for pack_name in sorted(packs):
            counts = packs[pack_name]
            counts_str = ", ".join(f"{bucket}: {count}" for bucket, count in sorted(counts.items()))
            lines.append(f"{pack_name}: {counts_str}")
        self.log_edit.setPlainText("\n".join(lines))

    def _update_summary_label(self) -> None:
        report = self._report or {}
        parts = []
        if report:
            parts.append(f"Processed {report.get('files_processed', 0)} file(s)")
            parts.append(f"Moved {report.get('files_moved', 0)}")
            parts.append(f"Copied {report.get('files_copied', 0)}")
            parts.append(f"Unsorted {report.get('unsorted', 0)}")
            if report.get("failed", 0):
                parts.append(f"Failed {report.get('failed', 0)}")
            if report.get("files_skipped_non_wav", 0):
                parts.append(f"Skipped non-WAV {report.get('files_skipped_non_wav', 0)}")
            if self._manual_overrides:
                parts.append(f"Manual overrides {len(self._manual_overrides)} (rerun before copy/move)")
            cache_stats = report.get("feature_cache_stats") or {}
            if isinstance(cache_stats, dict):
                parts.append(
                    "Cache hits/misses "
                    f"{int(cache_stats.get('hits', 0) or 0)}/{int(cache_stats.get('misses', 0) or 0)}"
                )
        self.summary_label.setText(" | ".join(parts) if parts else "No results.")
