# Getting Support

If you encounter a bug or have a feature request for Producer-OS,
please open an issue in the GitHub repository.

When reporting problems, include:

- Operating system and version
- Python version
- Exact command used (CLI) or action sequence (GUI)
- Expected behavior vs actual behavior
- A sample `run_report.json` when possible

Logs and reports are typically written under the hub folder at
`<hub>/logs/<run_id>/`.

GUI tips:

- Use **Save run report...** on the Run page after an analyze/run
- In Developer Tools, use **Open last report** and **Open config folder**

CLI tip:

- Redirect CLI JSON output to a file, for example:
  `producer-os analyze <inbox> <hub> > run_report.json`

For general questions or suggestions, open a GitHub issue (or GitHub Discussions
if enabled for the repository).

Support scope and compatibility expectations:

- `docs/SUPPORT_POLICY.md`
- `docs/COMPATIBILITY_POLICY.md`
