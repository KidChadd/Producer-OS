from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal

from producer_os.engine import ProducerOSEngine


class EngineRunner(QObject):
    """Run the engine in a background thread and emit a completion signal."""

    finished = Signal(dict, str)

    def __init__(self, engine: ProducerOSEngine, mode: str) -> None:
        super().__init__()
        self.engine = engine
        self.mode = mode

    def start(self) -> None:
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        report = self.engine.run(mode=self.mode)

        run_id = report.get("run_id")
        hub_dir = self.engine.hub_dir

        report_path = ""
        try:
            if run_id:
                candidate = hub_dir / "logs" / str(run_id) / "run_report.json"
                if candidate.exists():
                    report_path = str(candidate)
        except Exception:
            report_path = ""

        self.finished.emit(report, report_path)
