# Firstchair

Read ROADMAP.md and TODO.md to identify the current milestone. Keep changes
scoped to a testable slice. Run `PYTHONPATH=src python -m unittest discover -s tests -v`.

Use synthetic provider fixtures and temporary directories. Keep local transcripts,
account data and credentials out of Git, logs, tests, issues and PRs. Provider
profiles inherit explicit controller policy. New live adapters require documented
non-interactive contracts and fail-closed handling for unsupported versions.

## Lead and workers

The active Claude Code, Codex or Grok Build session leads. When the user
requests delegation, identify the active lead explicitly and dispatch scoped
tasks through `firstchair delegate run auto --lead claude|codex|grok` (choose
one lead value). In a source checkout, `python3 scripts/delegate.py` is also
available. The dispatcher can launch Codex and Grok Build workers.
See `docs/orchestration.md` for the lead workflow. A dispatched worker runs in its own git
worktree and receives its mode (`read` or `write`) and task in the prompt.
Workers edit only inside that worktree, never run Git write commands or
package installs, and end with Summary, Files changed, Verification and
Open issues sections. The lead reviews, merges and commits.
