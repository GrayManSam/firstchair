# Provider contract inventory

The following versions were present during local discovery. Authentication and live event compatibility need independent verification
before enabling adapters. See the smoke attempt below.

| Provider | Observed version | Candidate headless contract |
| --- | --- | --- |
| Codex CLI | 0.170.0 | `codex exec --json` emits JSONL. The CLI exposes a read-only sandbox and ephemeral mode. Use stdin for prompts and inspect its permissions and configuration controls before integration. |
| Claude Code | 2.1.328 | `claude -p` supports JSON, streaming JSON and output schema validation. Validate permission mode and tool availability independently from the output schema. |
| Grok Build | 1.0.77 | `grok --no-auto-update -p TASK --output-format streaming-json` uses newline-delimited events. Verify unattended denial behavior and sandbox scope before enabling it. |

For alpha, test supported event versions, terminal result detection, timeout
and cancellation, authentication failure and unknown usage with fixtures.
Treat provider output as data. Keep executable selection, working directory,
permissions and budget in controller-owned policy.

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Claude Code programmatic usage](https://code.claude.com/docs/en/headless)
- [Grok Build headless scripting](https://docs.x.ai/build/cli/headless-scripting)
- [Grok Build permissions](https://docs.x.ai/build/features/permissions)

## Live smoke attempt

Each CLI ran from an empty temporary directory with the same fixed-text
prompt and requested structured output. No provider returned a result.

| Provider | Result in the restricted execution environment |
| --- | --- |
| Codex | The app server failed to initialize on a read-only filesystem. The error persisted with writable log and SQLite paths. |
| Claude Code | The headless process timed out after 55 seconds without output. |
| Grok Build | The Linux sandbox refused to start because it could not create a required bubblewrap placeholder. |

The local TriadMux CLI suite still passed, including both the in-process demo
and synthetic subprocess workflow. A successful provider response remains
necessary to verify authentication and collect a sanitized event fixture.
