# Testing Guide

This project uses `pytest`, `ruff`, and `mypy`. The core safety and engine
behavior tests live in `tests/test_engine_rules.py` and `tests/test_engine.py`.
GUI structure fidelity is also protected by a spec-lock baseline test (`tests/test_gui_spec_lock.py`).

## Local Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If you are testing GUI changes:

```bash
python -m pip install -e ".[dev,gui]"
```

## Quick Checks

```bash
python -m ruff check src tests
python -m mypy src/producer_os
python -m pytest -q
```

GUI spec-lock structural check:

```bash
python scripts/gui_spec_lock_audit.py --baseline tests/fixtures/gui_spec_lock_baseline.json --check
python -m pytest -q tests/test_gui_spec_lock.py
```

## Full Local Validation (CI Parity)

```bash
python -m ruff check src tests
python -m mypy src/producer_os
python -m pytest -q --disable-warnings
python -m pip install --upgrade build
python -m build
```

## Focused Engine Rule Tests

Use this when working on routing, safety guarantees, styles, undo, or portable
mode logic:

```bash
python -m pytest -q tests/test_engine_rules.py
```

## GUI Smoke Test

```bash
producer-os-gui
```

Or via module entrypoint:

```bash
python -m producer_os gui
```

Timed GUI smoke mode (auto-exit):

```powershell
$env:PRODUCER_OS_SMOKE_TEST=1
$env:PRODUCER_OS_SMOKE_TEST_MS=400
python -m producer_os gui
Remove-Item Env:PRODUCER_OS_SMOKE_TEST
Remove-Item Env:PRODUCER_OS_SMOKE_TEST_MS
```

Recommended manual smoke checks:

- Open the wizard and switch between all four steps
- Verify the `Run` step footer hides `Next`
- Check `Options` -> `Appearance` (theme presets, density, accent, theme previews)
- Run `Analyze` on a small test inbox/hub
- Open `Low Confidence Review` and verify split-pane/details behavior
- Test batch review actions and row context menu
- If QtMultimedia is available, test audio preview + waveform on a selected row
- Run `Copy` (or `Move` in a disposable test folder)
- Save the run report from the Run page
- Open config folder / last report from Developer Tools

## GitHub Actions Workflows

- `python.yml`: Ruff, Mypy, Pytest, package build (push/PR on `main`)
- `build.yml`: manual Windows EXE build artifact (Nuitka, `dev`/`release` build profiles, timing artifacts)
- `release.yml`: tag-triggered/manual Windows release build (`v*.*.*`) with packaged GUI + tiny-analyze smoke tests
- `version.yml`: semantic-release automation on pushes to `main`

Windows build/release runs also publish:

- `BUILD_INFO.txt`
- `BUILD_TIMING.txt`
- `SIGNING_STATUS.txt`
