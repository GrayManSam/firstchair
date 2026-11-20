# Brand direction C — Job ticket

Provisional name: Benchdog. Not applied to the package. Examples use
`triadmux`.

## Thesis

A print shop job ticket. The work is a slip of paper that travels from
plan to review to synthesis and comes back stamped. The page is
newsprint and ink, with one rubber-stamp red. Rules are heavy. The peg
is a stamp, slightly off square, as if it hit the page by hand.

Personality: plain, a bit loud, practical. It talks like a counter
person: what you asked for, what finished, what did not.

Impression: "I could pin this above the bench."

Positioning: the same honest local CLI. The ticket makes the three
stages visible as a sequence, which is the shipped workflow, without
inventing a task tree UI.

Tagline: One ticket. Three stages. Then a record.

## Voice

Do: "Ticket: review the build. Stages: plan, review, synthesis. Result
stored locally. Usage unknown."

Don't: faux letterpress poetry, fake "job no. 00421" presented as a
real run, or a stamp that says APPROVED when the only finished path is
a synthetic demo.

Do: call sample numbers sample.

Don't: distress the type until it fails contrast or becomes hard to
read at 16px.

## Mark

The peg is drawn as a rubber stamp: ink outline, a square hole, a peg,
rotated 6 degrees on the hero only. In the favicon the rotation is 0.
Rotation at 16px makes the stem blur, so the small sizes are upright.

- Logotype: "benchdog" in a sturdy serif, not a script.
- Monochrome: stamp red becomes ink. The stamp still reads.
- Favicon: upright peg, filled.
- Dark variant: newsprint ink #F3EDE3 on #241C18, stamp in #F0B0A6 for small text. The prototype's default is light.
- Do not scan a real rubber stamp. Draw it in SVG so the edge stays sharp.

## Color

| Token | Hex | Role |
| --- | --- | --- |
| newsprint | #F3EDE3 | Page |
| slip | #FFF9F1 | Ticket cards |
| ink | #1A1A1A | Text and rules |
| graphite | #4E4944 | Secondary text |
| stamp | #9E2B1A | Links, the stamp, the current stage |
| stamp-on | #FFF9F1 | Text on a stamp-colored button |
| ok | #1E5C38 | Ready, as a word |
| rule | #1A1A1A | 2px rules |

`stamp` on `newsprint` is for links and short labels. Body text is
`ink`. A full-bleed stamp button uses `stamp-on` on `stamp`.

## Type, space, motion

- Display: Rockwell, Liberation Serif, Times New Roman, serif. System fonts. Rockwell is not free to embed. Do not download it. Liberation Serif is the METRICS-compatible free fallback on Linux and is licensed under the GPL with the font exception, which permits embedding. The prototype does not embed it; it names it and falls through.
- Body: system-ui, Segoe UI, sans-serif. The serif is for the name and the ticket title only.
- Commands: ui-monospace, Consolas. A ticket's command line is the one place type becomes mechanical.
- Scale: 17px body so the newsprint page does not look like a footnote. Hero 46px.
- Space: 8px grid. Tickets have a 2px ink border and 20px padding. Sections separated by a full-width 2px rule, not by whitespace alone.
- Radius: 2px. The stamp's hole stays square. Buttons are rectangles.
- Shadow: none. A second offset border, 4px down and right, in stamp at 30% opacity, sits behind the hero ticket only.
- Icons: none, or a single numbered index (01, 02, 03) in the serif. Numbered stages match plan, review, synthesis.
- Motion: the hero stamp does not wiggle. Reduced motion changes nothing visible, because nothing moves.

## Page and product

Hero: a ticket. Perforation is a repeating CSS radial gradient, not an
image. Fields: product, version 0.0.0, status "synthetic only", the
tagline, the install commands, a stamp of the peg.

Navigation: a top rule, text links, the current one in stamp color and
underlined.

Three stage cards in order, labeled Plan, Review, Synthesis, each with
one true sentence. A fourth note: "Live Codex, Claude Code, and Grok
adapters are not on this ticket."

Terminal: set inside the ticket as "shop copy," the same demo commands,
captioned as a sample.

Social card: a ticket crop, the peg stamp, the tagline. No fake job
number presented as telemetry.

README: a short rule, the wordmark, the four-line opening. Optional
stamp SVG.

Docs: newsprint, 2px rules, stamp-colored current heading in the rail.
Code on `slip`.

Application: a blank ticket and a filled sample ticket for one run.
Fields that do not exist (cost, tokens, leader model) are omitted, not
zeroed. Usage line: unknown. This is a specimen, not a product screen.

States: hover fills a link underline. Focus is a 3px ink outline,
offset 3px, which reads as a second stamp. Error replaces the stamp
word READY with FAILED in `stamp` color plus the word. Empty ticket:
"No runs punched on this slip." Loading: not used.

## Fit

Strengths: the three shipped stages become the layout, so the brand
teaches the product. High contrast. Memorable next to a typical dark
developer site. Still original: a job ticket, not a terminal cosplay
and not a pastel orb.

Weaknesses: the print metaphor can look like a restaurant menu if the
rules get decorative. Rotation and perforation must stay subtle.
"Stamp of approval" language will overclaim if a writer gets sloppy.

Complexity: medium. Perforation and the offset border are pure CSS.
The stamp is one SVG. No textures, no photographs.

Differentiation: paper, a heavy rule, and a red stamp. A reviewer
flipping from A to B to C should not think they are color swaps of one
system.
