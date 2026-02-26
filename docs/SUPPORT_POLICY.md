# Support Policy

This document defines the support scope and priorities for Producer-OS.

It helps users understand what is officially supported, what is best-effort, and what information to include when requesting help.

## Support Scope

### Supported (Primary)

- Windows release builds (portable ZIP and installer)
- `.wav` classification workflows
- Windows source installs (CLI and GUI) with Python `3.11+`
- Current `main` branch development for contributors (best effort, with reproducible steps)

### Best-Effort / Experimental

- non-Windows source installs (Linux/macOS)
- custom/local forks with modified classification rules or bucket vocab
- non-`.wav` sample classification behavior
- older historical releases with known packaging/toolchain issues

Best-effort means maintainers may still help, but fixes may be delayed or require community contributions.

## What Maintainers Need for Helpful Support

When opening an issue or asking for support, include:

- Producer-OS version (tag or commit)
- operating system and version
- Python version (if source install)
- whether you are using CLI or GUI
- exact command or action taken
- expected vs actual behavior
- relevant logs/output (redacted)

## What Maintainers Usually Cannot Support

- private sample packs or copyrighted content uploads
- debugging heavily modified local forks without a minimal repro
- issues with incomplete environment setup details

## Security and Privacy Notes

- Producer-OS is local-first and does not ship telemetry/analytics
- Do not post private audio files publicly
- Redact personal paths or account names before sharing logs/screenshots

## Where to Ask

- Bugs / concrete feature requests: GitHub Issues
- Questions / tuning help / design discussion: GitHub Discussions (when enabled)
- General help: [`SUPPORT.md`](../SUPPORT.md)

## Related Docs

- [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`docs/SYSTEM_REQUIREMENTS.md`](SYSTEM_REQUIREMENTS.md)
- [`docs/COMPATIBILITY_POLICY.md`](COMPATIBILITY_POLICY.md)

