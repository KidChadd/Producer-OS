# Contributor Quickstart

This guide is the fastest path to making a useful PR to Producer-OS.

Use this together with:

- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)

## 1) Clone and Set Up

```powershell
git clone https://github.com/KidChadd/Producer-OS.git
cd Producer-OS

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,gui]"
```

## 2) Verify the Environment

```powershell
python -m pytest -q
python -m ruff check src tests
python -m mypy src/producer_os
producer-os --help
producer-os-gui
```

## 3) Choose a Good First Task

Recommended places to start:

- docs improvements (`README.md`, `docs/*`)
- tests (`tests/*`)
- GUI polish under `src/producer_os/ui/`
- CI/workflow ergonomics under `.github/workflows/`

See the starter issue ideas in [`ROADMAP.md`](../ROADMAP.md).

For reproducible demos and bug reports, use the synthetic sample corpus:

- `examples/synthetic_corpus/`
- regenerate with `python scripts/generate_synthetic_corpus.py`

## 4) Branch and Make Changes

```powershell
git checkout -b feat/my-change
```

Conventions:

- keep changes scoped
- avoid unrelated refactors in the same PR
- preserve deterministic and non-destructive behavior

## 5) Run Checks Before PR

```powershell
python -m pytest -q
python -m ruff check src tests
python -m mypy src/producer_os
```

Optional (recommended):

```powershell
pre-commit run --all-files
```

## 6) Open a PR

Before opening:

- write a clear commit message (Conventional Commit style preferred)
- explain what changed and why
- include test steps and screenshots for GUI changes

PR labels:

- PR file-based labels are applied automatically (docs/gui/ci/tests/etc.)
- maintainers may add `help wanted` / `good first issue` on issues, not PRs

## Issues vs Discussions

Use GitHub Issues for:

- reproducible bugs
- concrete feature requests
- scoped implementation tasks

Use GitHub Discussions for:

- questions
- tuning advice
- design ideas / proposals
- usage guidance

If Discussions are not yet enabled, use the issue template contact links or `SUPPORT.md`.

## Common Gotchas

- `analyze` mode is no-write by design (no `run_report.json`, no cache writes)
- Hybrid classification is currently `.wav`-only
- GUI features may require `.[gui]` extras
- Windows release packaging changes should be validated in CI workflows
- Use `examples/synthetic_corpus/` when you need a shareable repro set

## Helpful References

- [`docs/CLI_REFERENCE.md`](CLI_REFERENCE.md)
- [`docs/CLASSIFICATION.md`](CLASSIFICATION.md)
- [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md)
- [`docs/SYSTEM_REQUIREMENTS.md`](SYSTEM_REQUIREMENTS.md)
