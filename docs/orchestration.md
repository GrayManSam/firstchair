# Lead a Firstchair development session

The active agent session plans the task, dispatches independent pieces when
requested, reviews the results, and integrates verified changes. Use the
`--lead` value matching the session that invoked the dispatcher.

| Lead | Automatic read worker | Automatic write worker |
| --- | --- | --- |
| Claude Code | Grok Build, then Codex | Codex, then Grok Build |
| Codex | Grok Build, then Claude Code | Grok Build, then Claude Code |
| Grok Build | Codex, then Claude Code | Codex, then Claude Code |

`auto` does not select the lead. `self` is the explicit request for the
lead's own provider.

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

## Conductor score

The primary seat runs the score. Pass `--lead` as that seat. Each part names
a seat: `self` starts the lead's own provider as a separate worker, `auto`
uses the table above, and `codex`, `claude`, or `grok` starts that CLI.
A Grok worker still receives `--no-subagents`. The conductor is what fans
the work out. The worker does not fan out again.

Parts run one at a time by default. The next part does not start after a
failure. Write parts keep branch `delegate/NAME`. Read parts remove their
worktrees. The board at `.firstchair/conduct/SCORE/board.json` stores the
limit and each part's status, seat, provider, and exit code. It does not
store the task or the reply. The reply is in the JSON printed when the
score returns.

`--limit N` runs up to N parts at once, where N is 1 through 4. A score can
set the same value as a top-level `"limit"`. The flag overrides the score.
Any other value is refused before a worker starts or a board is written.
Parts run in waves of N in input order, and a wave ends when all of its
parts end. After a wave with a failed part, no later wave starts. Parts
already running in that wave finish. Parts that never started are
`not_started`. The printed summary and the board keep input order, and the
exit code comes from the earliest failed part in that order. Only give
parts that do not depend on each other a limit above 1.

A part can read the reply of one earlier part. Set `"after"` to that part's
name. The conductor adds the earlier reply to the follow-up prompt, marks it
as untrusted output from another worker, and cuts it at 32,000 characters.
The reply stays in the conductor's memory. The board stores the `after`
name and not the reply. The earlier part must finish before the follow-up
starts, so with a limit above 1 the two must fall in different waves. A
score that breaks this is refused before a worker starts. A follow-up fails
without starting a worker when the earlier part returned an empty reply.

```json
{
  "parts": [
    {"name": "own-notes", "seat": "self", "mode": "read", "task": "Summarize the backlog"},
    {"name": "parser", "seat": "codex", "mode": "write", "task": "Add the regression test"},
    {"name": "contract", "seat": "claude", "mode": "read", "task": "Check the worker flags"},
    {"name": "second-look", "seat": "grok", "mode": "read", "after": "contract",
     "task": "Check the findings in the earlier reply against the source"}
  ]
}
```

```sh
firstchair conduct plan --lead grok --score score.json
firstchair conduct run --lead grok --name rehearsal --score score.json
firstchair conduct run --lead grok --name together --score score.json --limit 3
firstchair conduct status rehearsal
firstchair conduct cancel rehearsal
firstchair conduct resume --name rehearsal --score score.json
```

### Cancel a running score

Run `firstchair conduct cancel NAME` from another terminal. The conductor
checks for the request about ten times a second. It kills the process group
of each running part and starts no other part. A cancelled read part's
worktree is removed. A cancelled write part keeps its worktree and branch
for review. The board status becomes `cancelled`, the running parts are
`cancelled`, later parts are `not_started`, and the conductor exits 2. A
part that completed before the request stays `completed`.

Cancel is refused when the board is not `running`. It is also refused when
the board says `running` and no conductor holds the score lock. That score's
conductor died, and `resume` is the next step.

### Resume a score

`firstchair conduct resume --name NAME --score FILE` continues a score that
is not completed and has no live conductor. The conductor holds a lock on
`.firstchair/conduct/NAME/lock` while it runs. The operating system releases
the lock when the process ends, including when it is killed. Resume takes
that lock first and is refused while another conductor holds it. Resume
requires POSIX file locks.

The board has no task text, so pass the score file again. Its parts must
match the saved names, seats, modes, and `after` names in order. The lead
comes from the board. Task text is not compared.

- A completed part is not run again.
- A read part that did not complete runs again. Its leftover worktree and
  log directory are removed first.
- A write part that did not complete and left a worktree or branch is
  refused, and nothing is changed. Review the worktree. Then run
  `firstchair delegate finish NAME --delete-branch`, with `--force` to
  discard its edits, and resume again.
- A follow-up part cannot resume after its earlier part completed in a
  previous run, because that reply was not saved. Start a new score for the
  remaining parts.

A worker process whose conductor was killed can keep running in its own
process group until its provider exits. Check for it before resuming a
score whose conductor was killed.

A score holds at most eight parts. Claude workers run with `--restricted`.
Read parts get Read, Grep, and Glob. Write parts also get Edit and Write,
under `acceptEdits`. Command tools are not named. `firstchair run` stays the
read-only product path and does not use this desk.

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
input and output tokens for a successful Codex run, and for a Claude worker
reply the versioned parser accepts. Other usage is reported as unknown.
Automatic account selection, quota-based retries, and model optimization
require provider contracts and policy beyond the dispatcher's PATH check.

## Local verification

The installed dispatcher completed fixed-prompt read jobs through Codex and
Grok Build in temporary Git repositories on the development host. The same
jobs failed to start under the restricted workspace sandbox. Codex hit a
read-only filesystem and Grok Build's sandbox could not initialize. Claude
Code's separate fixed-prompt probe exited with code 1. Claude Code can lead
this workflow by selecting a Codex or Grok Build worker. That smoke did not
start a Claude worker. Conductor coverage for a Claude worker is synthetic.

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
