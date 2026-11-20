# Provider contract inventory

The following versions were present during local discovery. The workflow
currently accepts the bundled synthetic provider. The live-provider commands
below are candidates for future adapters.

| Provider | Observed version | Candidate headless contract |
| --- | --- | --- |
| Codex CLI | 0.170.0 | `codex exec --json` emits JSONL. The CLI exposes a read-only sandbox and ephemeral mode. Use stdin for prompts and inspect its permissions and configuration controls before integration. |
| Claude Code | 2.1.328 | `claude -p` supports JSON, streaming JSON and output schema validation. Validate permission mode and tool availability independently from the output schema. |
| Grok Build | 1.0.77 | `grok --no-auto-update -p TASK --output-format streaming-json` uses newline-delimited events. Verify unattended denial behavior and sandbox scope before enabling it. |

For alpha, test supported event versions, terminal result detection, timeout
and cancellation, authentication failure and unknown usage with fixtures.
Treat provider output as data. Keep executable selection, working directory,
permissions and budget in controller-owned policy. Each current subprocess
invocation uses a fresh `firstchair-workspace-*` directory and does not inherit
the controller cwd. The child environment is an allowlist: interpreter and
loader paths, locale, and `FIRSTCHAIR_TEST_*`. API keys and `HOME` are not
passed. Saved run records replace values of environment names containing
`SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, `API_KEY`, or `_KEY` when the
value is at least 12 characters. The replacement text is `[redacted]`.
POSIX timeout kills that process group. This check uses
a synthetic process tree. It does not launch Codex, Claude Code, or Grok.

## Result parsing

The parsers return a common `Reply(text, usage)`. The version gate distinguishes
verified versions from compatible releases. It rejects other versions and
prerelease strings with `unsupported_provider_version`.

| Provider | Verified versions | Accepted range |
| --- | --- | --- |
| Codex CLI | 0.170.0, 0.171.0 | 0.170.0 inclusive to 0.180.0 exclusive |
| Claude Code | 2.1.328, 2.1.329 | 2.1.328 inclusive to 2.2.0 exclusive |
| Grok Build | 1.0.77 | 1.0.77 inclusive to 1.1.0 exclusive |

Measured usage requires both input and output counts and at least one nonzero
count. Missing, incomplete, or all-zero usage is recorded as unknown. Reported
counts used by the parser must be integers from zero through 2⁶³ − 1.
Malformed usage fails closed. Token counts alone do not establish a billable amount.

### Codex CLI 0.170.0

The candidate command is `codex --ask-for-approval never exec --ephemeral
--sandbox read-only --skip-git-repo-check --json -`. The final hyphen
selects stdin for the prompt. The pinned source defines response text in
`item.completed` events containing an `agent_message` item, turn usage in
`turn.completed`, and failure in `turn.failed` or a top-level `error`
event. The parser requires a complete successful turn and a successful
process exit, then returns the last completed agent message with turn usage. The smoke checker
only looks for its marker in a completed agent message. Verify inherited
configuration and tool availability before launching unattended work.
[0.170.0 CLI arguments](https://github.com/openai/codex/blob/rust-v0.170.0/codex-rs/exec/src/cli.rs) ·
[0.170.0 event definitions](https://github.com/openai/codex/blob/rust-v0.170.0/codex-rs/exec/src/exec_events.rs)

Example success stream with invented identifiers, reply and counts.

```jsonl
{"type":"thread.started","thread_id":"00000000-0000-4000-8000-000000000001"}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"Synthetic reply"}}
{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":3,"reasoning_output_tokens":0}}
```

### Claude Code 2.1.328

The host smoke command uses `claude -p TASK --tools "" --setting-sources ""
--no-session-persistence --output-format json`. JSON mode yields a single
result object. A future adapter should require a successful process exit,
a successful result envelope and the expected payload. If it opts into
`--json-schema`, it must validate `structured_output` from that envelope.
An empty tool list disables built-in tools. Verify remaining configuration
and tool sources independently before enabling unattended runs. [2.1.328
release](https://github.com/anthropics/claude-code/releases/tag/v2.1.328) ·
[Headless output](https://code.claude.com/docs/en/headless#get-structured-output) ·
[CLI flags](https://code.claude.com/docs/en/cli-reference)

The parser requires one UTF-8 result object with an explicit success subtype,
`is_error: false`, and a nonblank `result` string. It reads input and output
token counts from the result's `usage` object. When `is_error` is true, API status
429 maps to `rate_limited` and 401 or 403 maps to `authorization_failed`, even on a
failed process exit. Other failed exits map to `provider_exit`. An invented
success fixture follows.

```json
{"type":"result","subtype":"success","is_error":false,"result":"Synthetic reply"}
```

### Grok Build 1.0.77

The host evidence establishes newline-delimited JSON framing for
`grok --no-auto-update -p TASK --output-format streaming-json`.
Each line in a reply stream must be a JSON object with a nonblank string
`type`. The parser ignores unfamiliar event types and joins the string `data`
from each `text` event in order. It requires one final `end` with
`stopReason: "end_turn"` and a nonblank reply. An `error` event or a different
stop reason fails the turn. Usage comes from the final event, falling back to
the last `usage` event when the final event omits the field. The framing-only
validator still reports event counts and types for version 1.0.77.
[Headless output modes](https://docs.x.ai/build/cli/headless-scripting) ·
[Permissions](https://docs.x.ai/build/features/permissions)

Invented success stream.

```jsonl
{"type":"probe","id":"fixture-0001","unused":true}
{"type":"text","data":"Invented "}
{"type":"text","data":"reply"}
{"type":"end","stopReason":"end_turn","usage":{"input_tokens":10,"output_tokens":3}}
```

## Claude Swap alpha decision

Defer the optional Claude Swap bridge. The alpha workflow runs offline and
has no live Claude Code adapter. Adding account status now would introduce
provider state and potential usage refreshes without improving the
synthetic workflow. The earlier [pinned source review](upstream-review.md)
covers version 1.2.0b1. No Claude Swap invocation or synthetic installation
was needed for the decision to defer.

If a later release needs quota visibility, evaluate an explicit opt-in
reader for `cswap status --json`. Upstream documents a single JSON object
with `schemaVersion: 1` and distinguishes current usage from cached,
unavailable and last-known readings. Test a synthetic executable for
valid, stale, missing and unsupported responses before enabling a reader.
Keep any account identifiers out of persisted workflow records. Account
switching and credential handling remain outside the proposed reader.
[Claude Swap JSON output reference](https://github.com/realiti4/claude-swap/blob/main/docs/json-output.md)

## Live smoke attempt

Each CLI ran from an empty temporary directory with the same fixed-text
prompt and requested structured output. No provider returned a result.

| Provider | Result in the restricted execution environment |
| --- | --- |
| Codex | The app server failed to initialize on a read-only filesystem. The error persisted with writable log and SQLite paths. |
| Claude Code | The headless process timed out after 55 seconds without output. |
| Grok Build | The Linux sandbox refused to start because it could not create a required bubblewrap placeholder. |

The local Firstchair CLI suite still passed, including both the in-process demo
and synthetic subprocess workflow. A successful provider response remains
necessary to verify authentication and collect a sanitized event fixture.

Run the same fixed-prompt checks from a normal terminal with the existing
provider logins:

```sh
python3 scripts/live-smoke.py
```

The checks run in temporary working directories and print only their
outcomes. It saves those same outcomes to `.firstchair/live-smoke.json` and
exits with status 1 if any check fails. Use `--report PATH` to save elsewhere.

## Host-terminal results

Codex and Claude Code both returned the expected structured reply using
the existing host logins. Grok Build exited successfully and produced
parseable JSONL, but the smoke test did not find the marker as a single
value. This leaves the Grok model reply unverified. The smoke runner now
uses [Grok's plain output mode](https://docs.x.ai/build/cli/headless-scripting)
to check the final text separately from its streaming contract.

```sh
python3 scripts/live-smoke.py --provider "Grok Build" --report .firstchair/grok-smoke.json
```
