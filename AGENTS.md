# TriadMux

Read ROADMAP.md and TODO.md to identify the current milestone. Keep changes
scoped to a testable slice. Run `PYTHONPATH=src python -m unittest discover -s tests -v`.

Use synthetic provider fixtures and temporary directories. Keep local transcripts,
account data and credentials out of Git, logs, tests, issues and PRs. Provider
profiles inherit explicit controller policy. New live adapters require documented
non-interactive contracts and fail-closed handling for unsupported versions.
