# Firstchair

Firstchair is a local-first CLI that makes the coding assistants you already
use check each other's work. One model leads: it plans, then a second model
reviews that plan, and the lead writes the final answer taking the review
into account. Firstchair drives Codex CLI, Claude Code and Grok Build through
their own headless modes and sign-ins, runs them read-only, and keeps a
record of every run on your machine.

```sh
firstchair run --provider codex --reviewer claude --workspace . --format text \
  "Find the riskiest error handling in src/ and propose fixes"
```

Formerly TriadMux. The `triadmux` command still works for one release and
prints a notice. An existing `.triadmux/` state directory is read when
`.firstchair/` does not exist.

## Quick start

Requires Python 3.12 or later and at least one of Codex CLI, Claude Code or
Grok Build, installed and signed in.

```sh
pipx install git+https://github.com/GrayManSam/firstchair   # or: pip install -e . from a checkout
firstchair doctor
firstchair run --provider codex --format text "Explain what this project's tests cover"
firstchair runs
firstchair status <run-id>
```

`doctor` locates Codex, Claude Code and Grok executables on PATH, runs each
one's `--version`, and reports whether that version is verified, compatible
or unsupported. `doctor --offline` only searches PATH.

## Live runs

`firstchair run --provider PROVIDER TASK` runs three stages:

1. **plan**: the lead provider plans the task.
2. **review**: the reviewer critiques the plan. It defaults to the lead;
   pass `--reviewer` to get a second model's opinion.
3. **synthesize**: the lead writes the final answer from its plan and the review.

| Option | Effect |
| --- | --- |
| `--reviewer codex\|claude\|grok` | Provider for the review stage |
| `--fallback codex\|claude\|grok` | Extra provider used when an earlier one is out of usage. Repeat once for a third |
| `--workspace DIR` | Directory providers may read. Without it they run in an empty temporary directory |
| `--profile NAME`, `--reviewer-profile NAME` | Use a named sign-in from `firstchair auth login` |
| `--timeout SECONDS` | Per-stage limit (default 600) |
| `--total-timeout SECONDS` | Budget across all stages |
| `--format text` | Print the plan, review and result instead of the JSON record |
| `--dry-run` | Show roles, versions and limits without starting a model |
| `TASK` = `-` | Read the task from stdin |

Providers run **read-only**: Codex uses its `read-only` sandbox, Claude Code
gets only `Read`, `Grep` and `Glob`, and Grok Build gets only `read_file`,
`list_dir` and `grep` with deny-by-default permissions. MCP servers are
switched off for all three. API key variables are never passed to a provider,
so each one uses its own native sign-in. On timeout or Ctrl-C the provider's
whole process group is killed and the run is recorded as failed or
interrupted. Each run record keeps every stage's text, provider version and
token usage. Usage is `measured` when the provider reports counts, `partial`
when only some stages did, and `unknown` otherwise. Token counts are not a
bill.

A named provider that is out of usage (`rate_limited`), unavailable, or
timed out is skipped. Firstchair keeps the stages already finished and
gives the rest of the run to the next named provider, so two providers
can become one and still finish. A login or authorization failure stops
the run instead of switching providers. `firstchair resume RUN_ID`
continues an interrupted run, or a run that stopped because every named
provider was out of usage, from the last finished stage. Add `--provider`
on resume to hand the remainder to a provider that still has usage.
Unknown provider versions are refused before a run starts.

## Offline demo

The demo and bundled synthetic provider need no sign-in:

```sh
firstchair run --demo "Review the project's build instructions"
``` The bundled synthetic provider
is ready offline. Run records can contain your task and result. Before a
record is stored, secret environment values of at least 12 characters are
replaced with `[redacted]`. Provider subprocesses receive an allowlisted
environment and do not inherit API keys. Records live in the ignored
`.firstchair/` directory by default. Use `firstchair --state-dir PATH`
to select another location.

The bundled synthetic subprocess adapter simulates a read-only handoff. Run
it by explicitly choosing `--provider synthetic` and passing a task. On success,
the run record includes the worker's structured review and the synthesis
result. Offline runs record token usage as unknown with null counts.

```sh
firstchair run --provider synthetic --dry-run --timeout 5 --total-timeout 10 "Review the build"
firstchair run --provider synthetic --timeout 5 --total-timeout 10 "Review the build"
```

`--dry-run` explains provider selection and shows the stage limits without
starting workers or creating a run record. For `--provider synthetic` it
also reports `"workspace": "temporary"`: each stage runs in a controller
temporary directory. `--max-input-bytes` applies to each
UTF-8 JSON request, including the envelope. Oversized requests fail with
`input_limit` before worker startup. Each worker also has a stdout byte limit
and a timeout. `--total-timeout` sets a shared budget across stages and reports
`budget_exhausted` when it expires. Cleanup can add time before the command
returns.

Pass `--config limits.toml` to reuse synthetic limits. Explicit flags take
precedence over the file, and omitted values use the bundled defaults. Select
the run mode on the command line.

```toml
[synthetic]
timeout = 5
total_timeout = 10
max_input_bytes = 65536
max_output_bytes = 65536
```

Use `firstchair runs` to find saved runs by ID, status, and stage. On POSIX,
`firstchair recover <run-id>` marks an abandoned run as interrupted once the
controller releases its run lock. Recovery updates the record only.
It requires a lock file created by the original run. Keep each run's
`.lock` file alongside its JSON record. A lifetime pipe stops bundled POSIX
workers when their controller dies.

A live provider that is killed with SIGKILL together with its controller is
not stopped by the lifetime pipe. Use `firstchair recover` to mark that run.

## Verification

CI is configured for Ubuntu 24.04 with Python 3.12–3.14 and macOS with Python
3.12. The release workflow installs the wheel on Ubuntu with Python 3.12
and compares a completed synthetic workflow with its saved status. A public
release is an annotated tag named `v` plus the package version. The workflow
publishes that changelog section and rejects every other tag.

Run the tests with `PYTHONPATH=src python -m unittest discover -s tests -v`.
See [the roadmap](ROADMAP.md) for alpha, beta and release gates and
[the to-do list](TODO.md) for the next implementation slice.

## Multi-agent development

Maintainers can lead development from Claude Code, Codex, or Grok Build.
The primary seat is the conductor. `firstchair conduct` runs a score that
can start the lead's own provider and the other two. `firstchair delegate`
still runs one bounded task. Each worker gets a Git worktree outside the
checkout. Read tasks use a disposable worktree. Write tasks keep branch
`delegate/NAME` for review. See [the orchestration guide](docs/orchestration.md).
Delegation uses your existing provider logins. Unlike `firstchair run`,
write-mode delegation lets a worker edit files inside its worktree.

```sh
firstchair delegate run auto --lead codex --dry-run
firstchair delegate run auto --lead codex --name parser-review "Review the parser tests"
firstchair conduct plan --lead grok --score score.json
firstchair conduct run --lead grok --name rehearsal --score score.json
firstchair delegate list
```

Grok loads `AGENTS.md` and `.grok/` only in a trusted folder. Run
`grok --trust` once in the checkout. Worktrees of a trusted checkout inherit it.

Use `firstchair auth login PROVIDER PROFILE` to sign in through the provider
CLI, and `firstchair auth list` to see local aliases. The orchestration guide
describes credential storage and how to select an account for a worker.

## Grok project files

Grok discovers agents under `.grok/`, the `firstchair` plugin, and that
plugin's `provider-fixture` skill. Those files stay in the repository for
offline fixture and parser work.

Firstchair is independently maintained and released under the [MIT license](LICENSE).

See the [upstream review](docs/upstream-review.md) and
[provider contract inventory](docs/provider-contracts.md) for the adapter plan.
