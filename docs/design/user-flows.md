# User flows — TriadMux 0.0.0

The first four flows are the shipped CLI. The last two are PROPOSED. They are not screens, commands, or prompts in this version. Version 0.0.0 does not launch Codex, Claude Code, or Grok, and it cannot route a run to them.

Sample ids in this document are `run_01` and `run_02`. The program prints a canonical UUID. `run_01` is a stand-in for that UUID, not an id the CLI accepts. There are no captured transcripts here. Result text is described, not quoted from a machine.

The actor in every shipped flow is a person at a terminal in a checkout of this project. The state directory is `.triadmux` in the current directory unless the example says otherwise. That flag belongs before the command name.

## 1. Install and first successful demo

Shipped path. This is the offline demo, not a live provider and not the synthetic subprocess.

**Actor.** A first-time user with Python 3.12 or newer.

**Entry.** A fresh checkout. No `.triadmux` directory yet. The user wants to see a finished handoff without calling Codex, Claude Code, or Grok.

**Steps.**

1. Create a virtual environment, activate it, and run `python -m pip install -e .`.
2. Run `triadmux --version` and confirm it prints `0.0.0`.
3. Run `triadmux doctor`.
4. Run `triadmux run --demo "Review the project's build instructions"`.
5. Read `run_id` from the printed JSON. In this write-up that id is `run_01`.
6. Run `triadmux status` with that id.

**System response.** Install puts `triadmux` on the environment path. `doctor` exits 0 and prints provider JSON. `synthetic` is ready and enabled. Any of `codex`, `claude`, and `grok` may be missing or installed, and each of those three has `enabled` false. Nothing is launched.

The demo run exits 0 and prints one record: schema version 1, id `run_01`, status `completed`, stage `synthesize`, a text `result` from the in-process handoff, and `usage` with provenance `unknown` and null token counts. There is no `worker_review` object. The same object is written under `.triadmux/` as a JSON file, plus a lock file on POSIX. `status` prints that record again and exits 0.

**Failure.** If Python or pip cannot install the package, the CLI never starts. Say so in the install tool's own error. Do not invent a `triadmux` recovery step.

If the task is empty or only spaces, the command exits 1, prints `{"error": "task must contain text"}` on standard error, and does not create `.triadmux`.

If the user adds `--timeout` or `--config` to this demo command, it exits 1 with `execution configuration requires --provider` and does not write a record. Limits belong on flow 3.

If `--state-dir` is placed after `run`, argparse exits 2 and prints an unrecognized-argument error. The working form is `triadmux --state-dir PATH run --demo "task"`.

`doctor` failing to find a live CLI is not a failure of this flow.

**Empty state.** Before step 4, `.triadmux` does not exist. `triadmux runs` prints `{"runs":[]}` and does not create the directory. `doctor` still returns the synthetic provider as ready. There is no previous run to open.

## 2. Doctor when a CLI is missing

Shipped discovery. No launch.

**Actor.** The same user, or someone checking a machine before they trust the tool list.

**Entry.** `triadmux doctor`. At least one of `codex`, `claude`, or `grok` is not on `PATH`. Example: Grok is absent, Codex is present as a binary, Claude Code is absent.

**Steps.**

1. Run `triadmux doctor`.
2. Read each live provider's `discovery`, `readiness`, and `enabled` fields.
3. Do not run a command that selects `grok`, `codex`, or `claude`. The CLI will reject those names.

**System response.** Exit 0. No live executable is started. The missing names have `executable` null, `discovery` `missing`, `readiness` `missing`, `auth` `unchecked`, and `enabled` false. A name that is on `PATH` has a path in `executable`, `discovery` `installed`, `readiness` `unverified`, `auth` `unchecked`, and `enabled` false. `synthetic` stays `discovery` `bundled`, `readiness` `ready`, `enabled` true, `auth` `not_required`. Auth is not prompted and not checked. The report does not by itself say which command to run next.

**Failure.** This report is not a failed health check. Exit 0 with a missing CLI is the success case for discovery. A real failure is the CLI not being installed, which is flow 1, or a bug that prevents the JSON from printing.

Choosing a live name anyway is a different command: `triadmux run --provider grok "task"` exits 2. Argparse says the only choice is `synthetic`. No run record is created.

**Empty state.** All three live CLIs missing. The `providers` object still includes `codex`, `claude`, `grok`, and `synthetic`. The three live entries are `missing` and disabled. Synthetic is still the enabled route. An empty live list is not an empty product.

## 3. Dry run, then a real synthetic run

Shipped path. This is the bounded subprocess, not `--demo`.

**Actor.** A user who wants to see the plan and the limits before anything is stored.

**Entry.** `triadmux run --provider synthetic`, with optional limit flags or `--config`. No need for a prior demo run.

**Steps.**

1. Run `triadmux --state-dir PATH run --provider synthetic --dry-run --timeout 5 --total-timeout 10 "Review the build"`. `PATH` is any directory the user chooses. It does not need to exist yet.
2. Read the plan.
3. If the plan is the intended provider and limits, run the same command without `--dry-run`.
4. Read `run_id` from the printed record. This write-up calls it `run_01`.

**System response.** The dry run exits 0. It prints `status` `planned`, `provider` `synthetic`, `selection` `explicit`, stages `plan`, `review`, and `synthesize`, and routing: synthetic `selected`, demo `requires_explicit_selection`, and the three live names `adapter_unavailable`. `limits` show the stage timeout, both byte caps, and the total timeout. `workspace` is `temporary`. The state directory is not created. No worker starts.

The real run exits 0 when all three stages finish. It prints a record for `run_01` with status `completed`, stage `synthesize`, a `worker_review` object (`assignment` and `validation_step`), a text `result`, and unknown usage with null counts. Each stage runs in a temporary workspace that is removed afterward. The record and its `.lock` file are under the state directory. Secret environment values of at least 12 characters, for names that look like secrets, are stored as `[redacted]`.

If the user omits every limit, the dry run shows the defaults: 5 seconds per stage, 65536 input bytes, 65536 output bytes, and `total_timeout` null.

**Failure.** A bad limit or a bad config file fails on the dry run too, because those values are checked before the plan is printed. Standard error is JSON, exit 1, and the state directory is not created. Examples of the current `error` text: the stage timeout must be greater than 0 and at most 60 seconds; the shared timeout must be greater than 0 and at most 180 seconds; the input limit must be between 1 and 65536 bytes; the output limit must be between 1 and 1048576 bytes; unknown config keys and wrong JSON types name the config rule.

A dry run does not prove the task fits the input cap. The real run can still exit 1 with a failed record whose `error` is `input_limit`. That record exists. The worker for the oversized request is not started.

A stage can also fail the record with `output_limit`, `provider_timeout`, `budget_exhausted`, `provider_exit`, `malformed_response`, `provider_unavailable`, or `stage_failed`. The command prints that record on standard output and exits 1. `stage_failed` does not include the worker's private exception text. If the shared budget ends, the process may still spend a short time stopping workers.

`--demo` and `--provider synthetic` together exit 2. Neither flag exits 2 with "one of the arguments --demo --provider is required."

**Empty state.** No earlier runs. After the dry run, `triadmux --state-dir PATH runs` still prints `{"runs":[]}` if the directory was never created, and it does not create it. After a failed real run, the list has one row: `run_01`, status `failed`, and the stage that stopped. The list does not include the task or the error sentence. `status` does.

## 4. Status, the run list, and recovery

Shipped path. Recovery updates a leftover record. It does not continue the work.

**Actor.** A user whose earlier synthetic or demo run is still marked `running` because the controller stopped, or a user who only wants to inspect saved runs.

**Entry.** A state directory that may contain records. This write-up uses `run_01` as a running abandoned run and `run_02` as a completed one. On a real disk those names are canonical UUIDs. `run_01` has a `.json` record and a `.lock` file. No controller is holding the lock.

**Steps.**

1. Run `triadmux --state-dir PATH runs`.
2. Run `triadmux --state-dir PATH status` with the id to inspect.
3. If the row is `running` and the user believes the controller is gone, run `triadmux --state-dir PATH recover` with that id.
4. Run `status` again on the same id.

**System response.** `runs` exits 0 and prints only id, status, and stage. Example shape, not a captured listing: `run_02` is `completed` at `synthesize`, and `run_01` is `running` at `review`. Task text and results are not in this list.

`status` on `run_02` exits 0 and prints the full record, including `result` if that field was saved, and `usage` if that field was saved. Older records without `usage` are printed as stored.

`status` on a failed or interrupted run exits 1 and still prints the record on standard output. The exit code is the run outcome.

`recover` on abandoned `run_01` exits 0. It prints the record with status `interrupted` and `error` `controller_crash`. It does not start a worker and does not change the stage name. The following `status` prints that same record and exits 1.

If a controller still holds the lock, `recover` exits 1, prints `run is locked by another controller` on standard error, and does not change the record.

**Failure.** `status` or `recover` with `run_01` typed as those literal letters exits 1 with `badly formed hexadecimal UUID string`. A UUID that is not in canonical text form exits 1 with `run ID must be a canonical UUID`.

`status` for a well-formed id that was never saved exits 1 with a file-not-found string and the path it tried. `recover` for that same missing id exits 1 with `run has no recovery lock`, including when the state directory itself is absent. Those two sentences do not match, and the recover sentence can be read as "the lock was lost" when the run was never created.

`recover` on a completed, failed, or already interrupted run exits 1 with `only running records can be recovered` and does not rewrite it. An unsupported schema exits 1 with `invalid or unsupported run record`. On a non-POSIX system, recover exits 1 with `run recovery requires POSIX file locking`.

A keyboard interrupt during a run is not this flow. That path already stores `interrupted` and exits 1. Recover will then refuse it because it is no longer `running`.

**Empty state.** The state directory is missing, or it has no valid records. `runs` prints `{"runs":[]}`, exits 0, and does not create the directory. Corrupt files are skipped, so the list can be empty while files are present. There is no row to recover. `status` and `recover` on an id the user hoped was there follow the failure sentences above. `doctor` is unrelated and can still report synthetic as ready.

## 5. PROPOSED later: choose a leader and workers

This flow is not implemented. There is no leader picker, no worker assignment screen, and no task tree. Do not document it as a control the user can operate in 0.0.0.

**Actor.** A user, only after at least one live adapter is enabled, version-checked, and fail-closed. That gate is not met today.

**Entry.** PROPOSED command shape, not a shipped interface: the user would start from `doctor`, see a provider whose readiness is verified and whose `enabled` field is true, and only then pass an explicit leader. A possible future flag is `--leader`, with workers chosen the same explicit way. Those flags must not exist until an adapter can honor them.

**Steps.**

1. PROPOSED: run `doctor` and read enabled versus disabled. Installed and unverified stays disabled.
2. PROPOSED: pass the leader and workers by name on the command line. Do not infer them from `PATH`.
3. PROPOSED: show a dry run that lists the selected leader, the workers, and the routing reason for every name that was not selected.
4. PROPOSED: start the run only after that plan. The user can still cancel before a record exists by stopping at the dry run.
5. The user inspects the result with the shipped `status` and `runs` commands.

**System response.** PROPOSED: the dry run names the leader and the workers and says why other providers were not used. A real run would then record the same selection on the run record. Until an adapter exists, the shipped response to a live name remains the argparse error that the only provider choice is `synthetic`.

**Failure.** Today, selecting `codex`, `claude`, or `grok` exits 2 and writes nothing. That refusal stays until the adapter work is done.

PROPOSED failures once selection exists: an unknown name is rejected before a record is written; a provider that is installed but not verified is rejected with the reason, not started; a provider that disappears between dry run and the real run fails closed with no partial live work presented as success. A missing choice does not silently fall back to another live CLI.

**Empty state.** PROPOSED: `doctor` shows no verified live provider. The plan says there is nothing to assign, and the only runnable routes remain `--demo` and `--provider synthetic`. The user is not shown an empty task tree or an empty assignment board, because those screens are not part of the product.

## 6. PROPOSED later: unknown usage versus measured usage

This flow is not a dashboard and not a budget screen. 0.0.0 does not measure tokens, quota, or money. Shipped runs store usage as unknown.

**Actor.** A user reading a finished or failed run, now, and later a user who is allowed to set a limit only when the product can measure what it limits.

**Entry.** Today: `triadmux status` on a saved id such as `run_01`. PROPOSED later: the same record, after a live adapter can attach measured usage, plus an explicit budget the user sets. There is no `usage` command and no cost page.

**Steps.**

1. Run `status` on `run_01` and read `usage`.
2. Treat `provenance` `unknown` and null `input_tokens` and `output_tokens` as "not measured." Do not treat null as zero.
3. If the concern is time or bytes, set the shipped synthetic limits (`--timeout`, `--total-timeout`, `--max-input-bytes`, `--max-output-bytes`, or `--config`) and preview them with `--dry-run`. Those limits are not a token budget and not a price.
4. PROPOSED, only after a live adapter records measured usage: read a provenance of `measured` or `estimated` on the same record, with counts only when they were actually observed. Estimated values must be labeled estimated. Unknown must stay null.
5. PROPOSED: set a budget in a dry run that shows the unit (tokens or another named unit, never a silent currency conversion). The real run rejects work that would pass the budget before the provider is asked to do that work, using the same style of stored error code as today's `budget_exhausted` and `input_limit`.

**System response.** Today, step 1 prints the record. For a current demo or synthetic run, `usage` is exactly provenance `unknown` and both counts null, including when the run failed for a byte or time limit. A legacy record may omit `usage`; `status` prints the file as it was saved.

Time and byte limits, when exceeded, already fail the run with a stored code. They do not fill in token counts.

PROPOSED response after measurement exists: `status` shows the provenance word next to any number, and a budget dry run shows the cap and the unit. No chart is required for that.

**Failure.** Today there is nothing to get wrong about a missing price, because no price is shown. The failure to avoid is displaying unknown as 0, or adding a budget flag that the synthetic provider cannot enforce as money.

A person who wants a token cap now has no such flag. Point them at the byte and time limits. Do not invent a cost.

PROPOSED failure: if the adapter does not return usage, the record stays `unknown` and null. The run can still complete. A budget that cannot be evaluated fails the run before the live call, with a plain message, rather than guessing. A measured value and an estimated value are never shown as the same kind of number.

**Empty state.** A new state directory has no runs, so there is no usage to total. `runs` is `{"runs":[]}`. PROPOSED: a usage summary over zero runs says that nothing has been measured. It does not show a zero-cost account, a quota bar, or a forecast. Those views are not part of this product.
