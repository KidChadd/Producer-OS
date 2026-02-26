# Compatibility and Deprecation Policy

This document describes what compatibility Producer-OS tries to preserve and how deprecations are handled.

Producer-OS is still evolving quickly, so this policy prioritizes clarity over rigid guarantees.

## Compatibility Priorities

Highest priority compatibility (avoid breaking without notice):

- safety-first behavior defaults (non-destructive expectations)
- `.wav`-only deterministic classification constraints
- core CLI commands (`analyze`, `dry-run`, `copy`, `move`, `undo-last-run`)
- report reasoning transparency (additive changes preferred)

Medium priority compatibility:

- GUI layouts and workflow affordances
- benchmark report schema (additive changes preferred)
- config file structure for active versions

Lower priority compatibility (may change with less notice):

- internal modules/APIs not documented as public extension points
- experimental or developer-only options
- CI/workflow internals and helper scripts

## Deprecation Approach

When a behavior, field, or option needs to change:

1. Prefer additive changes first (new fields/options instead of replacing existing ones)
2. Document the change in:
   - `CHANGELOG.md`
   - relevant docs (`README.md`, `docs/*`)
3. Keep compatibility shims where reasonable for at least one release cycle
4. Provide a migration note when user action is required

## Config and Report Schema Guidance

Preferred changes:

- add new keys
- add optional fields
- preserve existing key meanings

Avoid when possible:

- renaming keys without fallback
- changing field types
- silently changing safety-critical defaults

## CLI Compatibility Guidance

Preferred:

- add new subcommands/flags
- keep existing flags working
- add aliases before removing names

If a CLI flag must change:

- keep the old flag temporarily (if practical)
- print a deprecation warning
- document the replacement clearly

## What Counts as a Breaking Change (Examples)

- changing `analyze` to write files by default
- changing routing logic in a way that makes prior bucket expectations invalid without notice
- removing report reasoning fields used by the GUI or user workflows
- changing config file locations unexpectedly

## Exceptions

Breaking changes may happen faster when required for:

- data safety
- security fixes
- severe release-packaging failures
- clearly broken behavior that cannot be safely preserved

These should still be documented clearly in the changelog and release notes.

## Related Docs

- [`CHANGELOG.md`](../CHANGELOG.md)
- [`docs/SUPPORT_POLICY.md`](SUPPORT_POLICY.md)
- [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md)

