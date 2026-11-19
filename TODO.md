# TriadMux to-do list

[Roadmap and release gates](ROADMAP.md)

## Foundation · 0.0.0

- [ ] Create and verify the independent public repository, initial branch and upstream tracking.
- [x] Verify an installable package, version and help output, isolated tests and configuration defaults.
- [x] Record upstream revision, license and reuse decision. Inventory repository-local instructions, skills and available integrations.
- [ ] Run starter CI on GitHub and confirm release automation can build and verify distribution artifacts.
- [ ] Confirm default-branch protection and release permissions, then mark the baseline release.

- [x] Demonstrate an offline plan, review and synthesis handoff with persisted status.

## MVP · 0.1.0a1

- [ ] Document supported Codex, Claude Code and Grok Build command and event contracts using versioned sources and sanitized fixtures.
- [x] Build one offline vertical slice with a synthetic CLI, config validation, explicit provider selection, bounded execution and durable state.
- [x] Test malformed responses, output limits, stage timeouts, saved-state reads and classified failures.
- [x] Clean up POSIX workers and their process group on stage failure or timeout.
- [ ] Verify cancellation and crash recovery before enabling live subprocesses.
- [ ] Add real provider adapters and complete credential-free CI fixtures before opt-in live smoke tests.
- [ ] Implement scoped, user-approved Leader-to-worker delegation and structured synthesis. Verify the complete path with synthetic workers.
- [ ] Add enforceable task and execution budgets, usage provenance and routing explanations. Test unknown usage and budget rejection.
- [ ] Decide whether to include optional claude-swap support and verify its behavior with a synthetic installation.
- [ ] Verify installed-package examples, update the support matrix and publish the alpha prerelease.

## Beta and release

- [ ] Implement guarded recovery, eligible-provider fallback, bounded concurrency and explicit workspace isolation.
- [ ] Verify state backup, restart, migration and workspace recovery paths with synthetic data.
- [ ] Rehearse install and upgrade on advertised platforms. Record opt-in provider smoke results.
- [ ] Cut a beta, triage compatibility feedback, and close release-blocking reliability and security defects.
- [ ] Freeze the supported interface, build the release candidate, and validate support, release and rollback instructions.
- [ ] Publish the stable distribution and confirm installation from release assets.

## After the first stable release

- [ ] Create issue epics for task DAGs and review, resource estimation, reporting and packaging.
- [ ] Write a design and contract tests before introducing provider extensions or an MCP control interface.
- [ ] Publish public interface and deprecation commitments for 1.0.
