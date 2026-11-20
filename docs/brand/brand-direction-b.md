# Brand direction B — Pin and hole

Provisional name: Benchdog. Not applied to the package. Commands in
examples stay `triadmux` until a rename is approved.

## Thesis

An instrument, not a workshop postcard. The same peg-and-hole mark is
drawn as geometry: a circle in a square, measured, with the clearances
visible. The page is near-black, the type is a plain grotesque, and one
cobalt line means "this is the action." It should feel like a gauge on
a bench, not like a hacker movie.

Personality: exact, quiet, adult. Short sentences. Numbers when they
exist, and the word "unknown" when they do not.

Impression: "This was built by someone who has read a process table."

Positioning: a bounded local controller. The aesthetic may be technical.
The claims may not grow to match it.

Tagline: A peg for the task. A record when it stops.

## Voice

Do: "Stage plan finished. Stage review finished. Usage: unknown."

Don't: all-caps slogans, "not your keys" pastiche, fake shell prompts
that claim a daemon is listening, or progress bars made of block
characters for data the product does not have.

Do: name the flag and the bound. `--total-timeout 10` means ten seconds
across the stages.

Don't: imply a network service. There is no port.

## Mark

The mark is the same object as direction A, reduced to geometry. A
square hole, a circular head, a rectangular stem. Stroke 2px at 24px,
filled only in the favicon so it survives 16px.

- Logotype: "BENCHDOG" in small caps tracking is tempting and wrong. Use "benchdog" in the grotesque, medium weight, no letterspacing games.
- Monochrome: chalk on ink, or ink on chalk.
- Favicon: filled peg, 2px safe area.
- Dark is the default. Light is the same drawing on #F4F1EA with #142033 ink, for docs that must be printed.
- Illegible failure: if the hole and the head are both stroked at 16px, they merge. Fill the head.

## Color

| Token | Hex | Role |
| --- | --- | --- |
| ground | #121410 | Page |
| panel | #1C1F1A | Cards |
| chalk | #F4F1EA | Primary text |
| mist | #C4C0B6 | Secondary text |
| line | #34382F | Borders |
| cobalt | #8FB4FF | Links and focus on ground. Passes as text. |
| action | #D7E4FF | Button fill |
| action-ink | #10203A | Button label |
| ok | #9DDBB4 | The word Ready, with the word itself |
| stop | #FFB4A8 | The word Failed, with the word itself |

Do not use #2F6BFF for small type on this ground. It fails contrast.
Cobalt here is the lightened token above.

## Type, space, motion

- UI and display: system-ui, Segoe UI, sans-serif. One family. Weight 560 for the hero, 400 for body. No display serif.
- Commands: ui-monospace, Menlo, Consolas. Tabular figures where a limit is a number.
- Scale: 16px body. Hero 44px, line-height 1.1, max measure 22em.
- Space: 8px grid, cards 20px, sections 56px.
- Radius: 4px. The hole in the mark is the only square with a hard corner story. Buttons are 4px, not pills.
- Border: 1px `line`. No drop shadow. Depth is a second border, not blur.
- Icons: the same 24px strokes as A, in chalk. Fewer of them. A status is a word inside a 1px box.
- Motion: none by default. Focus outline appears instantly. Reduced motion is the baseline, not a special case.

## Page and product

Hero: left column is the sentence and the install block. Right column
is the mark at 160px, captioned "Peg in a dog hole." No illustration of
robots.

Navigation: text links only. Current page is underlined, not tinted
alone.

Feature list: a definition list, not a card grid. Term, then one
sentence. Four terms: doctor, synthetic run, limits, local record.

Terminal: a panel the same color as `panel`, chalk text, a cobalt
prompt character. The transcript is the shipped demo path. A caption
states that the transcript is illustrative sample output, not a live
capture from this session.

Social card: ground, the geometric peg, the tagline, "v0.0.0". No
fake star count.

README: no banner image required. If one is added, it is the geometric
peg and the one-sentence explanation.

Docs: the light variant. Code blocks use `panel` and `chalk` so a
command is obvious. Links are #1D4ED8 on the light ground (re-check
before shipping; the prototype's light switch uses the dark page).

Application: still no dashboard. A "run record" specimen shows the JSON
fields the CLI already stores: run id, status, stage, usage unknown.
Labeled sample.

States: hover on the action button mixes 6% ground into the fill. Focus
is a 2px cobalt outline. Error text uses `stop` plus the word Failed.
Empty is a single sentence in mist. There is no loading skeleton,
because the page does not fetch.

## Fit

Strengths: reads as a developer tool without borrowing a terminal-punk
costume. The mark stays geometric and owns the name. Low implementation
cost.

Weaknesses: near-black pages are common. The cobalt must stay scarce or
this becomes another dark SaaS skin. The voice can turn cold if every
sentence drops its verb.

Complexity: low. System fonts, borders, one SVG.

Differentiation: measured and quiet. Not acid green, not glass, not a
warm wood shop. Someone comparing A and B should feel a change of
posture, not a theme toggle.
