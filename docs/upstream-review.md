# Claude Swap source review

Reviewed the public repository at [ee79e705cf6e1ad3f70621b88b80983a99bb2001](https://github.com/realiti4/claude-swap/commit/ee79e705cf6e1ad3f70621b88b80983a99bb2001).
The package at that revision reports 1.2.0b1, Python 3.12+, and an MIT
license (copyright 2026 Onur Cetinkol). This was a pinned source review
through GitHub. Firstchair (formerly TriadMux) incorporates no upstream
source code and is not Claude Swap.

| Area | Finding | Firstchair decision |
| --- | --- | --- |
| CLI and JSON contracts | Account list and status use versioned JSON documents. Auto mode has a separate JSONL stream. Some commands may fetch usage. | Optional integration starts with a documented, opt-in status reader. Accept additive fields, reject unsupported versions and preserve unknown or stale readings. |
| Credential stores and switching | Switching serializes app, credential and config changes. Rollback and refresh handling protect successor credentials. Storage differs by OS. | Leave login and account selection to the provider or upstream. Keep credentials and transfer/export files out of Firstchair. |
| Usage and retries | An expiring reservation deduplicates checks. Refresh runs after releasing the store lock and failed requests retain last-good data. | Use independent reservations only for controller-owned work and retain freshness metadata with each observation. |
| Session paths | Claude profiles use separate config paths but can share settings and history. One slot uses the default Claude login. | Treat the profile as account selection. Enforce workspace permissions separately. |
| Process lifetime | POSIX can replace the current process, while Windows uses subprocess waiting. Process checks verify identity rather than relying on the PID alone. | Define cancellation and recovery for each supported platform with synthetic processes before enabling live orchestration. |
| State writes | The helper writes private temporary files in the destination directory and replaces the target after flushing. | Persist controller state separately. Use scoped atomic writes now and evaluate SQLite for recovery and concurrent claims. |

Maintain Firstchair independently. A fork would be useful for contributing a
specific Claude Swap change upstream, while a later optional CLI bridge would
keep Claude integration compatible with a standalone multi-provider controller.

- [Pinned architecture](https://github.com/realiti4/claude-swap/blob/ee79e705cf6e1ad3f70621b88b80983a99bb2001/docs/architecture.md)
- [Pinned JSON contract](https://github.com/realiti4/claude-swap/blob/ee79e705cf6e1ad3f70621b88b80983a99bb2001/docs/json-output.md)
- [Pinned source tree](https://github.com/realiti4/claude-swap/tree/ee79e705cf6e1ad3f70621b88b80983a99bb2001)
