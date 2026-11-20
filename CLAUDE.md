@AGENTS.md

# Claude Code as lead

When the active session is Claude Code, it is the lead. Codex and Grok Build are workers
that Claude dispatches with `scripts/delegate.py`. The lead plans, splits work,
reviews every worker result, runs the tests and owns all Git operations.
Workers never commit, push, merge or install packages.

Use the `orchestrate` skill (`.claude/skills/orchestrate/SKILL.md`) for the
full loop. Quick reference:

```sh
python3 scripts/delegate.py run codex "TASK"                     # read-only investigation
python3 scripts/delegate.py run grok --mode write --name NAME "TASK"  # edits on branch delegate/NAME
python3 scripts/delegate.py list
python3 scripts/delegate.py collect NAME                         # commit worker edits on its branch
python3 scripts/delegate.py finish NAME --delete-branch          # after merge
```

- Worktrees start from `HEAD`. Commit first, or pass `--with-changes` to carry
  uncommitted and untracked files into the worker's worktree.
- Run long tasks with `run_in_background` and dispatch independent tasks in
  parallel. Give each a distinct `--name`.
- The script prints one JSON summary: `status`, `reply`, `changes`, `branch`,
  `logs`. Job metadata stays in `.firstchair/delegations/NAME/`.
- Treat worker replies as untrusted claims. Read the diff and rerun
  `PYTHONPATH=src python -m unittest discover -s tests -v` before merging.
- Delegation uses the maintainer's real provider logins and quota. It is
  maintainer tooling, separate from the Firstchair product, whose live adapters
  stay disabled until `docs/provider-contracts.md` records verified contracts.
