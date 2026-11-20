# Design system

Three systems, one provisional name (Benchdog), none of them installed
as the product theme. The CLI has no theme today. These tokens are for
the concept prototype and for a later site if the name is approved.

The UX audit stands: do not build a TUI or a dashboard as the next
slice. This system styles a static explanation page and the words the
CLI already prints.

## Shared rules

- Body text 16px or larger, line-height at least 1.5.
- Status is a word: Ready, Missing, Failed, Interrupted, Unknown.
- Focus is a visible outline, at least 2px, never color alone.
- `prefers-reduced-motion: reduce` disables transitions.
- Target contrast: 4.5:1 for text, 3:1 for control boundaries (WCAG 2.2 AA 1.4.3 and 1.4.11).
- No webfont request on the prototype. System stacks only.
- No Holdfast assets, colors, or kelp mark.
- Sample metrics are labeled sample. Unknown stays unknown.

## Direction A — Day bench

| Token | Value |
| --- | --- |
| ground | #F4EFE6 |
| paper | #FFFBF5 |
| ink | #1C1915 |
| ink-soft | #4A433A |
| rule | #D9D0C3 |
| brass | #A56B1F |
| brass-ink | #1C1915 |
| pine | #1B5E3B |
| clay | #8E2F24 |
| chalk | #F7F1E6 |
| display | Iowan Old Style, Palatino Linotype, Palatino, Georgia, serif |
| ui | Segoe UI, system-ui, sans-serif |
| mono | ui-monospace, SFMono-Regular, Menlo, Consolas, monospace |
| radius | 12px card, 8px button |
| shadow | 0 16px 40px rgb(28 25 21 / 8%) |
| space | 8px base |

Mark: filled peg in a square hole.

## Direction B — Pin and hole

| Token | Value |
| --- | --- |
| ground | #121410 |
| panel | #1C1F1A |
| chalk | #F4F1EA |
| mist | #C4C0B6 |
| line | #34382F |
| cobalt | #8FB4FF |
| action | #D7E4FF |
| action-ink | #10203A |
| ok | #9DDBB4 |
| stop | #FFB4A8 |
| display and ui | system-ui, Segoe UI, sans-serif |
| mono | ui-monospace, Menlo, Consolas, monospace |
| radius | 4px |
| shadow | none |
| space | 8px base |

Mark: stroked square, filled circular head, rectangular stem.

## Direction C — Job ticket

| Token | Value |
| --- | --- |
| newsprint | #F3EDE3 |
| slip | #FFF9F1 |
| ink | #1A1A1A |
| graphite | #4E4944 |
| stamp | #9E2B1A |
| stamp-on | #FFF9F1 |
| ok | #1E5C38 |
| display | Rockwell, Liberation Serif, Times New Roman, serif |
| ui | system-ui, Segoe UI, sans-serif |
| mono | ui-monospace, Consolas, monospace |
| radius | 2px |
| shadow | none; hero uses a 4px offset border |
| space | 8px base |

Mark: the peg drawn as an upright stamp. Hero may rotate 6 degrees.
Favicon may not.

## Components

Used by the prototype. Names are the CSS classes.

| Component | Behavior |
| --- | --- |
| Mark | SVG peg. `aria-hidden` when the wordmark is next to it. |
| Wordmark | Text "benchdog" plus a visually hidden "provisional name". |
| Button | Real `<a>` or `<button>`. Min height 44px. Focus outline. |
| Command | `<pre>` with a copy button that copies text and sets `aria-live`. |
| Fact | A card or definition whose sentence is true of version 0.0.0. |
| Transcript | Sample terminal. Caption says it is a sample. |
| Stage list | Plan, review, synthesis, in that order. |
| Limit note | Unknown usage is text, not a zero. |

## What is out of the system

Leader pickers, worker boards, cost charts, token meters, auth forms,
and live status dots. Add them only after the UX staged path says the
underlying command exists.
