# Roadmap

This roadmap is a public planning document for Producer-OS.

It helps contributors understand:

- what is actively being improved
- what work is good for first contributions
- what larger efforts need design discussion first

Producer-OS priorities remain:

- deterministic behavior
- safety-first file operations
- explainable classification/reporting
- idempotent runs

## Now (Active Focus)

- Hybrid WAV classifier tuning and regression protection
- GUI low-confidence review workflow polish
- Windows release hardening (packaging, smoke tests, signing rollout)
- Performance improvements for large sample libraries
- Contributor experience and documentation

## Next (Planned)

- Review-driven rule correction UX improvements
- Better benchmark/report comparison for classifier tuning
- Additional Windows path edge-case coverage
- Expanded CLI reference and architecture diagrams
- Optional parallel feature extraction tuning/perf validation

## Later (Design / Larger Scope)

- Richer preview-before-apply workflows for large batch operations
- More maintainer tooling around labeling/release QA
- Broader platform validation (source install support beyond Windows)
- Additional safe automation around routing/style repair workflows

## Starter Issue Seeds (Recommended to Open and Label)

These are good candidates for maintainers to create/track as GitHub issues.

### Good First Issue

Apply labels:

- `good first issue`
- `help wanted`

Seeds:

- Add more screenshots/GIFs to `docs/` and `README.md`
- Improve error text for common config/schema validation failures
- Expand `docs/TROUBLESHOOTING.md` with more examples from user reports
- Add more examples to `docs/CLI_REFERENCE.md`
- Improve GUI tooltips for low-confidence review fields

### Help Wanted (Intermediate)

Apply labels:

- `help wanted`
- area label(s): `gui`, `engine`, `tests`, `docs`, `ci`, `perf`

Seeds:

- Add benchmark report visual summary helper (local script)
- Extend auto-labeler mappings for more file areas
- Add release checksum verification instructions to GitHub release template/docs
- Add architecture diagram asset for `docs/ARCHITECTURE.md`
- Expand Windows-path tests for more locked-file scenarios

### Design Discussion First

Before opening implementation PRs, start a discussion for:

- changes to default bucket definitions/keywords
- destructive behavior changes
- non-deterministic classification techniques (not currently in scope)
- major workflow/versioning/release automation changes

## How To Contribute Against This Roadmap

- Use [`docs/CONTRIBUTOR_QUICKSTART.md`](docs/CONTRIBUTOR_QUICKSTART.md) to set up your environment
- Open an issue (or discussion) before large changes
- Keep changes small and test-backed where possible
- Preserve safety-first defaults and explainability

## Community Notes

- Questions, ideas, and design discussions should go to GitHub Discussions once enabled in repo settings
- Bugs and feature requests should use the GitHub Issue templates

