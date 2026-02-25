# build_gui_entry.py
from __future__ import annotations

import os

# Disable numba JIT (important for frozen builds)
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from producer_os.gui import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())