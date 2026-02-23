# Producer OS

Producer OS is a desktop tool for organising music sample packs and
applying FL Studio folder styling via `.nfo` sidecar files.  It
provides a wizard‑driven GUI experience backed by a deterministic
engine and a command‑line interface for power users.  The default
behaviour is safe and idempotent – it copies files rather than
moving them, never deletes user content and logs every decision.

## Features

- **Wizard GUI**: Step through inbox selection, hub location,
  options and run/repair pages with a modern PySide6 interface.
- **CLI**: Perform `analyze`, `dry-run`, `copy`, `move`,
  `repair-styles`, `preview-styles`, `doctor` and `undo-last-run`
  operations from the terminal.
- **Deterministic routing**: Files are classified into fixed buckets
  based on simple string‑matching rules with a confidence score.  Low
  confidence files are routed to an `UNSORTED` folder.  Decisions
  and scores are recorded in an audit log when moving files.
- **Style system**: Bucket and category styles are defined in
  `bucket_styles.json` and applied to category, bucket and pack
  folders via `.nfo` files.  Missing styles fall back to sensible
  defaults and never interrupt execution.
- **Bucket renames**: Users can rename buckets via `buckets.json`
  without affecting the internal classification.  Renamed folders
  remain properly styled and repair runs reconcile any mismatches.
- **Idempotent and safe**: Re‑running on the same inbox/hub pair
  performs no duplicate actions.  Move operations are fully
  undoable via an audit trail.  A repair mode regenerates missing
  styles and removes orphans without touching audio files.
- **Portable or AppData modes**: Settings, styles and bucket
  mappings live in `%APPDATA%/ProducerOS` by default.  Create a
  `portable.flag` file next to the executable to store them in
  the application directory.
- **Open source**: Released under the GPL‑3.0‑or‑later license.

## Quickstart

Install the package and run the CLI:

```bash
python -m producer_os.cli analyze /path/to/inbox /path/to/hub
```

Or launch the GUI (requires PySide6):

```bash
python -m producer_os.gui
```

The first time you run Producer OS it will ask for your inbox and
hub folders.  Subsequent runs remember your settings.  Use the
`copy` command to organise your packs without altering the inbox
folders.  Switch to `move` when you’re confident everything is
working correctly – you can always undo the last move.

For more information see the in‑app help and documentation.

### Running the GUI

The GUI requires PySide6.  If it is not installed you will see an error
message when launching.  Install it with:

```bash
pip install PySide6
```

Then run:

```bash
python -m producer_os.gui
```

The wizard will guide you through selecting your inbox (source) and hub
(destination), choosing options such as move/copy, preserving vendor
structure and theme, and running the analysis or sort.  Results and logs
are displayed in the final step.  Use the developer tools toggle on the
Options page to access the config folder, open the last report and
validate JSON schemas.

### Building an executable (brief)

Producer OS can be bundled into a self‑contained Windows executable
using Nuitka or PyInstaller.  The recommended approach is Nuitka
because it produces faster, single‑folder deployments.  A simple
workflow is:

```bash
nuitka --onefile --follow-imports --output-dir=dist src/producer_os/gui.py
```

Then create an installer (e.g. with Inno Setup) or zip the resulting
folder for portable use.  The repository includes a GitHub Actions
workflow that performs this build automatically on Windows runners.

### Basic test plan

1. **Dry run**: Select a small inbox and hub, enable “Dry run” and
   click “Run”.  Verify that no files are moved or copied in the hub.
2. **First real run**: Uncheck “Dry run”, choose “Copy” in Step 2
   and click “Run”.  Confirm that files appear in the hub under the
   expected category/bucket folders and that `.nfo` files are written
   only next to folders (not next to individual WAVs).
3. **Second run**: Without changing anything, click “Run” again.
   Verify that the summary reports zero moved/copied files and no
   duplicate “(2)” files are created – the operation is idempotent.

This test plan ensures the GUI correctly drives the engine, that
options are respected, and that nothing unexpected happens when
running repeatedly.