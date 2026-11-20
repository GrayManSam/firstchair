# UI specifications

The shipped interface is the `triadmux` CLI. These specs cover the next
CLI copy slice and the static concept page. They do not add commands.

## CLI, next slice

Source of the sentences: `docs/design/ux-audit.md`. Keep current `error`
codes where tests already assert them. Add a `message` a person can read.

Help, program:

```text
usage: triadmux [-h] [--version] [--state-dir PATH] {doctor,run,status,runs,recover} ...

Local controller for a bounded coding handoff. Version 0.0.0 runs a
synthetic plan, review, and synthesis. doctor looks for Codex, Claude
Code, and Grok on PATH and does not start them.
```

Help, doctor: "Report which tools are on PATH. Found means installed,
not enabled. Synthetic is the only enabled route."

Help, run: "Run a synthetic handoff. Pass --demo or --provider synthetic,
and a task. Limits apply only with --provider synthetic."

`--demo` help: "Run the in-process demo. Ignores limit flags."

`--provider` help: "Provider to run. The only choice is synthetic."

`--state-dir` help: "Directory for run records. Default: .triadmux"

`task` help: "What the handoff should review, in one sentence."

`run_id` help: "Canonical UUID printed by triadmux run."

Doctor summary string, inside the JSON as `summary`, not instead of the
machine fields:

```text
Synthetic is ready and is the only enabled route. Demo is also available
with triadmux run --demo. Codex, Claude Code, and Grok were not launched.
Found on PATH means installed, not enabled. Missing means not on PATH.
Auth was not checked. Next: triadmux run --demo "your task"
```

Error messages for the cases in the UX audit stay as written there.
Argparse may still exit 2. Do not list live provider names as accepted
choices.

Acceptance for this slice is the list already in `docs/design/ux-audit.md`.
A concept page does not satisfy it.

## Concept page

One static file, `docs/brand/prototype/index.html`. Preferred skin is
direction A. A control swaps B and C for comparison. The control is
labeled "Direction" and is a group of three buttons with
`aria-pressed`.

### Regions

1. Header: mark, wordmark, the word Provisional, links to the docs in this folder.
2. Hero: tagline, one true sentence, install commands, link to the public GitHub repository.
3. Facts: four items that are true today.
4. Stages: plan, review, synthesis.
5. Transcript: sample, captioned.
6. Limits: what the page will not claim.
7. Footer: MIT, version 0.0.0, independent project, link to the upstream review.

### Responsive

- Under 720px the hero stacks. Buttons become full width. The transcript scrolls sideways inside `<pre>` rather than stretching the page.
- At 720px and up, the hero is two columns. Facts are a 2×2 grid. Stages are a row of three.
- No horizontal page scroll at 360px width except inside the transcript.

### Keyboard

- Skip link to `#facts`.
- Tab order follows the visual order.
- Direction buttons are real buttons.
- Copy buttons copy the adjacent command and announce "Copied" in an `aria-live="polite"` region.
- Focus outline uses the direction's focus token and is not removed.

### Reduced motion

No entrance animation. The direction swap is instant.

### Sample data

The transcript may show a fake run id `00000000-0000-4000-8000-000000000001`
and the word unknown for usage. It must not show a dollar amount, a token
count, a leader model, or a claim that Codex, Claude, or Grok replied.

## Explicitly not specified

A TUI layout, a local web dashboard, an auth screen, and a cost view.
The staged path in the UX audit is the gate for those.
