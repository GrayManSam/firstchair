# Launch plan

Do not execute this plan with the tree as it stands. There is no
release tag. Hosted CI failed on macOS on 2026-11-19. Live adapters are
disabled. A rename is not approved. Launching would advertise a product
the milestone does not meet.

## Gate before any public post

- The name is either approved or explicitly kept as TriadMux.
- `PYTHONPATH=src python -m unittest discover -s tests -v` passes locally.
- The GitHub CI matrix is green on the commit being announced, including macOS.
- The changelog has the version section filled and `## Unreleased` empty, if the post points at a tag.
- The post's feature list matches `docs/brand/research-and-audit.md`.
- The private mirror is not linked.

## What the first post can say

TriadMux 0.0.0 is a local Python CLI. `doctor` finds Codex, Claude Code,
and Grok and does not start them. `run --demo` and
`run --provider synthetic` complete a plan, review, and synthesis with
limits and a local record. Usage is unknown. Live adapters are off.
The license is MIT. The repository is
https://github.com/GrayManSam/triadmux.

## Channels, in order, after the gate

1. A GitHub Release only when `python -m triadmux.release_tag` passes and the tag is an annotated `v` tag on `main`. Prerelease if the version is 0.0.0 or an alpha, beta, or rc. This plan does not create that tag.
2. A discussion or release note on the same repository. Technical, short, with the quick start and the non-goals.
3. A Hacker News post only with a technical writeup of the controller: temporary workspace, env allowlist, redaction, fail-closed adapters. Title states the limitation ("a local synthetic handoff"). No "Show HN" that implies the three CLIs are live.
4. One relevant subreddit whose rules allow a source release, after reading those rules the week of the post. The draft belongs in the post, not in a cross-post spray.
5. A short demo video of `doctor` and `run --demo` on a clean checkout. No live account on screen. No terminal scroll of secrets.
6. Maintainer notes to people who already asked, individually. No purchased mentions, no fake quotes, no sockpuppets.

## Not in the launch

- A Product Hunt push that claims orchestration of three vendors.
- A domain buy.
- A rename announcement before approval.
- Badges for stars, downloads, or a green CI status we do not have.
