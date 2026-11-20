# Changelog

## Unreleased

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
