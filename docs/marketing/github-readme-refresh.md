# README opening, draft

Do not paste this over `README.md` until the name decision is settled.
The draft keeps the command as `triadmux`. It mentions Benchdog once,
as provisional, so the repository does not pretend the rename happened.

```markdown
# TriadMux

TriadMux is a local-first CLI for a bounded coding handoff. Version
**0.0.0** discovers Codex, Claude Code, and Grok on `PATH` and does not
launch them. It runs a synthetic plan, review, and synthesis on your
machine and stores the record locally.

Benchdog is a provisional name under review. The command you install
is `triadmux`.

## What works in this version

- `triadmux doctor` reports which of those tools are on `PATH`.
- `triadmux run --demo` runs the in-process demo.
- `triadmux run --provider synthetic` runs the same three stages in a
  temporary workspace, with timeouts and byte limits.
- `--dry-run` prints the plan and does not write a record.
- Saved runs redact long secret-like environment values. Usage is
  recorded as unknown.
- Live adapters are disabled.

## Quick start

Requires Python 3.12 or later.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
triadmux doctor
triadmux run --demo "Review the project's build instructions"
```

## What this version does not do

It does not send your task to Codex, Claude Code, or Grok. It does not
measure tokens or cost. It does not switch accounts. It is not Claude
Swap, and it is not affiliated with Anthropic, OpenAI, xAI, or the
Claude Swap maintainer. See [the upstream review](docs/upstream-review.md).

The license is MIT.
```

## GitHub description and topics

Description, 80 characters or so:

```text
Local CLI for a synthetic coding handoff. Live adapters are disabled.
```

Topics to set on the public repository when a maintainer wants them.
These describe the tree, not a hoped-for product:

`python` `cli` `coding-agents` `local-first` `mit`

Skip `tmux`, `orchestrator` as a boast, and vendor names.

## Social card

Direction A, when exported: maple ground, peg mark, "TriadMux",
"Local synthetic handoff. Live tools stay off.", and "0.0.0".
1200×630. Not exported in this change.
