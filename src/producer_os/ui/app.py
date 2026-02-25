from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from producer_os.ui.window import ProducerOSWindow


def _load_app_icon() -> Optional[QIcon]:
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        repo_root / "assets" / "app_icon.ico",
        repo_root / "assets" / "app_icon.png",
        repo_root / "assets" / "banner.png",
    ]
    for path in candidates:
        if not path.exists():
            continue
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon
    return None


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Producer OS")
    app.setOrganizationName("KidChadd")

    app_icon = _load_app_icon()
    if app_icon is not None:
        app.setWindowIcon(app_icon)

    win = ProducerOSWindow(app_icon=app_icon)
    win.show()

    try:
        return app.exec()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
