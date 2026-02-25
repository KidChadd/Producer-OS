```markdown
<p align="center">
  <h1 align="center">Producer OS</h1>
  <p align="center">
    Structured sample management.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" />
  <img src="https://img.shields.io/badge/Build-Nuitka-purple" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## Overview

Producer OS is a structured system for organizing sample packs and production assets.

It transforms unstructured folders into a clean, repeatable hub layout — without destructive behavior.

Designed for long-term use.

---

## Core Principles

- Safe by default  
- Transparent in operation  
- Re-runnable without duplication  
- Strict separation of responsibilities  
- Logging-first architecture  

---

## What It Does

- Wraps loose files into pack folders  
- Routes content into defined buckets  
- Preserves vendor structure (optional)  
- Logs every action  
- Quarantines uncertain input  
- Avoids reprocessing organized packs  

---

## Output Structure

```

Hub/
├── Drum Kits/
├── Samples/
├── FL Projects/
├── MIDI Packs/
├── Presets/
├── UNSORTED/
└── Quarantine/

```

Clean. Predictable. Repeatable.

---

## Architecture

```

UI Layer        → User interaction
Engine          → Sorting logic
Services        → Config / Styles / Buckets
CLI             → Headless execution
Tests           → Validation

````

No combined responsibilities.

---

## Execution

Development:

```bash
pip install -r requirements.txt
python -m producer_os.producer_os_app
````

Build (Nuitka):

```bash
python -m nuitka --standalone --enable-plugin=pyside6 build_gui_entry.py
```

---

## Safety Model

* No deletion by default
* Low-confidence → `UNSORTED`
* Suspicious input → `Quarantine`
* All actions logged

---

## Re-Run Behavior

First run:

* Distributes content

Second run:

* Skips previously processed packs
* Prevents duplication

Designed for repeated execution.

---

## Roadmap

* Waveform-based classification
* BPM / key detection
* Rule editor in UI
* Advanced duplicate detection

---

Producer OS is not a script.

It is a structured production environment.

```

---

# 🎯 Why This Works Better

- Short sentences
- No fluff
- Clear hierarchy
- Minimal emotion
- Controlled tone
- White space
- Quiet confidence

It now feels like:
- A productivity tool
- A system
- Intentional software
- Not a hobby project

---
Say **“Ultra minimal”** if you want to push it even cleaner.
```
=======
---

# 📄 `/README.md` (Premium Version)

```markdown
# 🎛 Producer OS

> A structured sample management system built for serious music producers.

Producer OS transforms chaotic sample libraries into a clean, categorized, production-ready hub.

Designed for:
- FL Studio users
- Organized creatives
- Power producers with large libraries
- Developers who value transparent logic

---

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Build](https://img.shields.io/badge/Build-Nuitka-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

# 🚀 Why Producer OS Exists

Most producers collect thousands of samples.

Over time:
- Folders get messy  
- Packs overlap  
- Duplicates multiply  
- Vendor structure becomes inconsistent  
- Retrieval slows down creativity  

Producer OS solves this without destroying your original structure.

It doesn’t just sort files.

It builds a **production system.**

---

# 🧠 Core Capabilities

### 📦 Pack Wrapping
Loose files are automatically grouped into structured pack folders.

### 🗂 Intelligent Bucket Routing
Samples are categorized into:

- Drum Kits
- Samples
- FL Projects
- MIDI Packs
- Presets
- UNSORTED
- Quarantine

Routing is based on:
- File extensions
- Folder keywords
- Confidence scoring
- Safety thresholds

---

### 🔍 Transparent Logging
Every run generates:

```

logs/<run_id>/

```

With:
- Detailed move report
- Reasoning for bucket decisions
- Skipped file explanations
- Confidence breakdown (developer mode)

Nothing happens silently.

---

### 🔐 Safety by Default

Producer OS will NEVER:

- Delete your files by default
- Overwrite without logging
- Destroy vendor structure
- Reprocess already organized packs
- Trust low-confidence matches

Low-confidence files go to:

```

UNSORTED

```

Suspicious input goes to:

```

Quarantine

```

You remain in control.

---

# 🖥 GUI Experience

Producer OS includes a wizard-based interface:

1. Select Inbox folder
2. Select Hub folder
3. Choose options
4. Run distribution

### 🎨 Theme System
- System
- Dark
- Light

Theme preference persists between runs.

---

# 🧩 Architecture Overview

Producer OS is built with strict separation of concerns:

```

UI Layer        → Input & Display
Engine          → Sorting Logic
Services        → Config / Styles / Buckets
CLI             → Headless Execution
Tests           → Validation

```

No mega scripts.
No hidden behavior.

---

# 🔁 First Run vs Second Run

### First Run
- Wrap loose files
- Distribute to buckets
- Generate structured log

### Second Run
- Detect already processed packs
- Skip duplicates
- Log skipped operations
- No "(2)" folder spam

It is designed to be rerun safely.

---

# 🧪 Developer Mode

When enabled:

- Displays rule scoring
- Shows bucket confidence
- Outputs matching breakdown
- Provides detailed reasoning in logs

Built for transparency.

---

# 📂 Example Hub Structure

```

Hub/
├── Drum Kits/
│    └── PackName/
├── Samples/
│    └── PackName/
├── FL Projects/
├── MIDI Packs/
├── Presets/
├── UNSORTED/
└── Quarantine/

```

Each bucket can have:
- Custom icon
- Custom color
- Optional NFO metadata

---

# 📦 Installation

## Development

```

pip install -r requirements.txt
python -m producer_os.producer_os_app

```

## Build Executable (Nuitka)

```

python -m nuitka 
--standalone 
--enable-plugin=pyside6 
--windows-console-mode=disable 
build_gui_entry.py

```

---

# 🧭 Project Philosophy

Producer OS follows strict development rules:

- Safety > Speed
- Logging > Guessing
- Structure > Chaos
- Iteration > Rush
- Clarity > Cleverness

Changes follow a controlled workflow:
1. Define goal
2. List changes
3. Define test plan
4. Approve (“go”)
5. Implement
6. Verify
7. Repeat

---

# 🔓 Open Source Commitment

Producer OS is:

- Fully open source
- Transparent in logic
- Designed for extension
- Built for long-term maintainability

We welcome contributions — see `CONTRIBUTING.md`.

---

# 🛣 Roadmap

Planned expansions:

- Waveform-based classification
- BPM & key detection scoring
- Preset metadata parsing
- Advanced duplicate detection
- Rule editor inside GUI
- CI validation pipeline
- Plugin-aware routing

---

# 🎯 Who This Is For

If you:

- Have 50+ sample packs
- Hate messy folders
- Care about clean systems
- Want reproducible structure
- Value transparent logic

Producer OS was built for you.

---

Producer OS isn’t just a sorter.

It’s the foundation of a clean production environment.
```

---
