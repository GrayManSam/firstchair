# Positioning and messaging

Provisional name: Benchdog. The shipped name is TriadMux. Use TriadMux
in any sentence that describes the binary a person can install today.
Use Benchdog only with the word provisional, until the name is approved.

## Job to be done

A developer who already uses more than one coding CLI wants one local
place to see what is installed, run a bounded handoff, and read what
happened, without handing credentials to a new service.

Version 0.0.0 does the middle of that job with a synthetic provider.
It does the "what is installed" part without launching the tools. It
does not yet run Codex, Claude Code, or Grok.

## Audiences

Primary, as a positioning judgment rather than a surveyed segment:
people who already run Codex, Claude Code, or Grok, and maintainers who
care how a local tool stores a run.

Secondary: a developer who wants the entry point explained without
multiplexer vocabulary.

Not the audience for this version: someone shopping for an autonomous
cloud agent, a quota manager, or a hosted multiplayer IDE.

## Message

One sentence: TriadMux 0.0.0 is a local CLI that discovers coding tools
without launching them and runs a synthetic plan, review, and synthesis
with limits and a record on disk.

Proof, each tied to the tree:

- `triadmux doctor` reports PATH discovery and does not start the executables (`src/triadmux/cli.py`, README).
- `triadmux run --provider synthetic` is the only provider choice.
- `--dry-run` does not write a record.
- Usage is stored as unknown.
- Secret-like environment values of at least 12 characters are redacted before save.
- Live adapters are disabled in `src/triadmux/inventory.py`.

## Do not say

- That the three CLIs are orchestrated live.
- That usage, cost, or quota is measured.
- That the tool bypasses rate limits or shares accounts.
- That it is Claude Swap, or a product of Anthropic, OpenAI, or xAI.
- That hosted CI is green. On 2026-11-19 the macOS job failed.
- That Benchdog is the installed command.

## Ladder

| Layer | Line |
| --- | --- |
| Name, provisional | Benchdog |
| Tagline | Hold the work. You still make the cut. |
| Category | Local CLI for a bounded coding handoff |
| Difference | Records stay on the machine. Live tools stay off until a contract is verified. |
| Reason to try today | `triadmux run --demo` finishes without an API key. |
