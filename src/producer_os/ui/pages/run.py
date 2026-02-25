from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QWidget,
)

from producer_os.ui.pages.base import BaseWizardPage
from producer_os.ui.widgets import StatChip, StatusBadge, set_widget_role


class RunPage(BaseWizardPage):
    analyzeRequested = Signal()
    runRequested = Signal()
    saveReportRequested = Signal()

    def __init__(self, action: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            "Step 4 - Run & Review",
            "Analyze or execute routing, then inspect the summarized results and export the run report.",
            parent,
        )
        self._action_name = action

        action_card = self.add_card("Execution Controls", "Run an analysis first to verify routing before moving files.")
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        self.analyze_btn = QPushButton("Analyze")
        set_widget_role(self.analyze_btn, "ghost")
        self.analyze_btn.clicked.connect(self.analyzeRequested.emit)
        action_row.addWidget(self.analyze_btn)

        self.run_btn = QPushButton(self._run_button_label(action))
        set_widget_role(self.run_btn, "primary")
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

        summary_card = self.add_card("Summary", "Key outcomes from the most recent analyze/run action.")
        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(10)
        self.processed_chip = StatChip("Processed", "0")
        self.moved_chip = StatChip("Moved", "0")
        self.copied_chip = StatChip("Copied", "0")
        self.unsorted_chip = StatChip("Unsorted", "0")
        for chip in (self.processed_chip, self.moved_chip, self.copied_chip, self.unsorted_chip):
            stats.addWidget(chip)
        summary_card.body_layout.addLayout(stats)

        self.summary_label = QLabel("No results yet.")
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        summary_card.body_layout.addWidget(self.summary_label)

        log_card = self.add_card("Pack Breakdown", "Per-pack bucket counts from the latest report.")
        self.log_edit = QTextEdit()
        self.log_edit.setObjectName("LogOutput")
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(220)
        log_card.body_layout.addWidget(self.log_edit)

        export_card = self.add_card("Report Export")
        export_row = QHBoxLayout()
        export_row.setContentsMargins(0, 0, 0, 0)
        export_row.setSpacing(8)
        self.save_report_btn = QPushButton("Save run report...")
        set_widget_role(self.save_report_btn, "ghost")
        self.save_report_btn.setVisible(False)
        self.save_report_btn.clicked.connect(self.saveReportRequested.emit)
        export_row.addWidget(self.save_report_btn)
        export_row.addStretch(1)
        export_card.body_layout.addLayout(export_row)

    def _run_button_label(self, action: str) -> str:
        action = action.lower().strip()
        return "Run (Move)" if action == "move" else "Run (Copy)"

    def set_action(self, action: str) -> None:
        self._action_name = action
        self.run_btn.setText(self._run_button_label(action))

    def set_busy(self, busy: bool, mode: str | None = None) -> None:
        self.analyze_btn.setEnabled(not busy)
        self.run_btn.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        self.progress_bar.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress_bar.setValue(0)
            self.status_badge.set_status("Ready", kind="neutral", pulsing=False)
            return
        if mode == "analyze":
            self.status_badge.set_status("Analyzing", kind="analyzing", pulsing=True)
        else:
            self.status_badge.set_status("Running", kind="running", pulsing=True)

    def clear_results(self) -> None:
        for chip in (self.processed_chip, self.moved_chip, self.copied_chip, self.unsorted_chip):
            chip.set_value("0")
        self.summary_label.setText("Working...")
        self.log_edit.clear()
        self.save_report_btn.setVisible(False)

    def set_results(self, report: dict, log_lines: list[str]) -> None:
        self.processed_chip.set_value(str(report.get("files_processed", 0)))
        self.moved_chip.set_value(str(report.get("files_moved", 0)))
        self.copied_chip.set_value(str(report.get("files_copied", 0)))
        self.unsorted_chip.set_value(str(report.get("unsorted", 0)))

        summary_parts = []
        if report:
            summary_parts.append(f"Processed {report.get('files_processed', 0)} file(s)")
            summary_parts.append(f"Moved {report.get('files_moved', 0)}")
            summary_parts.append(f"Copied {report.get('files_copied', 0)}")
            summary_parts.append(f"Unsorted {report.get('unsorted', 0)}")
            if report.get("failed", 0):
                summary_parts.append(f"Failed {report.get('failed', 0)}")
        self.summary_label.setText(" | ".join(summary_parts) if summary_parts else "No results.")
        self.log_edit.setPlainText("\n".join(log_lines))
        self.save_report_btn.setVisible(True)
        self.status_badge.set_status("Completed", kind="success", pulsing=False)
