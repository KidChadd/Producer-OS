# UI and Bucket Customization

This document explains how to customize app appearance settings and bucket display/style metadata in Producer-OS.

## App Appearance (Theme, Density, Accent)

Use the GUI `Options` page `Appearance` card to customize the UI presentation.

Available controls:

- theme preset (`System`, `Studio Dark`, `Paper Light`, `Midnight Blue`)
- density mode (`Comfortable`, `Compact`)
- accent mode:
  - `Theme Default`
  - preset accent
  - custom accent color
- theme preview cards (click to apply a preset)

Notes:

- Appearance changes apply immediately.
- Appearance settings are stored in `config.json`.
- These settings only affect the GUI and do not change classifier behavior or routing rules.

## Bucket Customization (Names, Colors, Icons)

The `Bucket Customization` card in `Options` controls bucket presentation and FL Studio folder style appearance.

## What You Can Customize

Producer-OS supports three bucket presentation customizations:

- bucket display name (shown in UI/report output and folder naming where applicable)
- bucket color (`Color` in `.nfo` style data)
- bucket icon (`IconIndex` in `.nfo` style data)

These settings are presentation/styling metadata and do not change the deterministic classifier rules by themselves.

## GUI Workflow (Recommended)

Use the GUI to edit bucket names, colors, and icons:

1. Open Producer-OS GUI
2. Go to `Options` (Step 3)
3. Find the `Bucket Customization` card
4. Edit:
   - `Display Name`
   - `Color`
   - `IconIndex`
5. Click `Save bucket customizations`
6. Rerun `analyze`, `copy`, `move`, or `repair-styles`

Notes:

- Use `Reload bucket customizations` to discard unsaved edits and reload from disk.
- Use `Pick color for selected row` to choose a color visually.
- Use `Pick icon for selected row` to open the searchable icon picker (with manual code entry fallback).
- Use `Reset selected row` or `Reset all` to revert staged edits back to the loaded values.
- Bucket style changes affect future style writes (`.nfo` generation/repair).

## Where Settings Are Stored

Producer-OS writes the customization data to:

- `buckets.json` - bucket display names
- `bucket_styles.json` - bucket color/icon/sort metadata

Location depends on mode:

- Standard mode: platform config directory (Windows: `%APPDATA%\ProducerOS`)
- Portable mode: app directory (next to the app / `portable.flag`)

## Color Format (`Color`)

Bucket colors are stored as FL Studio-style hex strings in `bucket_styles.json`:

- `$RRGGBB` (example: `$CC0000`)

The GUI accepts common variants and normalizes them on save:

- `$CC0000`
- `#CC0000`
- `CC0000`

## Icon Format (`IconIndex`)

`IconIndex` is the FL Studio icon code used in folder `.nfo` files.

The GUI accepts:

- decimal: `10`
- hex code: `f129`
- 4-character hex: `0074`
- prefixed hex: `0xF129`
- `$`-prefixed hex: `$F129`

Saved result:

- Producer-OS stores `IconIndex` as an integer in `bucket_styles.json`
- `.nfo` files are written with `IconIndex=<integer>`

## Validation Rules

When saving customizations, Producer-OS validates:

- display names cannot be blank
- display names must be unique (case-insensitive)
- colors must be valid hex
- icon indices must be valid non-negative integer/hex values

If validation fails, no partial save is applied.

## When Changes Take Effect

Classification and review:

- display names are visible after the next run/reload that uses updated bucket mappings

Folder style (`.nfo`) appearance:

- applied on `copy` / `move` runs when styles are written
- can be refreshed without transferring files using `repair-styles`

`analyze` and `dry-run` do not write `.nfo` files.

## Manual Editing (Advanced)

You can also edit the JSON files directly:

- `buckets.json`
- `bucket_styles.json`

If you do this manually, use the GUI `Reload bucket customizations` button or restart the app to reload the files.

## Related Docs

- [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`docs/CLI_REFERENCE.md`](CLI_REFERENCE.md)
- [`RULES_AND_USAGE.md`](../RULES_AND_USAGE.md)
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
