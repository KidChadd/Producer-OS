from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_VERSION = 1


GUI_MODULE_FILES = [
    "src/producer_os/ui/__init__.py",
    "src/producer_os/ui/app.py",
    "src/producer_os/ui/animations.py",
    "src/producer_os/ui/engine_runner.py",
    "src/producer_os/ui/state.py",
    "src/producer_os/ui/theme.py",
    "src/producer_os/ui/widgets.py",
    "src/producer_os/ui/window.py",
    "src/producer_os/ui/data/__init__.py",
    "src/producer_os/ui/data/fl_icon_favorites.py",
    "src/producer_os/ui/dialogs/__init__.py",
    "src/producer_os/ui/dialogs/icon_picker.py",
    "src/producer_os/ui/pages/__init__.py",
    "src/producer_os/ui/pages/base.py",
    "src/producer_os/ui/pages/hub.py",
    "src/producer_os/ui/pages/inbox.py",
    "src/producer_os/ui/pages/options.py",
    "src/producer_os/ui/pages/run.py",
]

ENTRY_FILES = [
    "src/producer_os/__main__.py",
    "build_gui_entry.py",
]

PAGE_FILES = [
    "src/producer_os/ui/pages/inbox.py",
    "src/producer_os/ui/pages/hub.py",
    "src/producer_os/ui/pages/options.py",
    "src/producer_os/ui/pages/run.py",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_ast(path: Path) -> ast.AST:
    return ast.parse(_read_text(path), filename=str(path))


def _unparse(node: ast.AST) -> str:
    return ast.unparse(node) if hasattr(ast, "unparse") else ""


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _call_is_signal(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id == "Signal"
    if isinstance(func, ast.Attribute):
        return func.attr == "Signal"
    return False


def _literal(node: ast.AST) -> Any:
    return ast.literal_eval(node)


def _find_class(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _extract_classes_and_functions(tree: ast.AST) -> tuple[list[str], list[str]]:
    classes: list[str] = []
    funcs: list[str] = []
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node.name)
    return classes, funcs


def _extract_signals_by_class(tree: ast.AST) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for node in tree.body:  # type: ignore[attr-defined]
        if not isinstance(node, ast.ClassDef):
            continue
        signals: list[str] = []
        for stmt in node.body:
            targets: list[str] = []
            value: ast.AST | None = None
            if isinstance(stmt, ast.Assign):
                value = stmt.value
                for t in stmt.targets:
                    if isinstance(t, ast.Name):
                        targets.append(t.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                value = stmt.value
                targets.append(stmt.target.id)
            if not targets or not isinstance(value, ast.Call) or not _call_is_signal(value):
                continue
            signals.extend(targets)
        if signals:
            out[node.name] = signals
    return out


def _extract_module_assign_literal(tree: ast.AST, name: str) -> Any | None:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    try:
                        return _literal(node.value)
                    except Exception:
                        return None
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            try:
                return _literal(node.value) if node.value is not None else None
            except Exception:
                return None
    return None


def _extract_class_assign_literal(cls: ast.ClassDef, name: str) -> Any | None:
    for node in cls.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    try:
                        return _literal(node.value)
                    except Exception:
                        return None
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            try:
                return _literal(node.value) if node.value is not None else None
            except Exception:
                return None
    return None


def _extract_add_card_titles(page_source: str) -> list[str]:
    tree = ast.parse(page_source)
    titles: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_card":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                titles.append(node.args[0].value)
    return titles


def _extract_header_labels_from_source(source: str, widget_name: str) -> list[str]:
    pattern = re.compile(
        rf"{re.escape(widget_name)}\.setHorizontalHeaderLabels\(\s*(\[[^\]]*\])\s*\)",
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return []
    try:
        labels = ast.literal_eval(match.group(1))
    except Exception:
        return []
    if isinstance(labels, list) and all(isinstance(x, str) for x in labels):
        return labels
    return []


def _extract_tab_names_from_run_source(source: str) -> list[str]:
    return re.findall(r'self\.tabs\.addTab\(\s*tab\s*,\s*"([^"]+)"\s*\)', source)


def _extract_connect_calls_in_method(tree: ast.AST, class_name: str, method_name: str) -> list[str]:
    cls = _find_class(tree, class_name)
    if cls is None:
        return []
    method = _find_method(cls, method_name)
    if method is None:
        return []
    calls: list[str] = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "connect":
            calls.append(_normalize_ws(_unparse(node)))
    return sorted(calls)


def _extract_connect_calls_in_class(tree: ast.AST, class_name: str) -> list[str]:
    cls = _find_class(tree, class_name)
    if cls is None:
        return []
    calls: list[str] = []
    for node in ast.walk(cls):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "connect":
            calls.append(_normalize_ws(_unparse(node)))
    return sorted(set(calls))


def _extract_engine_runner_run_call(tree: ast.AST) -> dict[str, str]:
    class_node = _find_class(tree, "EngineRunner")
    if class_node is None:
        return {}
    out: dict[str, str] = {}
    for node in ast.walk(class_node):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "run":
                if isinstance(func.value, ast.Name) and func.value.id == "engine":
                    for kw in node.keywords:
                        if kw.arg in {"log_callback", "progress_callback", "log_to_console"} and kw.value is not None:
                            out[kw.arg] = _normalize_ws(_unparse(kw.value))
                    return out
    return out


def _extract_window_step_defs(tree: ast.AST) -> list[list[str]]:
    cls = _find_class(tree, "ProducerOSWindow")
    if cls is None:
        return []
    value = _extract_class_assign_literal(cls, "STEP_DEFS")
    if not isinstance(value, list):
        return []
    out: list[list[str]] = []
    for item in value:
        if isinstance(item, tuple) and len(item) == 2 and all(isinstance(v, str) for v in item):
            out.append([item[0], item[1]])
    return out


def _extract_theme_snapshot(theme_tree: ast.AST) -> dict[str, Any]:
    theme_preset_choices = _extract_module_assign_literal(theme_tree, "THEME_PRESET_CHOICES") or []
    theme_preset_labels = _extract_module_assign_literal(theme_tree, "THEME_PRESET_LABELS") or {}
    theme_aliases = _extract_module_assign_literal(theme_tree, "_THEME_ALIASES") or {}
    ui_density_choices = _extract_module_assign_literal(theme_tree, "UI_DENSITY_CHOICES") or []
    accent_mode_choices = _extract_module_assign_literal(theme_tree, "ACCENT_MODE_CHOICES") or []
    accent_preset_colors = _extract_module_assign_literal(theme_tree, "ACCENT_PRESET_COLORS") or {}

    return {
        "theme_preset_choices": list(theme_preset_choices),
        "theme_preset_labels": dict(theme_preset_labels),
        "theme_aliases": dict(theme_aliases),
        "ui_density_choices": list(ui_density_choices),
        "accent_mode_choices": list(accent_mode_choices),
        "accent_preset_colors": dict(accent_preset_colors),
        "accent_preset_choices": list(accent_preset_colors.keys()),
    }


def _extract_entry_markers(repo_root: Path) -> dict[str, Any]:
    main_src = _read_text(repo_root / "src/producer_os/__main__.py")
    gui_entry_src = _read_text(repo_root / "build_gui_entry.py")
    app_src = _read_text(repo_root / "src/producer_os/ui/app.py")
    return {
        "main_subcommands_markers": {
            "gui": '"gui"' in main_src,
            "qt": '"qt"' in main_src,
        },
        "build_gui_entry_markers": {
            "numba_disable_jit": "NUMBA_DISABLE_JIT" in gui_entry_src,
            "producer_os_gui_main": "producer_os.ui.app" in gui_entry_src or "producer_os.gui" in gui_entry_src,
        },
        "app_icon_candidates": re.findall(r'repo_root\s*/\s*"assets"\s*/\s*"([^"]+)"', app_src),
        "app_smoke_env_vars": sorted(set(re.findall(r'PRODUCER_OS_[A-Z0-9_]+', app_src))),
    }


def _extract_source_markers(repo_root: Path) -> dict[str, Any]:
    window_src = _read_text(repo_root / "src/producer_os/ui/window.py")
    run_src = _read_text(repo_root / "src/producer_os/ui/pages/run.py")
    options_src = _read_text(repo_root / "src/producer_os/ui/pages/options.py")

    return {
        "window_markers": {
            "run_step_hides_next_button": "self.next_btn.setVisible(not is_run_step)" in window_src,
            "header_theme_combo_uses_no_wheel": "self.header_theme_combo = NoWheelComboBox()" in window_src,
            "step_sidebar_present": "StepSidebar(self.STEP_DEFS)" in window_src,
        },
        "run_markers": {
            "review_widget_threshold_literal": "_REVIEW_WIDGET_THRESHOLD = 500" in run_src,
            "review_splitter_present": "self.review_splitter = QSplitter(" in run_src,
            "qsettings_present": "QSettings(" in run_src,
            "audio_preview_qt_multimedia": "QMediaPlayer" in run_src and "QAudioOutput" in run_src,
            "delegates_present": all(
                marker in run_src
                for marker in ("_BucketBadgeDelegate", "_ConfidenceChipDelegate", "_Top3BadgeDelegate")
            ),
            "batch_actions_present": all(
                marker in run_src
                for marker in (
                    "review_batch_override_btn",
                    "review_batch_hint_btn",
                    "review_filter_selected_pack_btn",
                    "review_filter_selected_bucket_btn",
                )
            ),
            "context_menu_present": "customContextMenuRequested.connect" in run_src and "_open_review_context_menu" in run_src,
        },
        "options_markers": {
            "theme_preview_cards_present": "ThemePreviewCard" in options_src,
            "bucket_icon_picker_present": "IconPickerDialog" in options_src,
            "bucket_table_columns_present": "IconIndex" in options_src and "Preview" in options_src,
        },
    }


def collect_snapshot(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()

    all_required_files = GUI_MODULE_FILES + ENTRY_FILES
    files_snapshot: dict[str, Any] = {}
    class_signals: dict[str, dict[str, list[str]]] = {}

    for rel in all_required_files:
        path = repo_root / rel
        tree = _parse_ast(path)
        classes, funcs = _extract_classes_and_functions(tree)
        files_snapshot[rel] = {
            "classes": classes,
            "top_level_functions": funcs,
        }
        signals = _extract_signals_by_class(tree)
        if signals:
            class_signals[rel] = signals

    theme_tree = _parse_ast(repo_root / "src/producer_os/ui/theme.py")
    window_tree = _parse_ast(repo_root / "src/producer_os/ui/window.py")
    engine_runner_tree = _parse_ast(repo_root / "src/producer_os/ui/engine_runner.py")
    run_tree = _parse_ast(repo_root / "src/producer_os/ui/pages/run.py")

    page_card_titles: dict[str, list[str]] = {}
    for rel in PAGE_FILES:
        page_card_titles[rel] = _extract_add_card_titles(_read_text(repo_root / rel))

    run_source = _read_text(repo_root / "src/producer_os/ui/pages/run.py")
    options_source = _read_text(repo_root / "src/producer_os/ui/pages/options.py")

    snapshot = {
        "schema_version": SCRIPT_VERSION,
        "required_files": all_required_files,
        "files": files_snapshot,
        "signals_by_file": class_signals,
        "theme": _extract_theme_snapshot(theme_tree),
        "window": {
            "step_defs": _extract_window_step_defs(window_tree),
            "wire_signals_connect_calls": _extract_connect_calls_in_method(window_tree, "ProducerOSWindow", "_wire_signals"),
        },
        "pages": {
            "card_titles": page_card_titles,
            "run_tabs": _extract_tab_names_from_run_source(run_source),
            "review_table_columns": _extract_header_labels_from_source(run_source, "self.review_table"),
            "preview_table_columns": _extract_header_labels_from_source(run_source, "self.preview_table"),
            "bucket_table_columns": _extract_header_labels_from_source(options_source, "self.bucket_table"),
            "run_connect_calls": _extract_connect_calls_in_class(run_tree, "RunPage"),
        },
        "engine_runner": {
            "signals": _extract_signals_by_class(engine_runner_tree).get("EngineRunner", []),
            "run_call_keywords": _extract_engine_runner_run_call(engine_runner_tree),
        },
        "entry_markers": _extract_entry_markers(repo_root),
        "source_markers": _extract_source_markers(repo_root),
    }
    return snapshot


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze/validate a structural spec-lock snapshot of the current Producer-OS GUI."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path (default: current directory).")
    parser.add_argument("--write-baseline", help="Write current snapshot JSON to this path.")
    parser.add_argument("--baseline", help="Baseline JSON path to compare against.")
    parser.add_argument("--check", action="store_true", help="Fail if current snapshot differs from --baseline.")
    parser.add_argument("--print", action="store_true", dest="do_print", help="Print current snapshot JSON.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    snapshot = collect_snapshot(repo_root)

    if args.write_baseline:
        _write_json(Path(args.write_baseline), snapshot)

    if args.do_print:
        print(json.dumps(snapshot, indent=2, sort_keys=True))

    if args.check:
        if not args.baseline:
            parser.error("--check requires --baseline")
        baseline_path = Path(args.baseline)
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        if snapshot != baseline:
            print("GUI spec-lock snapshot mismatch.", file=sys.stderr)
            print(f"Baseline: {baseline_path}", file=sys.stderr)
            print("Re-run with --print or --write-baseline to inspect/update.", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
