# Firstchair to-do list

[Roadmap and release gates](ROADMAP.md)

## Foundation · 0.0.0

- [x] Create and verify the independent public repository, initial branch and upstream tracking.
- [x] Verify an installable package, version and help output, isolated tests and configuration defaults.
- [x] Record upstream revision, license and reuse decision. Inventory repository-local instructions, skills and available integrations.
- [ ] Run starter CI on GitHub and confirm release automation can build and verify distribution artifacts.
- [x] Require annotated public tags named `v` plus the package version, with changelog notes, before a GitHub Release.
- [ ] Confirm default-branch protection and release permissions, then mark the baseline release.

- [x] Demonstrate an offline plan, review and synthesis handoff with persisted status.

## MVP · 0.1.0a1

- [ ] Document supported Codex, Claude Code and Grok Build command and event contracts using versioned sources and sanitized fixtures.
- [x] Build one offline vertical slice with a synthetic CLI, config validation, explicit provider selection, bounded execution and durable state.
- [x] Test malformed responses, output limits, stage timeouts, saved-state reads and classified failures.
- [x] Clean up POSIX workers and their process group on stage failure or timeout.
- [x] Verify Ctrl-C during synthetic worker startup reaps the process and records an interrupted run.
- [x] Recover abandoned synthetic run records after a controller crash on POSIX.
- [x] List saved run IDs, stages, and statuses without printing task or result content.
- [x] Verify bundled POSIX synthetic worker exit after controller SIGKILL.
- [x] Run provider subprocesses in a temporary workspace and reap a POSIX grandchild on timeout.
- [x] Keep provider children on an environment allowlist and redact secret values in saved run records.
- [ ] Verify crash cleanup and workspace isolation for live provider process trees.
- [x] Preview selected stages and execution limits without starting workers.
- [ ] Add real provider adapters and complete credential-free CI fixtures before opt-in live smoke tests.
- [x] Exercise offline Codex and Claude Code output parsing with synthetic fixtures.
- [x] Validate Grok Build 1.0.77 streaming-json framing offline. Reply and usage acceptance stay disabled.
- [x] Verify a structured synthetic Leader-to-worker review and synthesis with explicit run selection.
- [x] Enforce a shared time budget across synthetic stages and test budget rejection.
- [x] Enforce per-stage request byte budgets and expose synthetic limits through explicit TOML configuration.
- [x] Report offline usage as unknown and explain provider readiness and routing.
- [x] Let Claude Code, Codex and Grok Build sessions lead the maintainer dispatcher and verify automatic worker selection with synthetic CLIs.
- [x] Record version-validated token usage for Codex delegation summaries and mark unavailable telemetry as unknown.
- [x] Defer optional Claude Swap support for alpha and document acceptance cases for a future bridge.
- [x] Verify installed-package examples locally and add a release-wheel smoke check.
- [x] Install the worktree dispatcher as `firstchair delegate` and verify live Codex and Grok read jobs on the development host.
- [ ] Verify the hosted support matrix and publish the alpha prerelease.

## Beta and release

- [ ] Implement guarded recovery, eligible-provider fallback, bounded concurrency and explicit workspace isolation.
- [ ] Validate a Claude worker permissions contract and verified usage telemetry for Claude and Grok.
- [x] Add native sign-in and private named provider homes, with sanitized login and Claude inference checks.
- [ ] Verify simultaneous signed-in accounts on each supported host and validate opt-in account quota snapshots and per-process profile selection, with freshness, cooldowns and explicit account policy.
- [ ] Route among eligible model and account profiles using task requirements and measured usage, and record the selection rationale.
- [ ] Verify state backup, restart, migration and workspace recovery paths with synthetic data.
- [ ] Rehearse install and upgrade on advertised platforms. Record opt-in provider smoke results.
- [ ] Cut a beta, triage compatibility feedback, and close release-blocking reliability and security defects.
- [ ] Freeze the supported interface, build the release candidate, and validate support, release and rollback instructions.
- [ ] Publish the stable distribution and confirm installation from release assets.

## After the first stable release

- [ ] Create issue epics for task DAGs and review, resource estimation, reporting and packaging.
- [ ] Write a design and contract tests before introducing provider extensions or an MCP control interface.
- [ ] Publish public interface and deprecation commitments for 1.0.
