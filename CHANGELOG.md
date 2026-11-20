# Changelog

## Unreleased

## 0.1.0a2

Fixes from the post-release review of the live adapters.

- Secret-looking variables, including test-prefixed ones, no longer reach
  live provider processes.
- Each provider executable is resolved once to an absolute path, so the
  version probe and every stage run the same file even with a relative
  `PATH` entry.
- The `--version` probe now has bounded output and process-group cleanup.
- Cleanup after a timeout or Ctrl-C no longer waits indefinitely on a
  descendant that left the process group but still holds stdout.
- A run whose failed stage reported no token counts now shows `partial`
  usage instead of `measured`.
- `--profile` and `--reviewer-profile` are validated before a dry run
  reports readiness.

## 0.1.0a1

- Added read-only live adapters for Codex CLI, Claude Code and Grok Build.
  `firstchair run --provider codex|claude|grok` runs plan, review and
  synthesis with your existing sign-in. `--reviewer` picks a different model
  for the review, `--workspace` lets providers read a directory, and
  `--format text` prints a readable summary. Each run records stage outputs
  and measured token usage where the provider reports it.
- Live providers run without write tools or MCP servers, never receive API key
  variables, and are killed with their process group on timeout or Ctrl-C.
- Accept verified provider versions and a bounded compatible range. Unknown
  versions are rejected before any run starts. `firstchair doctor` reports
  each provider's version and contract status.
- Claude Code rate-limit and authorization failures are reported as
  `rate_limited` and `authorization_failed`.
- Added `firstchair delegate` for dispatching Codex and Grok Build workers
  into Git worktrees, and `firstchair auth` for named provider sign-ins.
- Renamed the project from TriadMux to Firstchair. The distribution, import
  package and command are now `firstchair`, and the default state directory
  is `.firstchair/`. For one release, a `triadmux` command prints a notice
  and runs the same CLI, `.triadmux/` is read when `.firstchair/` is absent,
  and `TRIADMUX_TEST_` variables still reach provider children. Old run
  records stay valid.
- Added structured synthetic reviews, explicit usage provenance, provider
  readiness reporting, and dry-run routing explanations.
- Added synthetic request and workflow budgets with optional TOML configuration.
- Added run summaries, guarded POSIX recovery, and bundled worker cleanup after
  controller exit.
- Added offline Codex and Claude result parser tests and an installed-wheel
  workflow smoke check.
- Added offline Grok Build 1.0.77 streaming-json framing checks. Reply and
  usage acceptance stay disabled.
- Run each provider subprocess in a temporary workspace. A dry-run reports
  that workspace as `temporary`. Relative `PYTHONPATH` entries stay resolvable.
- Give provider children an explicit environment allowlist, and replace
  secret environment values in saved run records with `[redacted]`.
- Require an annotated `v` tag that matches the package version and changelog
  before publishing a GitHub Release.

## 0.0.0

- Added a credential-free leader, reviewer and synthesis demo with persisted run status.
- Added executable discovery for Codex, Claude Code and Grok Build.
- Established the MIT-licensed project, contributor workflow and release pipeline.
