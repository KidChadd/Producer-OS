from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_audit_module(repo_root: Path):
    module_path = repo_root / "scripts" / "gui_spec_lock_audit.py"
    spec = importlib.util.spec_from_file_location("gui_spec_lock_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load audit module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gui_spec_lock_snapshot_matches_baseline() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    baseline_path = repo_root / "tests" / "fixtures" / "gui_spec_lock_baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    audit = _load_audit_module(repo_root)
    snapshot = audit.collect_snapshot(repo_root)

    assert snapshot == baseline
