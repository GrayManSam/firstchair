# Firstchair

Firstchair is a local-first CLI for coordinating coding assistants. Version
**0.0.0** demonstrates a leader, reviewer, and synthesis handoff using
deterministic synthetic stages. It keeps run records on the local machine.

Formerly TriadMux. The `triadmux` command still works for one release and
prints a notice. An existing `.triadmux/` state directory is read when
`.firstchair/` does not exist.

## Quick start

Requires Python 3.12 or later. From a checkout:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
firstchair doctor
firstchair run --demo "Review the project's build instructions"
firstchair status <run-id>
```

`doctor` locates Codex, Claude Code and Grok executables on PATH and reports
each provider's readiness without launching it. The bundled synthetic provider
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

Live adapters are disabled pending workspace isolation, process-tree cleanup,
and version-specific contract verification.

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
Codex and Grok Build can run as headless workers. The installed
`firstchair delegate` command runs one bounded task per worker in a Git
worktree outside the checkout. Read tasks use a disposable
worktree. Write tasks keep branch `delegate/NAME` for review. See
[the orchestration guide](docs/orchestration.md). Delegation
uses your existing provider logins and is separate from Firstchair's own
adapters, which stay disabled.

```sh
firstchair delegate run auto --lead codex --dry-run
firstchair delegate run auto --lead codex --name parser-review "Review the parser tests"
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
offline fixture and parser work. Live adapters stay disabled.

Firstchair is independently maintained and released under the [MIT license](LICENSE).

See the [upstream review](docs/upstream-review.md) and
[provider contract inventory](docs/provider-contracts.md) for the adapter plan.
