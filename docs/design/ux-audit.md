# UX audit — TriadMux 0.0.0

This audit describes the shipped command-line product. Version 0.0.0 has one surface: the `triadmux` CLI. It does not have a leader picker, a worker assignment screen, a task tree, a quota or cost dashboard, a text UI, a local web app, or an auth prompt. Those are not missing pages in a product the user can already open. They are not built. Sections that talk about them are marked PROPOSED.

Live adapters for Codex, Claude Code, and Grok are disabled. `doctor` may find those programs on `PATH`. It does not launch them, and `run` cannot select them. The only enabled route is the bundled synthetic provider. `--demo` is a second offline mode that stays inside the controller process.

Output is indented JSON on standard output. Handled failures are one JSON object on standard error, `{"error": "..."}`, and exit code 1. Argparse mistakes are plain text on standard error and exit code 2. Nothing uses color. Status is always a word.

## What a first-time user can do today

Install is not a `triadmux` command. From a checkout the person needs Python 3.12 or newer, a virtual environment, and `python -m pip install -e .`. Then the commands below work. `triadmux --version` prints the package version. An uninstalled tree reports `0.0.0`.

Global flag, and it has no help sentence today:

```text
triadmux --state-dir PATH <command>
```

The default directory is `.triadmux` in the current working directory. This repository ignores that name. The flag must come before the command name. `triadmux run --state-dir PATH ...` is rejected as an unrecognized argument and exits 2. The directory is created only when a real run is saved, in mode `0700`. `doctor`, `runs`, and `--dry-run` do not create it.

### `triadmux doctor`

Help today: "Discover provider executables on PATH".

Prints `{"providers": {...}}` and exits 0. It looks up `codex`, `claude`, and `grok` with a `PATH` search and does not start those processes. Each live provider has:

| Field | If the executable is on PATH | If it is not |
| --- | --- | --- |
| `executable` | path string | `null` |
| `auth` | `unchecked` | `unchecked` |
| `discovery` | `installed` | `missing` |
| `readiness` | `unverified` | `missing` |
| `enabled` | `false` | `false` |

`synthetic` is always present: `executable` is `null`, `auth` is `not_required`, `discovery` is `bundled`, `readiness` is `ready`, `enabled` is `true`. A missing live CLI does not fail the command. There is no overall health sentence and no "next command" line. Auth is never checked, and there is no login step.

### `triadmux run --demo TASK`

Help today: "Run the synthetic leader/reviewer workflow". `--demo` itself has no help text. `--demo` and `--provider` are mutually exclusive, and one of them is required.

This mode runs three in-process stages named `plan`, `review`, and `synthesize`. It does not start a provider process, does not use a temporary workspace, and does not apply byte or time limits. Limit flags or `--config` with `--demo` fail before any record is written. Standard error is `{"error": "execution configuration requires --provider"}` and the exit code is 1.

A blank or whitespace-only task fails the same way with `{"error": "task must contain text"}`. No record is written.

A real `--demo` run writes a JSON record and prints that record. On success the status is `completed`, the stage is `synthesize`, and `result` is text produced by the demo handoff. There is no `worker_review` object. `usage.provenance` is `unknown`, and both token counts are `null`. Exit code 0.

`--dry-run` prints a plan and does not write a record. For demo the plan has `status` `planned`, `provider` `demo`, `selection` `explicit`, the three stage names, and a `routing` object. It has no `limits` and no `workspace`. Routing marks `demo` as `selected`, `synthetic` as `requires_explicit_selection`, and `codex`, `claude`, and `grok` as `adapter_unavailable`. Exit code 0.

### `triadmux run --provider synthetic TASK`

`--provider` accepts only `synthetic`. `codex`, `claude`, and `grok` are invalid choices. Argparse exits 2 with "choose from 'synthetic'". That is fail-closed. Finding a binary with `doctor` does not make it selectable.

This mode runs the same three stage names in a bundled subprocess, one stage at a time. Each stage uses a controller temporary directory (`workspace` is `temporary` on a dry run) that is removed after the stage. On POSIX, a lifetime pipe stops the bundled worker if the controller dies. The child environment is an allowlist. API keys are not passed through.

Default limits, used when the flag and the config file omit the value:

| Limit | Default | Accepted range |
| --- | --- | --- |
| `--timeout` | 5 seconds | greater than 0 and at most 60 |
| `--max-input-bytes` | 65536 | 1 to 65536, counting the UTF-8 JSON request, envelope included |
| `--max-output-bytes` | 65536 | 1 to 1048576 stdout bytes |
| `--total-timeout` | no shared budget (`null`) | if set, greater than 0 and at most 180 |

`--config limits.toml` is allowed only with `--provider`. The file must contain one `[synthetic]` table and only the keys `timeout`, `total_timeout`, `max_input_bytes`, and `max_output_bytes`. Explicit flags override the file. Omitted keys keep the defaults. A bad file or an out-of-range number fails on standard error before a record is created. The state directory is not created in that case.

`--dry-run` with `--provider synthetic` prints the demo plan fields plus `limits` and `"workspace": "temporary"`. Default dry-run limits look like this shape: `stage_timeout` 5.0, both byte limits 65536, `total_timeout` null. It does not start workers and does not create a run record. It also does not check whether the task text fits the input limit. A dry run can look fine, and the real run can then fail with `input_limit`.

A real synthetic run writes the record first, with status `running`, then updates it after each stage. Success adds `result` and a `worker_review` object with `assignment` and `validation_step`. Usage is again unknown, with null counts. Exit code 0 when completed.

These failure codes are stored on the record, printed on standard output, and cause exit code 1:

| `error` | When |
| --- | --- |
| `input_limit` | The request is over the input cap. The worker for that stage is not started. |
| `output_limit` | Stage stdout exceeds the output cap. |
| `provider_timeout` | One stage exceeds its own timeout. |
| `budget_exhausted` | The shared `--total-timeout` runs out. Stopping workers can add time before the command returns. |
| `provider_exit` | The stage process exits with a failure before a result is accepted. |
| `malformed_response` | The stage output is not a valid result envelope. |
| `provider_unavailable` | The stage process cannot be started. |
| `stage_failed` | The stage raises an unexpected error. The private exception text is not stored. |

A keyboard interrupt stores `interrupted` and exits 1. That record may have no `error` field. The task string is not its own field. It can still appear inside `result` or `worker_review`, because those fields quote the work. Before the record is stored, environment values of at least 12 characters are replaced with `[redacted]` when the variable name contains `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, `API_KEY`, or `_KEY`. Shorter values are not redacted. The printed JSON is the redacted record.

The run id in the record is a canonical UUID. The examples in the flow document call that id `run_01`. Typing the letters `run_01` is not valid.

### `triadmux status RUN_ID`

Help today: "Read a run record". Prints the whole JSON file. That includes result text when the run completed. It is not a short summary.

Exit code 0 if the stored status is `completed` or `running`. Exit code 1 if the stored status is `failed` or `interrupted`, even though the read succeeded and the record is on standard output. Exit code 1 on standard error if the id is not a canonical UUID (`badly formed hexadecimal UUID string`, or `run ID must be a canonical UUID` for a non-canonical form) or if no file exists. A missing file reports a Python errno string and the full path.

### `triadmux runs`

Help today: "List saved run summaries". Prints `{"runs":[...]}` sorted by id. Each entry has only `run_id`, `status`, and `stage`. Task text and results are omitted. Status values in the list are `running`, `completed`, `failed`, and `interrupted`.

If the state directory is missing, the command prints `{"runs":[]}`, exits 0, and does not create the directory. Records that are not regular files, or that fail the schema, status, stage, or id check, are skipped with no warning. A person can have files on disk and still see an empty list.

### `triadmux recover RUN_ID`

Help today: "Mark an abandoned run interrupted". POSIX only. It does not rerun work, does not resume a stage, and does not launch a provider.

It needs the `.lock` file that the original run created beside the JSON record. If the controller still holds that lock, recovery exits 1 with `run is locked by another controller` and leaves the record unchanged. If this command can take the lock and the record is schema version 1 with status `running`, it sets status to `interrupted` and `error` to `controller_crash`, prints the record, and exits 0. A later `status` of that same run exits 1 because the run is interrupted.

Other refusals, all exit 1, record unchanged:

- `only running records can be recovered` if the run already finished, failed, or was interrupted.
- `run has no recovery lock` if the lock file cannot be opened. This same sentence is used when the state directory does not exist at all, so it can sound like a lost lock when the run was never there.
- `invalid or unsupported run record` for a bad schema or a mismatched id.
- `run recovery requires POSIX file locking` on non-POSIX systems.

A missing JSON file is not always the message `status` would print. Recovery checks the lock first.

## Gaps

### Clear first run

The README path is `doctor`, then `run --demo`, then `status`. The CLI never says that. After `doctor`, a person sees `enabled: false` on the tools they likely installed and `enabled: true` only on `synthetic`, with no sentence that says what to type next.

`--demo` and `--provider synthetic` are both required choices and neither help line says how they differ. `--demo` is the short offline handoff inside this process. `--provider synthetic` is the bounded subprocess path. Using limit flags on the README command fails.

The success id is one field inside a large JSON object. Nothing tells the person to copy `run_id` into `status`. The placeholder in conversation, `run_01`, is rejected.

`--state-dir` is easy to put in the wrong place, and `run --help` does not mention it. The main help line for the flag is blank.

Two error dialects meet on the first day. Usage mistakes are argparse text and exit 2. Product mistakes are JSON and exit 1. A failed run is JSON on standard output and exit 1. Those three shapes are easy to confuse.

### Reading doctor

`installed` plus `unverified` plus `enabled: false` looks like a half-finished setup. It means "a binary was found, it was not launched, and this version cannot route to it." `missing` means "not on PATH." Both leave the provider disabled. `auth: unchecked` looks like a step the person should complete. There is no auth command, and live sign-in is not part of this version.

There is no single health word, and exit 0 does not mean every named CLI is usable. It means the report was produced. The only ready provider is synthetic. Demo does not appear in the provider list even though `--demo` is a legal run mode. Routing mentions demo only on a dry run.

### Failure and recovery

The stable stage codes are useful for tests and opaque for a person. `input_limit` does not say that the worker was not started, that the cap includes the JSON envelope, or what flag to change. `budget_exhausted` does not say that cleanup can make the command return later than the budget.

`status` uses exit 1 for a run that failed. A script can branch on that. A person sees a failure of the status command. The record they need is on standard output, and the explanation is not.

`runs` can show `running` with no start time and no lock column. The way to learn whether that run is abandoned is to try `recover`, which fails if a controller is still alive. The error does not say "wait" or "this does not stop the other process."

`controller_crash` is written even when the person is the one deciding the old run is abandoned. Recovery does not replay the task. The help text "Mark an abandoned run interrupted" is accurate and easy to read as "get the work going again."

`runs` hides corrupt records. `status` and `recover` then speak in different sentences for the same missing id. A missing state directory becomes "no recovery lock."

`--demo` has no timeout because its stages are local functions. A person who copies `--timeout` onto the README command gets a hard error instead of a bounded demo. Synthetic defaults are conservative. Demo does not inherit them.

### Safe defaults

The safe path is the one the product already takes for live tools: do not launch them, and do not accept them as `--provider`. Keep that.

Synthetic defaults are 5 seconds per stage, 65536 input bytes, 65536 output bytes, and no extra shared budget until the person sets `--total-timeout`. Those defaults are not printed unless the person asks for a synthetic dry run. Demo does not use them.

Records land in the working directory unless `--state-dir` is set first. That is local-first and easy to do in the wrong project. The directory is private to the user (`0700`) and lock files are `0600`, which is the right default. Redaction is silent, which is correct, and it is not a promise that the task is safe to store. Unknown usage is stored as unknown, not as zero. That is the right default and it is easy to misread.

Dry run is the safe preview. It should stay free of side effects. It should not be described as proof that the task fits the input cap.

## CLI copy

Keep these names: `doctor`, `run`, `status`, `runs`, `recover`, `--demo`, `--provider`, `--dry-run`, `--timeout`, `--total-timeout`, `--max-input-bytes`, `--max-output-bytes`, `--config`, `--state-dir`.

Do not rename them in the next slice. Names below the heading "Proposed names" are not commands to add now.

Tone for errors: one stable code, one plain sentence, no traceback, no blame. Say what happened and the next legal action. Do not suggest a live provider. Do not suggest turning a check off. Do not quote private worker text. `stage_failed` must stay generic.

Where a code is already stored on run records, keep it: `input_limit`, `output_limit`, `provider_timeout`, `budget_exhausted`, `provider_exit`, `malformed_response`, `provider_unavailable`, `stage_failed`, `controller_crash`. Add a `message` string beside it. Do not replace those codes with prose.

Exit codes to document, not to change in the next slice:

| Situation | Exit |
| --- | --- |
| `doctor`, `runs`, dry run, completed run | 0 |
| `recover` when it updates the record | 0, even though the run is now interrupted |
| Product error JSON, or a run whose status is `failed` or `interrupted` | 1 |
| Argparse usage error | 2 |

`status` and `run` should say, in help text, that exit 1 means the run failed or was interrupted, not that the file could not be read. If the file could not be read, there is no record on standard output.

### Help text to ship

Main `--state-dir`:

> Directory for run records. Put this flag before the command. Default: .triadmux in the current directory. It is created only when a run is saved.

`doctor`:

> Look up Codex, Claude Code, and Grok on PATH. Do not launch them. Only the bundled synthetic provider is enabled.

`run`:

> Run plan, review, and synthesis offline. Choose --demo or --provider synthetic. Put --state-dir before run.

`--demo`:

> Run the three stages in this process. Does not apply time or byte limits. Writes a run record unless --dry-run is set.

`--provider`:

> Offline provider. The only accepted value is synthetic. Live CLIs are not a choice in this version.

`--dry-run`:

> Print the plan. Do not start workers and do not write a run record.

`--timeout`:

> Seconds for one synthetic stage. Default 5. More than 0 and at most 60. Requires --provider synthetic.

`--total-timeout`:

> Shared seconds across synthetic stages. Unset by default. At most 180. Requires --provider synthetic. Cleanup can make the command return a little later.

`--max-input-bytes`:

> Max UTF-8 bytes for one stage request, including the JSON envelope. Default 65536. At most 65536. Requires --provider synthetic.

`--max-output-bytes`:

> Max stdout bytes from one synthetic stage. Default 65536. At most 1048576. Requires --provider synthetic.

`--config`:

> TOML file with one [synthetic] table of limits. Flags win. Requires --provider synthetic.

`task` (the run positional):

> What the offline handoff should work on. Empty text is rejected.

`status`:

> Print one saved run as JSON. Exit 1 if that run failed or was interrupted. The id is the canonical UUID from run.

`runs`:

> List saved run ids, statuses, and stages. Omit task text and results. An empty list is printed if the state directory is missing.

`recover`:

> On POSIX, mark a leftover running run as interrupted. Do not rerun it. Requires the run's .lock file. Exit 0 if the record was updated. A later status of that run exits 1.

### Error sentences

Keep the current `error` text for this slice where tests already match it, and add `message`.

| Case | `message` |
| --- | --- |
| Empty task | The task has no text. Pass a short description of the work. |
| Limits or `--config` with `--demo` | Time and byte limits apply only with --provider synthetic. Remove them, or use --provider synthetic. |
| Timeout out of range | The stage timeout must be greater than 0 and at most 60 seconds. |
| Total timeout out of range | The shared timeout must be greater than 0 and at most 180 seconds. |
| Input cap out of range | The input limit must be from 1 to 65536 bytes. |
| Output cap out of range | The output limit must be from 1 to 1048576 bytes. |
| Bad config key or type | Say which rule failed, in the sentence already used, without a traceback. |
| `input_limit` | The request is larger than the input limit, including the JSON envelope. The worker was not started. |
| `output_limit` | A stage wrote more stdout than the output limit allows. Later stages did not run. |
| `provider_timeout` | A stage passed its timeout. Later stages did not run. |
| `budget_exhausted` | The shared time budget ran out. Stopping workers can take a little longer before this command returns. |
| `provider_exit` | The stage process exited with an error before a result was accepted. |
| `malformed_response` | The stage returned data that was not a valid result. |
| `provider_unavailable` | The stage process could not be started. |
| `stage_failed` | The stage failed. Details from the worker are not stored. |
| Id is not a canonical UUID | The run id must be the canonical UUID printed by triadmux run. |
| No record file | No saved run matches this id in the state directory. Try triadmux runs. |

Argparse can keep exit 2. The help text above should make "one of the arguments --demo --provider is required" rare. Do not claim in help that live provider names are accepted.

Doctor JSON should add a `summary` string, not a second colored status:

> Synthetic is ready and is the only enabled route. Demo is also available with triadmux run --demo. Codex, Claude Code, and Grok were not launched. Found on PATH means installed, not enabled. Missing means not on PATH. Auth was not checked. Next: triadmux run --demo "your task"

### Proposed names

Not for this version. Do not add them while live adapters are disabled.

- PROPOSED: `triadmux run --leader` and `--worker`, only after a live adapter exists and is still opt-in.
- PROPOSED: a later read-only `usage` view. Until then, usage stays inside the run record. Do not add a `budget` command that pretends token counts are money.
- PROPOSED: no `tui` command and no `serve` command in the next slice.

## CLI, terminal UI, or local web

Stay on the CLI. Build no text UI and no local web app in the next slice. Do not build a heavy dashboard now.

The only shipped surface is the CLI. Live adapters are disabled. A dashboard would have to draw a leader picker, worker assignment, a task tree, and quota or cost, and the product cannot do any of those. The only enabled route is synthetic, and every shipped run records usage as unknown with null counts. A chart of that data would show a guess.

Staged path:

1. Next slice. CLI copy only. Clearer `doctor` output and clearer run errors, as in the acceptance criteria below. Same command names. Same JSON for scripts. No new surface.
2. After one live adapter is enabled, documented, and fail-closed. Still the CLI. A person must be able to finish one real run and read it with `status` before any new view exists.
3. If many real runs make `runs` plus `status` hard to scan. A read-only terminal list is the first optional surface. It lists id, status, and stage, and it opens one record. It does not assign workers.
4. Only if a long result is painful to read in a terminal, and only after usage can be measured rather than unknown. Consider one local read-only page for a single run. Still not a dashboard, not a cost console, and not an auth flow.

A text UI is not cheaper than good help text. It adds focus, contrast, and cancel behavior that this CLI does not need while it prints one JSON document. A web app is a second product. It is not justified by an offline three-stage demo.

## WCAG 2.2 AA

Targets below are for a future terminal UI or local web page. They are not a request to build those surfaces. Plain CLI help has a smaller set.

### Applies to CLI help and errors now

- 1.4.1 Use of color, and 1.3.3 Sensory characteristics. Status is a word (`ready`, `missing`, `failed`, `interrupted`). Help and errors must not use color, position, or shape as the only cue. The current JSON already meets this. Keep it if color is added later.
- 3.3.1 Error identification. The message names the failed item in text: the task, the run id, the limit, or the provider choice.
- 3.3.2 Labels or instructions. Every flag and positional needs a help sentence. `--demo`, `--provider`, `--state-dir`, `task`, and `run_id` are unlabeled today.
- 3.3.3 Error suggestion. When a safe fix is known, say it. Example: limits were passed with `--demo`, so say to drop them or switch to `--provider synthetic`. Do not suggest a way around a safety check.
- 3.2.6 Consistent help. One mechanism: `--help` and `-h` on the program and on every command. Do not add a second, hidden help channel.

Plain language is the product rule that makes those criteria hold. Reading-level scoring (WCAG 3.1.5) is AAA, not AA. Still write the sentences for someone who has not read the source.

Contrast ratios do not apply to uncolored help text. The person's terminal theme is theirs. 1.4.3 and 1.4.11 apply only if TriadMux starts painting status. Pointer target size, reflow, focus order, and drag rules do not apply to help text. 3.3.8 does not apply today because there is no auth prompt.

### Future terminal UI

Apply the CLI rules above, plus:

- 1.4.3 contrast at least 4.5:1 for text, and 1.4.11 at least 3:1 for controls and state marks, against the theme the UI sets.
- 2.1.1 keyboard access, 2.1.2 no keyboard trap, and 2.1.4 a way to turn off or focus-limit single-character shortcuts.
- 2.4.3 a sensible focus order, 2.4.6 labels on every control, 2.4.7 a visible focus, and 2.4.11 focus not fully hidden.
- 2.2.1 a way to extend or turn off a session time limit. Ctrl-C must keep working. A shared run budget is a product limit, not an authorization timeout. The UI must say that the run stopped because the budget ended.
- 2.5.7 no action that can only be done by dragging. 2.5.8 at least 24 by 24 CSS pixels if the UI accepts pointer input.
- 4.1.3 status changes are text. A stage change cannot be color alone.
- 3.2.6 help in the same place on every view.
- 3.3.7 do not ask the person to type the same task again for a retry the product itself offers.

### Future local web page

Apply the terminal set, plus 1.3.1 (the heading and table structure is in the markup), 1.4.4 resize to 200 percent, 1.4.10 reflow at 320 CSS pixels without two-axis scrolling for the main view, 1.4.12 text spacing, 2.4.1 a skip link, 2.4.2 a page title, 2.4.4 link purpose, 3.1.1 a page language, and 4.1.2 name, role, and value for controls.

3.3.8 applies only to a PROPOSED sign-in. If that is ever added, do not use a puzzle, a memory test, or a transcription of an image as the login. 0.0.0 has no sign-in. Do not add one to meet this criterion.

Meeting WCAG is not a reason to build the web app. The CLI can meet the criteria that apply to help and errors.

## Acceptance criteria for the next CLI slice

This slice is doctor output and run errors, including the help text those commands need. It is done only when the checks below pass without a live provider. It does not include a text UI, a web page, a leader picker, worker assignment, a task tree, a quota view, or an auth prompt. It does not change `recover` wording. That stays a later CLI slice.

Doctor:

1. `triadmux doctor` exits 0 and prints JSON. `providers.synthetic` is `enabled` true, `readiness` `ready`, `discovery` `bundled`, `auth` `not_required`, and `executable` null.
2. `codex`, `claude`, and `grok` are `enabled` false. If the name is not on `PATH`, `discovery` and `readiness` are `missing` and `executable` is null. If the name is on `PATH`, `discovery` is `installed`, `readiness` is `unverified`, `auth` is `unchecked`, and `enabled` is still false.
3. A fake `codex`, `claude`, or `grok` on `PATH` that would record a launch is not executed. The launch record stays empty.
4. The JSON includes a plain `summary` string that says only synthetic is enabled, demo is available, live CLIs were not launched, and found-on-PATH is not enabled. The summary does not depend on color.
5. Missing live CLIs do not change the exit code.
6. `triadmux doctor --help` says that discovery does not launch providers and does not enable them.

Run errors and run help:

7. `triadmux --help` gives `--state-dir` a sentence and says the flag comes before the command. `triadmux run --help` repeats that placement. `run --help` also states the `--demo` versus `--provider synthetic` difference, that dry run does not write a record, and that exit 1 from `run` and `status` means a failed or interrupted run.
8. A whitespace-only task with `--demo` or `--provider synthetic` exits 1, prints JSON on standard error, includes a plain `message` that the task has no text, and creates no state directory.
9. `--timeout`, other limit flags, or `--config` together with `--demo` exits 1, does not write a record, and the message says to drop the limits or use `--provider synthetic`.
10. Out-of-range limits and a bad TOML file exit 1 with JSON on standard error, no traceback, and no state directory. `--provider codex` stays an argparse exit 2 and is not silently accepted.
11. A synthetic run whose request exceeds the input cap exits 1, writes a failed record with `error` `input_limit`, and includes a `message` that the worker was not started. The same pattern applies to `output_limit`, `provider_timeout`, and `budget_exhausted`: the stored code is unchanged, and a `message` says what stopped.
12. An unexpected stage failure stores `stage_failed` only. A private exception string from the stage does not appear in the record or on standard error.
13. `--dry-run` for synthetic exits 0, prints `planned`, includes limits and `"workspace": "temporary"`, and creates no state directory. `--dry-run` for demo exits 0, has no `limits` and no `workspace`, and creates no state directory.
14. `triadmux runs` with a missing state directory exits 0, prints `{"runs":[]}`, and does not create the directory.
15. Checks 1 through 14 pass with the synthetic provider and fixtures only. No test starts Codex, Claude Code, or Grok.
