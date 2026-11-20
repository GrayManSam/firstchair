# Naming shortlist

Retrieved 2026-11-19. The current public name remains TriadMux. Nothing in
the package, the CLI, or the GitHub remotes was renamed. Scores are
judgments, not measurements. Availability below is a preliminary screen,
not legal clearance. "Domain not checked" means no registrar page was
opened.

The word tmux, the syllable mux, and the count "triad" do not appear in
the candidates. Vendor names and Holdfast do not appear either.

## Recommendation

Primary: **Benchdog**. Command: `benchdog`. Pronunciation: BENCH-dog.

A bench dog is the peg that sits in a hole on a workbench so the
workpiece does not slide. The person still does the work. The peg lines
it up and holds it. That matches a local controller: it discovers the
tools on the bench, runs a bounded handoff, and keeps a record. It does
not claim to be the carpenter.

Tagline: Hold the work. You still make the cut.

One sentence: Benchdog is a local command-line controller for coding
tools, and version 0.0.0 only runs a synthetic plan, review, and
synthesis on your machine.

Elevator: Coding tools already live on your PATH. Benchdog is the peg
that keeps one task from sliding between them. Today it can show whether
Codex, Claude Code, and Grok are installed, and it can run an offline
three-stage handoff with limits, a local record, and secret redaction.
It does not launch those tools yet. Live adapters are disabled until
their contracts are verified.

CLI line: `benchdog doctor` — show which coding tools are on PATH. None
are launched. Synthetic is the only enabled route.

README opening:

```text
# Benchdog

Benchdog is the provisional name for a local-first CLI that coordinates
coding tools. Version 0.0.0 runs a synthetic plan, review, and synthesis
on your machine. It can see Codex, Claude Code, and Grok on PATH and
does not start them.
```

Alternatives, in order: **Dovetail**, then **Bollard**. Both lose to
Benchdog on the collisions recorded below. Either can replace Benchdog
if the maintainer prefers a more familiar metaphor (Dovetail) or a
shorter, sterner word (Bollard).

## How the top five were scored

Each row is a judgment from 1 to 10, multiplied by the weight. The total
is the weighted sum, out of 10.

| Name | Comprehension 25% | Distinctiveness 20% | Recall 15% | Credibility 15% | Discoverability 15% | Extensibility 10% | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Benchdog | 7 → 1.75 | 8 → 1.60 | 8 → 1.20 | 7 → 1.05 | 7 → 1.05 | 8 → 0.80 | 7.45 |
| Dovetail | 9 → 2.25 | 6 → 1.20 | 8 → 1.20 | 8 → 1.20 | 3 → 0.45 | 7 → 0.70 | 7.00 |
| Bollard | 6 → 1.50 | 7 → 1.40 | 8 → 1.20 | 8 → 1.20 | 5 → 0.75 | 8 → 0.80 | 6.85 |
| Dowel | 8 → 2.00 | 6 → 1.20 | 8 → 1.20 | 7 → 1.05 | 4 → 0.60 | 8 → 0.80 | 6.85 |
| Ferrule | 5 → 1.25 | 7 → 1.40 | 6 → 0.90 | 7 → 1.05 | 3 → 0.45 | 8 → 0.80 | 5.85 |

Benchdog is easier to say than it is to define, so comprehension is not
a 10. One sentence fixes it, and the picture (a peg in a hole) sticks.
Discoverability is a 7, not a 10, because a benchmarking repo already
uses the word. That repo is not a coding-agent product.

Dovetail is the clearest metaphor: two pieces cut so they lock. It loses
because Dovetail the research company owns dovetail.com, and an old PyPI
project already used the name. Bollard is a dock post you make a line
fast to. It is a good second voice, and Rust developers already meet
`bollard` as a Docker client library.

## Screened names

These six were opened in search results on 2026-11-19. Domains were not
checked.

### Benchdog

- GitHub: [skupperproject/benchdog](https://github.com/skupperproject/benchdog) is a containerized client-server benchmark for comparing network setups. It is not a coding-agent CLI. No other coding product with this name turned up in the search.
- PyPI: no `benchdog` project page appeared in the search results. Not claimed as free.
- Domain: not checked.
- Trademark: no office record was opened.
- Search ambiguity: woodworking vocabulary, plus the Skupper benchmark.

### Dovetail

- Company: the GitHub organization [dovetail](https://github.com/dovetail) describes itself as storing and analyzing user research, and the search result says it controls dovetail.com. That organization also publishes `conduit`, a self-hosted agent platform, and `lasso`, usage reporting for Cursor and Claude.
- Older CLI: [TIBCOSoftware/dovetail-cli](https://github.com/TIBCOSoftware/dovetail-cli) generates smart contracts. [PyPI `Dovetail` 1.0beta3](https://pypi.org/project/Dovetail/) (2012) is a Python build tool.
- Domain: dovetail.com is identified with the research company in that GitHub result. Other TLDs were not checked.
- Trademark: not opened. The company use is enough to treat the word as crowded.

### Bollard

- GitHub: [fussybeaver/bollard](https://github.com/fussybeaver/bollard) is an asynchronous Rust client for the Docker and Podman API. The releases page shows a maintained library (v0.21.0 noted in search). It is not a user-facing coding orchestrator, and it is a name Rust and container developers already type.
- PyPI: no Python `bollard` project appeared in this search.
- Domain: not checked.

### Dowel

- PyPI: [`dowel` 0.0.4](https://pypi.org/project/dowel/) is a logger for machine-learning research from the Reinforcement Learning Working Group. `pip install dowel` is taken.
- npm: [`@dowel-ui/cli`](https://www.npmjs.com/package/@dowel-ui/cli) installs UI components and is documented as something a coding agent can drive through MCP.
- Domain: not checked.
- The metaphor (a pin that aligns two boards) is good. The install name is not.

### Ferrule

- A Go command `ferrule` is described as a local key vault and model router: [pkg.go.dev](https://pkg.go.dev/github.com/NakliTechie/ferrule/cmd/ferrule).
- [AmineDiro/ferrules](https://github.com/aminediro/ferrules) is a Rust document parser with a CLI (615 stars in the search result).
- [karol-broda/ferrule](https://github.com/karol-broda/ferrule) is a programming language whose command is `ferrule`.
- [lib.rs `ferrule`](https://lib.rs/crates/ferrule) is a Rust database query CLI.
- Domain: not checked.
- Pronunciation splits between FER-ul and fer-OOL. Too many existing commands.

### Rejected after the same search pass

These fit the metaphor and fail the screen. They are not finalists.

| Name | Why it lost | Source opened |
| --- | --- | --- |
| Skiff | A current product calls itself the multi-agent coding terminal for Claude Code, Codex, and others, and ships a `skiff` command. | https://skiff.solutionscay.com/ and https://github.com/solutionscay/skiff |
| Cairn | Several agent products already use it, including a terminal coding agent and a background coding agent. | https://github.com/cairn/cairn and https://github.com/cairn-dev/cairn |
| Keel | `keel-workflow` on PyPI turns coding agents into a GitHub issue-to-PR backbone and installs a `keel` command. | https://pypi.org/project/keel-workflow/ |
| Fairlead | An npm CLI describes itself as guardrails for coding agents. | https://npm.io/package/fairlead |
| Haft | A decision tool for Claude Code, Cursor, and Codex. The command is `haft`. | https://quint.codes/docs/ |
| Weft | A language for AI orchestration with a large GitHub presence, plus other `weft-*` packages. | https://github.com/WeaveMindAI/weft |
| Switchyard | NVIDIA NeMo Switchyard routes LLM calls across providers. | https://github.com/NVIDIA-NeMo/Switchyard |
| Tiller | Helm's historical `tiller`, plus more than one Claude/Codex companion that already uses the name. | https://github.com/hmSchuller/tiller-ai |
| Braid | `@braid-cloud/cli` installs prompt artifacts into coding tools. The command is `braid`. | https://www.npmjs.com/package/@braid-cloud/cli |
| Muster | `@musterhq/cli` is a governed agent harness. Another `muster` owns coding-agent sessions. | https://www.npmjs.com/package/@musterhq/cli |
| Halyard | Spinnaker's archived tool, plus a current CLI that syncs Claude, Cursor, and Codex sessions. | https://github.com/spinnaker/halyard and https://socket.dev/npm/package/@halyard/cli |
| Kedge | An archived Kubernetes tool and a current `@kedge/cli`. | https://github.com/kedgeproject/kedge |
| Waymark | A Python workflow engine, plus agent navigation markers. | https://github.com/piercefreeman/waymark |
| Lariat | PyPI project `lariat` is already a CLI. | https://pypi.org/project/lariat/ |
| Courier | PyPI `courier` is an email CLI, and Courier is a notifications company. | https://pypi.org/project/courier/ |
| Pitwall | An F1 timing TUI and a Claude Code cost plugin. | https://github.com/AidanFogarty/pitwall |
| Conduit | ConduitIO and several Python `conduit-*` projects, including agent-adjacent ones. | https://github.com/ConduitIO/conduit |

## Full candidate list

Availability is UNVERIFIED unless the row points at the screen above.

| Name | Say it | Territory | Why it was on the list | Likely command | Note |
| --- | --- | --- | --- | --- | --- |
| Benchdog | BENCH-dog | Metaphor | The peg that holds the work | `benchdog` | Primary. Screened. |
| Dovetail | DUV-tail | Metaphor | Two pieces cut to lock | `dovetail` | Alternative. Screened. |
| Bollard | BOL-erd | Metaphor | The post you make fast to | `bollard` | Alternative. Screened. |
| Dowel | DOW-ul | Metaphor | A pin that keeps two boards aligned | `dowel` | Screened. PyPI taken. |
| Ferrule | FER-ul | Metaphor | The band that joins a handle to a tool | `ferrule` | Screened. Several CLIs. |
| Cleat | KLEET | Metaphor | Where a line is secured | `cleat` | UNVERIFIED. Short. Easy to spell. |
| Halyard | HAL-yerd | Metaphor | The line that raises a sail | `halyard` | Screened. Crowded. |
| Fairlead | FAIR-leed | Metaphor | The fitting that keeps a line running true | `fairlead` | Screened. Same category. |
| Keel | KEEL | Metaphor | The spine of the hull | `keel` | Screened. Same category. |
| Muster | MUS-ter | Descriptive | Call the roll and see who is present | `muster` | Screened. Agent harness. |
| Waymark | WAY-mark | Metaphor | A mark that shows the path | `waymark` | Screened. Workflow engine. |
| Lariat | LA-ree-et | Metaphor | A loop that gathers | `lariat` | Screened. PyPI CLI. |
| Splice | SPLICE | Developer-native | Join two ends without dropping either | `splice` | UNVERIFIED. Also means gene and film edits. |
| Chock | CHOK | Metaphor | The wedge that stops a wheel | `chock` | UNVERIFIED. One syllable. Easy to misspell as "chalk". |
| Transom | TRAN-sum | Metaphor | The flat face at the stern | `transom` | UNVERIFIED. Distinct, less obvious. |
| Skiff | SKIFF | Metaphor | A small boat you handle yourself | `skiff` | Screened. Direct competitor. |
| Cairn | KAIRN | Metaphor | Stones that mark a trail | `cairn` | Screened. Direct competitors. |
| Relay | REE-lay | Descriptive | Pass one task along | `relay` | UNVERIFIED. Generic. Likely crowded. Not researched as a finalist. |
| Dispatch | dis-PATCH | Descriptive | Send the task to a tool | `dispatch` | UNVERIFIED. Generic operations word. |
| Notary | NO-tuh-ree | Descriptive | Record what happened | `notary` | UNVERIFIED. Sounds like a legal product. |
| Quorum | KWOR-um | Metaphor | Enough voices to proceed | `quorum` | UNVERIFIED. Implies a vote the product does not hold. |
| Handlist | HAND-list | Descriptive | The short list of a task and its record | `handlist` | UNVERIFIED. Plain, a little flat. |

## Tradeoff

Benchdog asks the reader to learn one workshop word. Dovetail does not,
and it collides with a known company. Bollard is stern and short, and
it collides with a well-known Rust crate. The recommendation accepts a
small teaching cost to avoid those two collisions.

No domain was registered. No PyPI or GitHub name was claimed. Do not
treat any row as "available."
