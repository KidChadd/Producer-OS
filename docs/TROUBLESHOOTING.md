# Troubleshooting

This page covers common setup and runtime issues for Producer-OS.

## Privacy / Telemetry

Producer-OS does not include telemetry or analytics collection.

- no automatic telemetry
- no automatic cloud uploads of audio/content
- local files stay local unless you explicitly copy/move/export them

If you are troubleshooting a bug, share only redacted logs/paths and never upload private sample packs.

## GUI Fails to Start (PySide6 Not Installed)

Symptom:

- Running `producer-os-gui` or `python -m producer_os gui` fails on a source install

Fix:

```powershell
pip install -e ".[gui]"
```

## Qt Platform Plugin Error (`qwindows.dll`)

Symptom (older/broken Windows portable builds):

- `Could not find the Qt platform plugin "windows"`
- `no Qt platform plugin could be initialized`

Cause:

- The Windows portable build was created without the required PySide6/Nuitka plugin assets.

Fix:

- Download the latest GitHub Release build
- If rebuilding locally/CI, ensure the PySide6 plugin is bundled (the current CI workflow verifies `qwindows.dll` and runs a packaged GUI smoke test)

Related docs:

- `docs/RELEASE_PROCESS.md`

## Built-in Troubleshooting Panel (GUI)

The GUI Options page includes a Troubleshooting card with quick actions:

- Open config folder
- Open logs folder
- Open last report
- Verify audio dependencies
- Qt plugin check (packaged builds)

It also displays:

- portable mode status
- audio dependency check summary
- latest Qt plugin check result

## Bucket Name / Color / Icon Changes Did Not Apply

Symptom:

- Bucket display names or colors/icons still look unchanged after editing them in the GUI

What to check:

- Click `Save bucket customizations` in `Options` -> `Bucket Customization`
- Use `Reload bucket customizations` to confirm the saved values were written
- Rerun `copy`, `move`, or `repair-styles` to regenerate folder `.nfo` styling

Why this happens:

- `analyze` and `dry-run` do not write `.nfo` files
- `.nfo` styles only update when style-writing modes run

Icon format reminders (`IconIndex`):

- decimal: `10`
- hex: `f129`
- 4-char hex: `0074`
- prefixed: `0xF129` or `$F129`

Related docs:

- [`docs/CUSTOMIZATION.md`](CUSTOMIZATION.md)

## `analyze` Mode Did Not Create Logs or Reports

This is expected.

`analyze` mode is a strict no-write mode:

- no logs
- no `run_report.json`
- no `feature_cache.json`
- no `.nfo` writes

Use `dry-run` if you want logs/reports without moving/copying files.

## Low-Confidence Classifications

Symptom:

- Files are still bucketed, but flagged `low_confidence`

This is expected behavior.
Producer-OS always selects a best bucket and records the top candidates in the reasoning payload.

What to do:

- Review `run_report.json`
- Check `top_3_candidates`
- Tune keyword mappings / bucket vocab
- Tune classifier thresholds/weights (advanced)

## Audio Features Seem Missing / Weak Classification

Possible cause:

- Optional audio dependencies are not installed or failed to import

Recommended source install:

```powershell
pip install -e ".[gui]"
```

For development:

```powershell
pip install -e ".[dev,gui]"
```

## Config Files Not Being Loaded

Check the mode/location first:

- Standard mode uses the platform config directory (Windows: `%APPDATA%\ProducerOS`)
- Portable mode uses local files when `portable.flag` exists or `--portable` is used

Files to verify:

- `config.json`
- `buckets.json`
- `bucket_styles.json`
- `bucket_hints.json`

Starter examples:

- `examples/config.example.json`
- `examples/buckets.json`
- `examples/bucket_styles.json`

## Release Was Not Tagged After a Push

Producer-OS uses semantic-release rules.
Not every commit type creates a version bump.

Version bump commit types:

- `feat` (minor)
- `fix` (patch)
- `perf` (patch)
- `refactor` (patch)

No version bump by default:

- `docs`
- `chore`

## Duplicate Tag / Release Race (Manual Tag + Auto Version)

Symptom:

- CI fails trying to push a tag that already exists

Cause:

- A tag was pushed manually while `version.yml` also tried to create the same version tag

Current behavior:

- `version.yml` checks for an existing version tag on `HEAD` and skips safely

Recommendation:

- Let `version.yml` own version tags unless you are intentionally rebuilding an existing tag via manual release dispatch

## Download Verification (Checksums)

Recent Windows releases include `SHA256SUMS.txt`.

If a download looks suspicious or Windows reports corruption:

1. Download `SHA256SUMS.txt` from the release page
2. Run `Get-FileHash -Algorithm SHA256` on the downloaded ZIP/EXE
3. Compare the hash to the published checksum

## Windows SmartScreen / Unsigned EXE Warning

Symptom:

- Windows warns that the app is from an unknown publisher

Cause:

- The artifact is unsigned (or signing is not configured in CI)

Current CI behavior:

- Release/build workflows include optional code-signing placeholders
- If signing secrets are not configured, builds still complete and log that signing was skipped
- Release builds also generate `SIGNING_STATUS.txt` and `SHA256SUMS.txt` for transparency/verification

If you maintain releases:

- Configure the signing secrets described in `docs/RELEASE_PROCESS.md`
- Rebuild the release to produce signed artifacts
