# TriadMux research and audit

Retrieved and read on 2026-11-19. This note records what the tree and the public pages actually show. It does not propose a new name.

## What the repository is today

TriadMux is a local Python CLI at package version `0.0.0`. The checkout on `main` is commit `800e14e` (`Record the public repository and private mirror.`), tracking `origin/main`. `git tag -l` is empty. The public releases page has no releases.

Remotes in this checkout:

- `origin`: `https://github.com/GrayManSam/triadmux.git`
- `private`: `https://github.com/GrayManSam/triadmux-private.git`

`docs/grok-handoff.md` says both remotes carry the same history and that `main` is the public default branch. This audit did not open the private repository.

Distribution metadata in `pyproject.toml`:

- name `triadmux`
- version `0.0.0`
- description `Local-first orchestration for AI coding CLIs`
- `requires-python = ">=3.12"`
- license `MIT`
- script `triadmux = "triadmux.cli:main"`
- setuptools package discovery under `src`

`LICENSE` is MIT, copyright 2026 TriadMux contributors. Runtime dependencies are not declared. `https://pypi.org/pypi/triadmux/json` returned `Not Found` on 2026-11-19.

The working tree is a small src-layout package. Top level: `README.md`, `ROADMAP.md`, `TODO.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md`, `LICENSE`, `pyproject.toml`, `src/triadmux/`, `tests/`, `docs/`, `scripts/live-smoke.py`, `.github/`, and `.grok/`. There is no website, dashboard, or TUI in the tree.

`src/triadmux/` modules: `__init__.py`, `__main__.py`, `cli.py`, `config.py`, `inventory.py`, `workflow.py`, `handoff.py`, `provider.py`, `synthetic.py`, `redaction.py`, `state_listing.py`, `release_tag.py`, `strict_json.py`, `claude_json.py`, `codex_jsonl.py`, `grok_jsonl.py`.

GitHub automation is `.github/workflows/ci.yml` (workflow name `CI`) and `.github/workflows/release.yml` (workflow name `Release`), plus `dependabot.yml` for GitHub Actions, two issue forms, and a pull request template. CI runs on pull requests and pushes to `main`, and the release workflow calls it. The test matrix is Ubuntu 24.04 with Python 3.12, 3.13, and 3.14, plus `macos-latest` with Python 3.12. The release workflow is tag-triggered (`v*`), requires an annotated tag on `main`, checks the tag text and package version, then builds and smoke-tests a wheel. No tag exists, so that workflow has not published a release.

Hosted CI is not green. The public Actions index on 2026-11-19 lists failed CI runs, including the first public push run and the current `main` push:

- First public CI run, commit `b7cb36f`: https://github.com/GrayManSam/triadmux/actions/runs/44635762280 — status Failure. The page annotation is on `Test (macos-latest, Python 3.12)`, exit code 1, and on the aggregate `CI required` job. The recorded result of that run is that Ubuntu 3.12, 3.13, and 3.14 passed, and macOS 3.12 failed in `tests/test_subprocess_env.py::test_provider_child_receives_allowlisted_names_only` because a child environment name was outside the allowlist. Job logs require a signed-in session, so this note does not quote a log line.
- Current `main` push, commit `800e14e`: https://github.com/GrayManSam/triadmux/actions/runs/44635962993 — also Failure, with the same visible macOS annotation.
- Two Dependabot pull-request CI runs the same day are also marked failed. Their logs were not opened.

`TODO.md` still leaves "Run starter CI on GitHub and confirm release automation" and "mark the baseline release" unchecked. That matches the public result.

### Commands that exist

`triadmux` (`argparse` prog `triadmux`) has global `--version` and `--state-dir` (default `.triadmux`). Subcommands:

| Command | Role |
| --- | --- |
| `doctor` | Report PATH discovery for `codex`, `claude`, and `grok`, plus the bundled synthetic provider. It does not start those executables. |
| `run` | Requires exactly one of `--demo` or `--provider synthetic`. Positional task text. Optional `--timeout`, `--max-output-bytes`, `--max-input-bytes`, `--total-timeout`, `--config`, `--dry-run`. |
| `status <run-id>` | Print one saved run record. |
| `runs` | List saved run summaries. |
| `recover <run-id>` | On POSIX, mark an abandoned run interrupted after the controller releases its lock. It updates the record only. |

`run --demo` calls in-process `demo_plan`, `demo_review`, and `demo_synthesize`. `run --provider synthetic` calls `SyntheticProvider` for the same three stage names. `--provider` choices are only `synthetic`. Limit flags and `--config` are rejected unless `--provider` is set.

`--dry-run` prints a plan and returns. It does not call `run_workflow`, so it does not start workers or write a run record. For `--provider synthetic` the plan includes `"workspace": "temporary"`.

Persisted stage names in `workflow.py` are `plan`, then `review`, then `synthesize`. The README describes that handoff as leader, reviewer, and synthesis. A completed synthetic run stores the worker review and a synthesis result. `usage` is stored as `provenance: "unknown"` with null token counts.

Before a record is saved, environment values of length at least 12 are replaced with `[redacted]` when the variable name contains `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, `API_KEY`, or `_KEY`. Provider children receive an allowlist (`PATH`, locale, Python, and loader paths listed in `provider.py`) plus any name that starts with `TRIADMUX_TEST_`. `HOME` and API keys are not on that allowlist.

`inventory.py` sets `enabled` false for `codex`, `claude`, and `grok`. Only `synthetic` is `enabled` true and `readiness` `ready`. Auth for the live names is `unchecked`. `routing_explanation` marks those three `adapter_unavailable`.

`claude_json.py`, `codex_jsonl.py`, and `grok_jsonl.py` are not imported by `cli.py`, `workflow.py`, or `provider.py`. They are offline parsers and a framing check, not the worker result path. `validate_grok_jsonl` accepts version `1.0.77` only, requires a zero exit, and returns event counts and type tags. It does not read reply text or usage.

### Changelog versus version

The package version is still `0.0.0`. `CHANGELOG.md` has two sections.

`0.0.0` records the credential-free demo, executable discovery, the MIT project, the contributor workflow, and the release pipeline.

`Unreleased` records behavior that is already in this tree and not yet cut as a new version or tag: structured synthetic reviews, usage provenance, readiness and dry-run routing, TOML budgets, run summaries, POSIX recovery, worker cleanup, offline Codex and Claude parser tests, the wheel smoke check, Grok 1.0.77 framing checks with reply and usage acceptance still disabled, temporary workspaces, the child environment allowlist, `[redacted]`, and the annotated-tag release rule.

### Provider contracts: what is verified

`docs/provider-contracts.md` is a candidate inventory, not an enabled adapter matrix. Observed versions recorded there are Codex CLI 0.170.0, Claude Code 2.1.328, and Grok Build 1.0.77.

Verified in the controller today: the synthetic provider, temporary `triadmux-workspace-*` directories, the child allowlist, secret redaction, and POSIX process-group timeout against a synthetic process tree. The document says that check does not launch Codex, Claude Code, or Grok.

Offline only: Codex and Claude parsers gate on those pinned versions and invented fixtures. The Grok validator checks type-tagged JSONL and nothing else. The doc says TriadMux does not treat the Grok user-guide fields as a worker result until a sanitized host capture confirms them.

A restricted live-smoke attempt did not get a result from any of the three CLIs. A later host-terminal note says Codex and Claude Code returned the expected structured reply with existing logins, while Grok Build produced parseable JSONL but the smoke marker was not found as a single value. The live adapter stays disabled. `scripts/live-smoke.py` is an opt-in maintainer script, not a `triadmux` subcommand.

The Claude Swap bridge is explicitly deferred. No Claude Swap invocation is part of the workflow.

## Product claims

Status words: shipped means the current tree does it; experimental means code or docs exist but the path is not the supported worker or has not been proven in hosted CI or a release; planned means a roadmap or to-do item; unsupported means absent or contradicted.

| Claim | Status | Evidence path |
| --- | --- | --- |
| Package `triadmux` 0.0.0, MIT, Python >=3.12, console script `triadmux` | shipped | `pyproject.toml`, `LICENSE` |
| CLI: `doctor`, `run`, `status`, `runs`, `recover`, `--version`, `--state-dir` default `.triadmux` | shipped | `src/triadmux/cli.py` |
| `run` accepts only `--demo` or `--provider synthetic` | shipped | `src/triadmux/cli.py` |
| `run` accepts `--timeout`, `--max-output-bytes`, `--max-input-bytes`, `--total-timeout`, `--config`, `--dry-run` | shipped | `src/triadmux/cli.py` |
| Synthetic or demo handoff persists stages `plan`, `review`, `synthesize` | shipped | `src/triadmux/cli.py`, `src/triadmux/workflow.py` |
| Dry-run does not start workers or write a run; synthetic dry-run reports workspace `temporary` | shipped | `src/triadmux/cli.py`, `README.md` |
| Secret environment values of length >= 12 are replaced with `[redacted]` before save | shipped | `src/triadmux/redaction.py` |
| Provider child environment is an allowlist plus the `TRIADMUX_TEST_` prefix | shipped | `src/triadmux/provider.py` |
| Run records store usage provenance `unknown` and null token counts | shipped | `src/triadmux/workflow.py` |
| `doctor` can see Codex, Claude Code, and Grok on PATH, and live adapters stay disabled | shipped | `src/triadmux/inventory.py`, `README.md` |
| Run records default to ignored `.triadmux/` | shipped | `src/triadmux/cli.py`, `.gitignore` |
| POSIX `recover` marks an abandoned locked run interrupted and does not relaunch work | shipped | `README.md`, `src/triadmux/workflow.py` |
| Offline Codex and Claude parsers exist and are not the worker result path | experimental | `src/triadmux/codex_jsonl.py`, `src/triadmux/claude_json.py` |
| Grok 1.0.77 JSONL framing check accepts type tags only and does not accept a reply | experimental | `src/triadmux/grok_jsonl.py`, `CHANGELOG.md` |
| CI workflow is configured for Ubuntu 3.12–3.14 and macOS 3.12 | experimental | `.github/workflows/ci.yml` |
| Annotated `v*` tag workflow can build a wheel and smoke a synthetic run | experimental | `.github/workflows/release.yml` |
| Opt-in live-smoke script can probe provider CLIs outside the CLI | experimental | `scripts/live-smoke.py`, `docs/provider-contracts.md` |
| Versioned Codex, Claude Code, and Grok command contracts are supported adapters | experimental | `docs/provider-contracts.md` |
| Live Codex, Claude Code, and Grok workers, with workspace isolation still to verify | planned | `README.md`, `TODO.md` |
| Optional Claude Swap status reader, not account switching | planned | `docs/provider-contracts.md`, `docs/upstream-review.md`, `TODO.md` |
| Beta recovery beyond the current POSIX path, bounded parallel read-only work, worktree isolation, fallback | planned | `ROADMAP.md` |
| Task DAGs, cost and quota forecasts, task views, provider plugin API, optional MCP control | planned | `ROADMAP.md`, `TODO.md` |
| Alpha, beta, release candidate, 0.1.0, and 1.0.0 gates | planned | `ROADMAP.md` |
| A published GitHub Release | planned | `CONTRIBUTING.md`, `.github/workflows/release.yml` |
| Live multi-CLI orchestration as something a user can run today | unsupported | `src/triadmux/inventory.py`, `src/triadmux/cli.py` |
| Quota or cost management | unsupported | `src/triadmux/cli.py`, `ROADMAP.md` |
| TUI, project website, or dashboard | unsupported | repository tree; no such command in `src/triadmux/cli.py` |
| Auth handling or account switching | unsupported | `src/triadmux/inventory.py`, `docs/upstream-review.md` |
| Rate-limit bypass | unsupported | `docs/provider-contracts.md` |
| Hosted CI is green | unsupported | https://github.com/GrayManSam/triadmux/actions/runs/44635762280 |
| A TriadMux distribution on PyPI | unsupported | https://pypi.org/pypi/triadmux/json |

Claim counts: 31 rows, 12 shipped, 6 experimental, 6 planned, 7 unsupported.

The pyproject description and the first README sentence say the tool coordinates or orchestrates coding CLIs. The following README sentence limits version 0.0.0 to a deterministic synthetic handoff. The broader sentence is easy to over-read. The shipped orchestration is the synthetic or demo stage chain only.

## Differentiation from claude-swap

TriadMux's recorded upstream review is commit `ee79e705cf6e1ad3f70621b88b80983a99bb2001` in `realiti4/claude-swap`. At that commit, `pyproject.toml` reports name `claude-swap`, version `1.2.0b1`, Python `>=3.12`, MIT, author Onur Cetinkol, and scripts `claude-swap` and `cswap`. The pinned `LICENSE` copyright line is `Copyright (c) 2026 Onur Cetinkol`. `docs/upstream-review.md` says TriadMux incorporates no upstream source. It is not a fork, not Claude Swap, and not affiliated with that maintainer or with Anthropic, OpenAI, or xAI.

On 2026-11-19 the public `main` README describes a multi-account switcher for Claude Code and the VS Code extension: add and switch accounts, show 5-hour and 7-day usage, auto-switch before a rate limit, run one account in the current terminal, a Textual dashboard, JSON for `list` and `status`, and an optional macOS menu bar. The raw `main` `pyproject.toml` fetched the same day still says version `1.2.0b1`. This audit did not diff `main` against the pinned commit, so current README behavior is cited from the page retrieved today, not from the pinned tree.

What differs, from those pages and this tree:

- Claude Swap stores and swaps Claude Code logins. TriadMux leaves login and account selection to the provider or to upstream and keeps credentials out of its state.
- Claude Swap's current README is about one vendor's accounts and quotas. TriadMux's controller is meant to sit in front of more than one coding CLI, but the only runnable provider is the bundled synthetic one.
- Claude Swap can change which Claude account is active, including before a limit. TriadMux has no rate-limit bypass and has deferred even an opt-in `cswap status --json` reader.
- Claude Swap ships a TUI and an optional menu bar. TriadMux's interface is a JSON CLI.
- A later TriadMux bridge, if built, is described as a status reader with version rejection. Account switching stays outside that reader.

## Adjacent tools

Opened on 2026-11-19. These are orchestration or multi-session coding-CLI tools, not feature parity claims. Star counts and install ranks are omitted.

**CLI Agent Orchestrator** (`awslabs/cli-agent-orchestrator`). The README says a local `cao-server` starts provider CLIs in isolated terminal sessions so a supervisor can delegate work. Prerequisites listed there include Python 3.11 or later, tmux 3.3 or later, and uv. The provider list on that page includes Kiro, Claude Code, Codex, and Grok Build, among others. It documents a web UI, MCP, and tmux attach. License text on the page is Apache-2.0. Install paths shown are a uv tool from GitHub and a PyPI package named `cli-agent-orchestrator`. TriadMux does not depend on tmux, does not run a server, and does not launch those CLIs.

**Claude Squad** (`smtg-ai/claude-squad`). The README describes a terminal app, binary names `claude-squad` and `cs`, that manages Claude Code, Codex, Gemini, Aider, and other local agents in separate workspaces. It says the mechanism is tmux sessions plus git worktrees, and that each task can be reviewed before changes are applied. License on the page is AGPL-3.0. Prerequisites named there are tmux and `gh`. TriadMux has no TUI and no git-worktree isolation. Worktree isolation for approved writes is a beta roadmap item, not current behavior.

**Parallel Code** (`johannesjo/parallel-code`). The README describes a desktop app that starts Claude Code, Codex, OpenCode, Copilot, Antigravity, or another terminal agent in its own git worktree, then reviews the diff. The page says MIT, local execution, macOS and Linux release downloads, and an Electron, SolidJS, and TypeScript stack. Optional items listed there include a phone UI, Docker sandboxes, and a Kanban file. TriadMux has no GUI, no merge flow, and no phone or container runtime.

None of these pages was used as a source for TriadMux behavior.

## Audience

Facts from this repo: the README targets a local checkout on Python 3.12 or later and tells the reader to install the package, run `doctor`, and run the synthetic demo. Records stay on the machine. The roadmap's first useful workflow is a user-approved task, a bounded provider invocation, and an inspectable outcome. Later gates add real-provider smoke checks run by maintainers outside ordinary CI. Authentication stays with the provider CLIs.

Positioning judgment, not a measured audience: the people who can use 0.0.0 today are maintainers and contributors checking the controller, the state files, and the limits. Someone who needs several live coding agents in parallel already has tools that start those CLIs. Someone who needs to rotate Claude Code accounts is in Claude Swap's problem, which this project has chosen not to solve. The roadmap's later user is an operator who already runs Codex, Claude Code, or Grok locally and wants an explicit, recorded handoff with budgets and redaction. That user is not served by the live path yet.

## Rename touchpoint inventory

Current strings only. No replacement is proposed. A search of the tree for `triadmux`, `TriadMux`, and `triad-mux` found no tracked `triad-mux` string. The local checkout directory is `triad-mux` (hyphen). The GitHub slug is `triadmux` (no hyphen).

### Repo slug

- Public remote URL contains `GrayManSam/triadmux`.
- Private remote URL contains `GrayManSam/triadmux-private`.
- `docs/grok-handoff.md` quotes both `https://github.com/GrayManSam/triadmux` and `https://github.com/GrayManSam/triadmux-private`.

### Distribution name

- `pyproject.toml`: `name = "triadmux"`.
- `src/triadmux/__init__.py`: `version("triadmux")`.

### Import package

- Directory `src/triadmux/`.
- Tests import `triadmux` (`from triadmux.cli import main` and the other `triadmux.*` imports under `tests/`).
- Module invocation string `python -m triadmux` in docs, tests, and workflows.
- Release helper prog in `src/triadmux/release_tag.py`: `python -m triadmux.release_tag`.
- Synthetic worker argv in `src/triadmux/provider.py`: `"-m", "triadmux.synthetic"`.

### CLI binary

- `pyproject.toml`: `triadmux = "triadmux.cli:main"`.
- `src/triadmux/cli.py`: `prog="triadmux"`.
- `.github/workflows/release.yml`: `cli = install / "bin" / "triadmux"`.
- Docs and `CONTRIBUTING.md` invoke the command as `triadmux`.

### State directory

- `src/triadmux/cli.py`: `default=Path(".triadmux")`.
- `.gitignore`: `.triadmux/`.
- `.grok/config.toml` deny rules: `Read(.triadmux/**)` and `Edit(.triadmux/**)`.
- `scripts/live-smoke.py` default report: `Path(".triadmux/live-smoke.json")`.

### Environment prefix

- `src/triadmux/provider.py`: `_SUBPROCESS_ENV_PREFIX = "TRIADMUX_TEST_"`.
- `docs/provider-contracts.md`: `` `TRIADMUX_TEST_*` ``.
- Tests set `TRIADMUX_TEST_MARKER` and `TRIADMUX_TEST_WORKER_LOCK`.
- Related but not the allowlist prefix: `scripts/live-smoke.py` sets `MARKER = "TRIADMUX_SMOKE_OK"`.

### GitHub workflows

Workflow file names `ci.yml` and `release.yml` do not contain the product name. Strings inside `release.yml` do:

- `prefix="triadmux-wheel-"`
- `python -m triadmux.release_tag`
- `bin/triadmux`
- tag-body check `TriadMux ${GITHUB_REF_NAME#v}`
- release title `--title "TriadMux ${GITHUB_REF_NAME#v}"`

`ci.yml` runs `triadmux --version` and `triadmux --help` after `pip install .`. `dependabot.yml` has no product string.

### Docs and policy files

| Path | Current string |
| --- | --- |
| `README.md` | heading `# TriadMux`; commands `triadmux`; directory `.triadmux/` |
| `ROADMAP.md` | heading `# TriadMux roadmap` |
| `TODO.md` | heading `# TriadMux to-do list` |
| `CHANGELOG.md` | no product name in the headings; behavior text does not repeat the slug |
| `CONTRIBUTING.md` | `# Contributing to TriadMux`; tag message `TriadMux 0.1.0a1`; release title `TriadMux <version>` |
| `SECURITY.md` | `the TriadMux GitHub repository` |
| `AGENTS.md` | heading `# TriadMux` |
| `LICENSE` | `Copyright (c) 2026 TriadMux contributors` |
| `docs/upstream-review.md` | `TriadMux incorporates no upstream source code.` |
| `docs/provider-contracts.md` | `triadmux-workspace-*`, `.triadmux/live-smoke.json` |
| `docs/grok-handoff.md` | heading `# TriadMux handoff for Grok` |
| `.github/ISSUE_TEMPLATE/bug.yml` | `Report a TriadMux problem` |
| `.github/ISSUE_TEMPLATE/feature.yml` | `Propose a TriadMux capability` |
| `.github/pull_request_template.md` | no product string |

### Tests

Every file under `tests/` imports `triadmux`. Names that also embed the string:

- `tests/test_workspace.py` expects directory prefix `triadmux-workspace-`.
- `tests/test_subprocess_env.py` uses `TRIADMUX_TEST_`.
- `tests/test_release_tag.py` asserts `python -m triadmux.release_tag` in the workflow.

`src/triadmux/provider.py` creates `TemporaryDirectory(prefix="triadmux-workspace-")`. `scripts/live-smoke.py` uses `prefix="triadmux-live-"`.

### Grok project files

- `.grok/plugins/triadmux/plugin.json`: `"name": "triadmux"`.
- `.grok/config.toml`: `enabled = ["triadmux"]`.
- Paths `.grok/agents/triadmux.md` and `.grok/plugins/triadmux/`.
- `README.md` calls out the `triadmux` plugin.

### Badges

No badge markup, shields.io URL, or the word `badge` appears in the tree. There is no badge string to rename. The README does not show a CI or PyPI badge.

## Risks

**tmux confusion.** The slug `triadmux` reads like a multiplexer. CLI Agent Orchestrator and Claude Squad, opened above, actually require tmux and say so. TriadMux does not import or shell out to tmux. A reader can still assume session panes, attach, and detach. The CLI has none of those commands.

**Vendor-name confusion.** `doctor` reports executables named `codex`, `claude`, and `grok`. Docs cite Claude Code, Codex CLI, and Grok Build versions and upstream manuals. The project is not those products and is not affiliated with Anthropic, OpenAI, xAI, or the Claude Swap maintainer. The name does not include a vendor, which avoids one kind of confusion and does nothing to stop another: people will still describe it as a Claude or Grok product if the independent-maintenance line is dropped.

**Claiming unshipped features.** The dangerous claims are live multi-CLI orchestration, quotas, cost management, a TUI, a website, a dashboard, task DAGs, auth handling, and rate-limit bypass. None of those run. The README and to-do list already say live adapters are disabled and the Claude Swap bridge is deferred. The pyproject one-line description does not say that. Host-terminal smoke notes in `docs/provider-contracts.md` must not be retold as enabled adapters. Offline parsers must not be retold as the worker path. The Grok validator must not be retold as reply acceptance.

**macOS CI failure.** The first public CI run on 2026-11-19 passed the three Ubuntu Python versions and failed macOS 3.12 in `tests/test_subprocess_env.py::test_provider_child_receives_allowlisted_names_only` because a child environment name was outside the allowlist. The current `main` Actions run is also Failure, with the macOS job annotated. The README is accurate that CI is configured. It would be inaccurate to say the matrix passes.

**No tag yet.** Version `0.0.0` is the only package version. There is no `v0.0.0` tag and no GitHub Release. The release workflow, checksums, and wheel smoke have not run on a tag. `CHANGELOG.md`'s `Unreleased` section is work in the tree, not a publication. `TODO.md` still has the foundation CI confirmation and baseline release open. Roadmap tags from `v0.1.0a1` onward are names for future gates, not builds that exist.

## Sources

All retrieved 2026-11-19 unless the row is an in-repo file read the same day.

- This repository, read locally: `README.md`, `ROADMAP.md`, `TODO.md`, `CHANGELOG.md`, `pyproject.toml`, `LICENSE`, `src/triadmux/cli.py`, `src/triadmux/inventory.py`, `src/triadmux/workflow.py`, `src/triadmux/provider.py`, `src/triadmux/redaction.py`, `src/triadmux/grok_jsonl.py`, `docs/upstream-review.md`, `docs/provider-contracts.md`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`.
- Public repository: https://github.com/GrayManSam/triadmux
- Actions index and the two `main` CI runs: https://github.com/GrayManSam/triadmux/actions , https://github.com/GrayManSam/triadmux/actions/runs/44635762280 , https://github.com/GrayManSam/triadmux/actions/runs/44635962993
- Releases page (none): https://github.com/GrayManSam/triadmux/tags
- PyPI JSON (Not Found): https://pypi.org/pypi/triadmux/json
- Claude Swap repository README: https://github.com/realiti4/claude-swap
- Claude Swap pin used by TriadMux: https://github.com/realiti4/claude-swap/commit/ee79e705cf6e1ad3f70621b88b80983a99bb2001
- Pinned package metadata: https://raw.githubusercontent.com/realiti4/claude-swap/ee79e705cf6e1ad3f70621b88b80983a99bb2001/pyproject.toml
- Pinned license: https://raw.githubusercontent.com/realiti4/claude-swap/ee79e705cf6e1ad3f70621b88b80983a99bb2001/LICENSE
- Current `main` package metadata, still `1.2.0b1` when fetched: https://raw.githubusercontent.com/realiti4/claude-swap/main/pyproject.toml
- CLI Agent Orchestrator README: https://github.com/awslabs/cli-agent-orchestrator
- Claude Squad README: https://github.com/smtg-ai/claude-squad
- Parallel Code README: https://github.com/johannesjo/parallel-code
