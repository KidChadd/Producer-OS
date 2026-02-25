# src/producer_os/__main__.py
from __future__ import annotations

import sys


def _run_cli() -> int:
    from producer_os.cli import main as cli_main

    # Your CLI is already wired for `python -m producer_os.cli ...`
    # so we just call it and let it read sys.argv itself.
    return int(cli_main())


def _run_gui() -> int:
    try:
        from producer_os.gui import main as gui_main
    except ModuleNotFoundError as e:
        if "PySide6" in str(e):
            print(
                "GUI dependencies are not installed.\n"
                'Install them, then re-run:\n  pip install -e ".[gui]"\n'
                "Or use the CLI:\n  python -m producer_os --help"
            )
            return 1
        raise
    return int(gui_main())


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = ProducerOSWizard()
    win.show()

    try:
        return app.exec()
    except KeyboardInterrupt:
        return 0