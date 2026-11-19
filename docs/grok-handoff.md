# TriadMux handoff for Grok

Continue the MVP toward `0.1.0a1` from the Git checkpoint that introduced
this file. The package version at this checkpoint is `0.0.0`. Read
`AGENTS.md`, `ROADMAP.md`, `TODO.md`, and
`docs/provider-contracts.md` before editing.

## What is in the checkpoint

- The offline synthetic workflow passes a structured worker review into
  synthesis, then persists the review, result, and usage provenance.
- The CLI previews routing and limits, loads optional TOML configuration,
  and enforces per-stage input and output bounds plus a shared time budget.
- POSIX recovery uses a per-run lock. The bundled synthetic worker exits
  when its controller dies. Use `triadmux runs` to find an abandoned run and
  `triadmux recover <run-id>` to mark it interrupted.
- Codex and Claude result parsers have invented offline fixtures. Live
  routing remains disabled. The release workflow checks a synthetic
  handoff and its persisted status from the installed wheel.

## Verification evidence

All 43 unit tests passed locally on Linux with Python 3.12 and 3.14. The
release smoke ran against a freshly built wheel under Python 3.12 and
validated the wheel and source distribution checksums. Hosted CI and
publication are pending.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m triadmux doctor
git diff --check
```

## First work order

Review the Grok Build 1.0.77 contract gaps in `docs/provider-contracts.md`.
The recorded host evidence confirms JSONL framing. A successful terminal
reply, usage fields, and unattended tool-denial behavior still need
version-specific evidence. Start with documentation and an invented offline
fixture for fields the evidence actually confirms. Keep the adapter
disabled while those gates are open. Any live smoke requires explicit
maintainer opt-in and a credential-isolated environment.

The other open gates are live workspace isolation and process-tree
cleanup, hosted CI across the configured matrix, and the alpha release
rehearsal. Keep transcripts, local state, account information, and credentials
out of work products and Git.
