# Brand direction A — Day bench

Provisional name: Benchdog. This direction is not applied to the CLI,
the README title, or the GitHub repository. Sample commands use today's
`triadmux` binary, because that is what runs.

## Thesis

A workbench in daylight. The tool is a peg, not a pilot. The person
keeps their hands on the work. The page should feel like a clean bench:
warm wood, a metal pin, pencil notes, and one honest terminal card.

Personality: calm, specific, a little fond of materials. It does not
wink, and it does not shout about autonomy.

Impression: "I can see what this does before I install it."

Positioning: one local command that shows which coding tools are
installed and runs a bounded offline handoff. Not a hosted agent, not a
quota product, not a multiplexer.

Tagline: Hold the work. You still make the cut.

## Voice

Do: name the command, the limit, and the place the record is stored.
Say when a number is unknown. Say that live tools are not launched.

Don't: "autonomous," "unlimited," "one prompt and we handle the rest,"
"bypass the rate limit," or any sentence that implies Codex, Claude
Code, or Grok ran when they did not.

Do: "Synthetic is ready. Codex is on PATH and was not started."

Don't: "All three agents are online."

## Mark

The symbol is a round-headed peg sitting in a square hole. At 16 pixels
the hole becomes a ring and the peg a dot with a short stem. It is not
a person, not a root system, and not three blades.

- Logotype: "benchdog" in sentence case, lower, with the peg to the left.
- Monochrome: ink peg on a maple square, or a maple peg knocked out of an ink square.
- Favicon: the peg alone, optically centered, 2px padding.
- App icon: same peg, maple ground, ink pin. No gloss, no gradient mesh.
- Dark variant: maple peg on #1C1915. Light variant: ink peg on #F4EFE6.
- Small-size test: the stem must stay at least 2px wide at 16px, or the mark becomes a blob. Prefer a slightly fatter stem over a delicate one.

## Color

All values are the pairs the prototype uses. Text tokens were checked
against WCAG 2.2 AA (4.5:1) for body size. The brass fill is a control
color, not small text.

| Token | Hex | Role |
| --- | --- | --- |
| maple | #F4EFE6 | Page ground |
| paper | #FFFBF5 | Cards |
| ink | #1C1915 | Text and the peg |
| ink-soft | #4A433A | Secondary text |
| rule | #D9D0C3 | Borders |
| brass | #A56B1F | Primary button fill |
| brass-ink | #1C1915 | Text on the brass button |
| pine | #1B5E3B | Success word and focus-safe link on maple |
| clay | #8E2F24 | Error word |
| chalk | #F7F1E6 | Text on ink |

`pine` on `maple` and `clay` on `maple` are for short labels. Body copy
stays `ink`. Do not use brass as the only way to say "ready."

## Type, space, motion

- Display: Iowan Old Style, Palatino Linotype, Palatino, Georgia, serif. System fonts. No webfont download. If a later site licenses a serif, use an OFL face such as Source Serif 4 and keep the metrics close to Palatino.
- UI: Segoe UI, system-ui, sans-serif.
- Commands: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace.
- Scale: 16px body, 1.5 line-height. Display 40–56px, line-height 1.05, tracking -0.02em.
- Space: 8px grid. Cards pad 24px. Section gap 64px desktop, 40px under 720px.
- Radius: 12px cards, 999px the peg head only. Buttons 8px. Do not round the page into pills.
- Shadow: one soft shadow, `0 16px 40px rgb(28 25 21 / 8%)`. No glass blur.
- Icons: 24px stroke icons, 1.75px, round caps, ink. The peg is the only filled symbol.
- Motion: the peg does not bounce. A card may fade 160ms. `prefers-reduced-motion: reduce` sets every transition to 0ms. No autoplay.

## Page and product

Hero: peg, wordmark, the tagline, one sentence that names version 0.0.0
and the synthetic handoff, then two actions: copy the install commands,
and jump to "what works today." A third quiet link goes to the GitHub
repository.

Navigation: Product, What works today, Commands, Limits, GitHub.

Feature row, four cards, all true today:

1. Doctor, without launching.
2. A synthetic plan, review, and synthesis.
3. Limits, a dry run, and a local record.
4. Secret redaction and an allowlisted child environment.

Terminal card: a real-shaped session using `triadmux`, labeled "Commands
as they run today." No invented usage totals. The usage line says
unknown.

GitHub social card: maple ground, peg, "Benchdog", the tagline, and
"Local synthetic handoff. Live tools stay off." 1200×630. Illustrative
until exported.

README header: the same peg as inline SVG, then the four-line opening
from the naming note.

Docs: maple page, ink type, a left rail of short links, code blocks on
paper with a brass left border. Do not theme docs as a second brand.

Dashboard: not in this direction. The UX audit says a dashboard would
draw capabilities that are not built. The application view is the
terminal card and a single run record, pretty-printed, with `usage`
shown as unknown.

States: hover darkens brass by mixing 8% ink. Focus is a 3px pine
outline, offset 2px. Error is clay text plus the word "Failed", never
color alone. Empty runs: "No saved runs in this state directory."
Loading is not a spinner on a CLI; the page has no live status. If a
later page waits on a local command, say "Checking PATH…" in text.

## Fit

Strengths: the name and the picture are the same object. Approachable
without looking like a finance app or a game HUD. Easy to keep honest.

Weaknesses: "bench dog" is jargon until the first sentence. A cute peg
can drift into mascot territory if it grows a face. Do not give it eyes.

Complexity: medium. One SVG, system fonts, no framework.

Differentiation: warm material and a single pin. Not a dark glass
dashboard, not an acid terminal, not an iridescent orb.
