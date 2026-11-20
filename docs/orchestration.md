# Lead a Firstchair development session

The active agent session plans the task, dispatches independent pieces when
requested, reviews the results, and integrates verified changes. Use the
`--lead` value matching the session that invoked the dispatcher.

| Lead | Automatic read worker | Automatic write worker |
| --- | --- | --- |
| Claude Code | Grok Build, then Codex if Grok is absent | Codex, then Grok Build if Codex is absent |
| Codex | Grok Build | Grok Build |
| Grok Build | Codex | Codex |

Use `firstchair delegate run auto --lead codex --dry-run` to preview worker
selection and timeout without starting a worker or creating a worktree.
`firstchair delegate --repo PATH` selects a checkout from another directory.
The repository's `python3 scripts/delegate.py` entry point remains available.

Automatic selection checks PATH before dispatch. An invocation makes one worker
attempt. The summary records the requested worker, chosen worker, and lead.

```sh
firstchair delegate run auto --lead codex --name parser-review --prompt-file /tmp/review.md
firstchair delegate run auto --lead grok --mode write --name parser-fix --prompt-file /tmp/fix.md
firstchair delegate run codex --lead claude "Review the parser tests"
```

Pick one testable slice from ROADMAP.md and TODO.md. Give each worker a distinct
name, files in scope, and acceptance criteria. Independent tasks can run
concurrently in separate worktrees. Worktrees start from HEAD. Review pending
changes before intentionally carrying them into a worker with `--with-changes`.

Read the JSON returned by the command and inspect each write worktree's diff.
The dispatcher saves job metadata locally and removes temporary prompt and
provider output files when the invocation ends. Run
`PYTHONPATH=src python -m unittest discover -s tests -v` before integrating.
The lead owns Git integration.

Delegation uses the worker CLI's existing login and provider quota. Select an
explicit worker to pass `--model` or `--effort`. Summaries report measured
input and output tokens for successful Codex runs when the versioned parser
recognizes the full event stream. Other usage is reported as unknown.
Automatic account selection, quota-based retries, and model optimization
require provider contracts and policy beyond the dispatcher's PATH check.

## Local verification

The installed dispatcher completed fixed-prompt read jobs through Codex and
Grok Build in temporary Git repositories on the development host. The same
jobs failed to start under the restricted workspace sandbox. Codex hit a
read-only filesystem and Grok Build's sandbox could not initialize. Claude
Code's separate fixed-prompt probe exited with code 1. Claude Code can lead
this workflow by selecting a Codex or Grok Build worker.

## Sign in and choose accounts

On POSIX, use a distinct alias for each account. Run login from a terminal
and complete the provider's native browser flow. Over SSH, add
`--device-auth` for Codex and Grok and open the printed URL on your local
device. For Claude, follow the native sign-in URL and paste the browser code
into the SSH terminal if prompted. Treat sign-in URLs and codes as private.

```sh
firstchair auth login codex work
firstchair auth login codex personal
firstchair auth login claude work
firstchair auth login grok work
firstchair auth list
firstchair auth check codex work
firstchair auth check claude work --probe
firstchair delegate run codex --profile work "Review the parser tests"
```

The account directories live under
`${XDG_STATE_HOME:-$HOME/.local/state}/firstchair/accounts`. Firstchair
requires private, user-owned directories outside Git checkouts and starts
named login and worker processes with a restrictive umask. Providers manage
credential storage. File-backed provider storage depends on the permissions
of the local account and filesystem for confidentiality. Firstchair stores
no credentials or provider account identifiers in its job metadata.

Named sessions set the provider home for that process. Claude login uses
claude.ai, whose per-directory behavior is documented by Anthropic. Keyless
Claude Console profiles use a separate native authentication system. Codex
and Grok named profiles can be selected for delegation. Claude profiles
currently support native login, status, and a fixed-prompt inference probe.

`auth check` without an alias examines the current native login. Grok's
check sends a small fixed prompt because its CLI has no status subcommand.
Claude's `--probe` sends a fixed prompt and reports `rate_limited` for
HTTP 429. A signed-in Claude account can still be rate limited. Retry after
the provider's allowance resets.

[Codex authentication](https://learn.chatgpt.com/docs/auth) ·
[Claude Code authentication](https://code.claude.com/docs/en/authentication) ·
[Grok Build settings](https://docs.x.ai/build/settings) ·
[Grok Build sign-in](https://docs.x.ai/build/overview)
