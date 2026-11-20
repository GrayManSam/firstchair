# Brand decision

**Decided 2026-11-20: Firstchair.** The maintainer rejected round 1
(Benchdog, Dovetail, Bollard) and approved Firstchair from
[naming-round-2.md](naming-round-2.md). Local rename committed on branch
`rename-firstchair`; GitHub repos renamed to `GrayManSam/firstchair` and
`GrayManSam/firstchair-private` with redirects from the old slugs. No
domain, trademark or PyPI name has been registered. The three brand
directions below were drafted for Benchdog and need re-skinning for the
new name.

---

## Round 1 record (superseded)


Status: recommendation only. Waiting for approval of the name. No
package, command, README title, remote, or domain has been changed.

## Name

Use **Benchdog** as the provisional public name. Keep shipping and
documenting the binary as `triadmux` until approval.

Alternatives, if Benchdog fails a later check: **Dovetail**, then
**Bollard**. The scorecard and the collisions are in
[naming-shortlist.md](naming-shortlist.md). Scores are judgments. No
name was cleared for trademark, PyPI, or a domain.

Why this one: it does not lean on tmux, it does not name a vendor, and
the picture (a peg that holds the work) matches a local controller that
does not pretend to do the work itself. The closest public collision
found on 2026-11-19 is a network benchmark called benchdog, not a
coding-agent product. That is still a collision. It is a smaller one
than Skiff, Cairn, Keel, Fairlead, or Haft, which already sit in this
category.

## Direction

Prefer **A, Day bench**, for the first public page and the README
header, if the name is approved.

Day bench puts the peg on a warm, quiet page and keeps the product
example in a terminal card. That matches the UX audit: the shipped
surface is the CLI, and a dashboard is not justified. The warmth is
there so a newcomer can read the page. The claims stay inside version
0.0.0.

Direction B, Pin and hole, is the better system if the maintainer wants
the site to feel like an instrument and is willing to accept another
dark developer page. Direction C, Job ticket, is the better system if
the three stages should be the whole layout. C is the strongest
teaching tool and the easiest to over-decorate.

Do not blend them. A brass peg on a black glass card with a red stamp
is three brands at once.

## What must stay true in every direction

- Version 0.0.0 runs a synthetic plan, review, and synthesis.
- `doctor` can see Codex, Claude Code, and Grok on PATH and does not start them.
- Live adapters are disabled.
- Usage in a saved run is unknown.
- Records stay in a local state directory. Secrets of sufficient length are redacted before save.
- The project is independent of Claude Swap and is not affiliated with Anthropic, OpenAI, xAI, or that upstream maintainer.
- Hosted CI was not green on 2026-11-19. Do not claim a green matrix.

## Not decided

- The approved spelling.
- Whether the GitHub slug changes.
- Whether a domain is purchased.
- Whether direction A survives contact with a real README reader. That needs the maintainer, not another mock.
