# Producer OS - Rules, Usage, and Safety Guarantees

This document summarizes how Producer-OS is intended to be used and what each
mode is allowed to do.

## Safety Rules

### 1. `analyze` is read-only

`analyze` is the safest mode. It classifies files and returns a report, but it
must not modify the inbox or hub.

```bash
producer-os analyze <inbox> <hub>
```

### 2. `dry-run` previews routing

`dry-run` shows what would happen without moving or copying files. It may write
logs/reports, but it should not copy/move files or write `.nfo` style files.

```bash
producer-os dry-run <inbox> <hub>
```

### 3. `copy` preserves the inbox

`copy` writes organized files into the hub while leaving the source inbox
unchanged.

```bash
producer-os copy <inbox> <hub>
```

### 4. `move` is destructive (with audit trail)

`move` relocates files from inbox to hub. Use it only after validating with
`analyze` or `dry-run`.

```bash
producer-os move <inbox> <hub>
```

### 5. Style repair and undo are explicit actions

- `repair-styles` regenerates missing/misplaced `.nfo` files in the hub
- `undo-last-run` attempts to roll back the last move using the audit trail

```bash
producer-os repair-styles <hub>
producer-os undo-last-run <hub>
```

### 6. Placeholder commands are not implemented yet

`preview-styles` and `doctor` exist as CLI placeholders and currently return a
"not implemented" error.

## Portable Mode

Portable mode can be enabled in two ways:

- Add `--portable` (or `-p`) to supported CLI commands
- Create a `portable.flag` file next to the application / in the app directory

When `portable.flag` exists, it takes precedence over the CLI flag.

## Configuration Files

Producer-OS uses these runtime config files:

- `config.json`
- `buckets.json`
- `bucket_styles.json`

By default, these live in the platform config directory (for example,
`%APPDATA%\ProducerOS` on Windows). In portable mode they are stored locally
next to the app.

Starter examples are available in `examples/`.

## Common CLI Usage

```bash
# CLI help
producer-os --help

# Module entrypoint (CLI)
python -m producer_os --help

# Module entrypoint (GUI)
python -m producer_os gui

# Verbose dry run with portable mode
producer-os dry-run <inbox> <hub> --verbose --portable

# Copy while forcing overwrite of .nfo sidecars
producer-os copy <inbox> <hub> --overwrite-nfo
```

## Recommended Workflow

1. Run `analyze`
2. Run `dry-run` if you want logs/reports without file copies/moves
3. Run `copy` on a real dataset first
4. Use `move` only after validating rules and destination layout
