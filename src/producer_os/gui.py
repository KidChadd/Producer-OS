"""Compatibility GUI entrypoint for Producer-OS.

This module preserves the public import path ``producer_os.gui:main`` while the
actual GUI implementation lives under ``producer_os.ui``.
"""

from __future__ import annotations

from producer_os.ui.app import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
