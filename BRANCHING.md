# Branching Policy

## Roles

- `main`: release/stable only
- `dev`: integration branch for active work and dev builds

## Workflow

1. Create `feature/*` branches from `dev`.
2. Merge feature branches into `dev`.
3. Run dev builds/tests from `C:\producer_os_dev`.
4. Open a PR from `dev` to `main` when ready to release.
5. Tag and release from `main` only.
6. Merge `main` back into `dev` after each release (or cherry-pick as needed).

## Hotfix Flow

1. Create `hotfix/*` from `main`.
2. Merge hotfix into `main` first.
3. Merge or cherry-pick the hotfix into `dev`.

## Branch Protection (Target State)

### `main` (strict)

- Require pull requests before merging
- Require status checks
- Require CODEOWNERS review
- Block force pushes and deletion

### `dev` (lighter)

- Require at least Python CI (PR requirement is optional for solo development)
- Block force pushes and deletion

## Worktrees

- `C:\producer_os_dev` -> `dev` (dev work/builds)
- `C:\producer_os_main` -> non-dev/release builds (detached `HEAD` is acceptable)

If you need to commit from `C:\producer_os_main`, create a writable local branch:

```powershell
git switch -c main-build --track origin/main
```
