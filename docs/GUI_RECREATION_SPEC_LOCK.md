# GUI Recreation Spec-Lock

This repository already contains the authoritative GUI implementation.

The "spec-locked recreation" plan is implemented as a reproducible structural baseline plus a validation harness that enforces fidelity to the current GUI template without reinterpretation.

## Authoritative Scope

- `src/producer_os/ui/**`
- `src/producer_os/__main__.py`
- `build_gui_entry.py`

## What Is Frozen

The spec-lock snapshot captures:

- GUI module/file manifest
- Classes and top-level functions by file
- Qt signal declarations by class
- Theme/theming registries (`theme` presets, density modes, accent modes/presets, aliases)
- `ProducerOSWindow.STEP_DEFS`
- `ProducerOSWindow._wire_signals()` connect-call set (normalized)
- Page card titles
- Run-page tab names and table column headers
- Run-page connect-call set (normalized)
- EngineRunner signal set and engine `run(...)` callback keyword wiring
- Entry/runtime markers (GUI smoke/tiny-analyze env vars, icon fallback candidates)
- Source markers for key GUI features (run footer behavior, review split-pane, delegates, audio preview, batch review actions, icon picker, theme preview cards)

## Baseline Fixture

- `tests/fixtures/gui_spec_lock_baseline.json`

This file is the frozen structural baseline for the current GUI template.

## Validation Commands

Validate current GUI against the frozen baseline:

```powershell
python scripts/gui_spec_lock_audit.py --baseline tests/fixtures/gui_spec_lock_baseline.json --check
```

Run the corresponding test:

```powershell
python -m pytest tests/test_gui_spec_lock.py -q
```

Print the current snapshot (for inspection only):

```powershell
python scripts/gui_spec_lock_audit.py --print
```

Regenerate the baseline intentionally (only when the authoritative GUI template changes by decision):

```powershell
python scripts/gui_spec_lock_audit.py --write-baseline tests/fixtures/gui_spec_lock_baseline.json
```

## Idempotent Recreation Enforcement

The spec-lock process is idempotent when run against the same authoritative GUI source:

- repeated snapshots produce the same JSON payload
- no new structural elements are introduced
- signal/slot and layout identifiers remain stable

Any mismatch must be resolved by aligning to the literal current GUI implementation.
