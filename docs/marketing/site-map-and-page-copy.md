# Site map and page copy

The site is not published. This is the copy to use if a static site is
built later. The homepage draft is also the source for the prototype.
Commands are the ones that exist.

Canonical, until a domain is approved: `https://github.com/GrayManSam/triadmux`.

## Routes

| Route | Title | Meta description | H1 |
| --- | --- | --- | --- |
| `/` | TriadMux — local CLI for a synthetic coding handoff | Discover Codex, Claude Code, and Grok without launching them. Version 0.0.0 runs a local synthetic plan, review, and synthesis. | A local handoff you can run without an API key. |
| `/docs/getting-started` | Getting started with TriadMux | Install the 0.0.0 package, run doctor, and finish one synthetic demo. | Start with doctor, then one demo. |
| `/install` | Install TriadMux | Python 3.12 or newer. Editable install from the git checkout. | Install from a checkout. |
| `/supported-clis` | Supported CLIs | Doctor looks for Codex, Claude Code, and Grok. Live adapters are disabled. | What TriadMux can see, and what it will not start. |
| `/how-it-works` | How a TriadMux run works | Plan, review, and synthesis, with limits, a dry run, and a local record. | Three stages, then a record. |
| `/compare` | TriadMux and Claude Swap | What the upstream review decided. TriadMux copies no Claude Swap source. | An independent controller, not a fork. |
| `/faq` | TriadMux FAQ | Live tools, secrets, state directory, and what 0.0.0 does not do. | Questions about this version. |
| `/changelog` | TriadMux changelog | The changelog in the repository. | Changelog |
| `/contributing` | Contributing to TriadMux | Tests, tags, and what not to send. | Contributing |
| GitHub | the public repository | — | — |

## Homepage

H1: A local handoff you can run without an API key.

Lede: TriadMux 0.0.0 discovers Codex, Claude Code, and Grok on your PATH
and does not start them. It runs a synthetic plan, review, and synthesis
on the machine, stores the record locally, and redacts long secret-like
environment values before that write.

Primary action: copy the install block.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
triadmux doctor
triadmux run --demo "Review the project's build instructions"
```

Secondary action: read what works today.

Facts:

- Doctor reports readiness and launches nothing.
- The only run you can start is synthetic, or the in-process demo.
- Dry run shows the plan and writes no record.
- A saved run lists usage as unknown.
- Live adapters are disabled.
- The license is MIT. The project is not Claude Swap.

Footer line: Benchdog is a provisional rename, not the command. The
command is `triadmux`.

## Install page

H1: Install from a checkout.

Body: Python 3.12 or newer. There is no published wheel on PyPI under
this name as of 2026-11-19 (`https://pypi.org/pypi/triadmux/json` was
Not Found during the audit). Clone `https://github.com/GrayManSam/triadmux`
and install editable. Then run `triadmux doctor`.

## Supported CLIs

H1: What TriadMux can see, and what it will not start.

Body: `doctor` looks for `codex`, `claude`, and `grok`. Found means the
executable is on PATH. It does not mean the adapter is enabled. The
inventory marks those three disabled. The synthetic provider is enabled.
Authentication is not checked and not stored.

## How it works

H1: Three stages, then a record.

Body: A synthetic run moves through plan, review, and synthesis. You can
set a per-stage timeout, a shared timeout, and input and output byte
limits with `--provider synthetic`. `--dry-run` explains the selection
and does not start workers. Records default to `.triadmux/`, which is
gitignored. `triadmux runs` lists id, status, and stage. `triadmux
recover` marks an abandoned POSIX run interrupted. It does not restart
the work.

## Comparison

H1: An independent controller, not a fork.

Body: The upstream review pinned realiti4/claude-swap at
`ee79e705cf6e1ad3f70621b88b80983a99bb2001`. That package was 1.2.0b1,
MIT, copyright 2026 Onur Cetinkol. TriadMux incorporates none of its
source. Claude Swap moves among Claude profiles. TriadMux, today, runs
a synthetic handoff and leaves provider login to the provider. Do not
add rows for products we did not open.

## FAQ

- Does it call the model APIs? Not in 0.0.0. The demo and the synthetic provider are local.
- Where is the data? In the state directory you choose, default `.triadmux/` in the working directory.
- Can it switch Claude accounts? No. That is the kind of job Claude Swap does. This project does not do it.
- Is the macOS CI job passing? It failed on 2026-11-19. See the audit.

## Structured data notes

When the pages exist, each page sets a canonical link to itself on the
chosen host, and the home page includes the `SoftwareSourceCode` object
described in `seo-strategy.md`. Open Graph title equals the title. The
description equals the meta description. The image is generated later
from direction A and labeled with the version.
