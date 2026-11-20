# Naming, round 2

Retrieved 2026-11-20. The maintainer rejected round 1 (Benchdog,
Dovetail, Bollard; see [naming-shortlist.md](naming-shortlist.md)) and
asked for a fresh exploration. Round 1 used workshop and nautical
metaphors. This round tried theatre/production, signal routing,
railway signalling, and ensemble/leader territories.

Scores are judgments. Registry status is an HTTP status from the public
registry API on the retrieval date (404 = no project at that name, 200 =
taken). It is not a reservation. Domains and trademarks were not checked.

## Recommendation (provisional, awaiting approval)

Primary: **Firstchair**. Command: `firstchair`. Say it: FIRST-chair.

In an orchestra the first chair leads a section and still plays in it.
That is the product's model: you pick one tool to lead, the others take
parts, and you stay the conductor who approves the plan.

- Tagline: Pick a lead. Keep the score.
- One sentence: Firstchair is a local command-line controller that lets
  one coding tool lead and others review, with limits and a record you
  can read.
- CLI reads: `firstchair doctor`, `firstchair run --dry-run`,
  `firstchair runs list`.

Alternatives: **Stagecall**, then **Leadline**.

## Scorecard

| Name | Comprehension 25% | Distinctiveness 20% | Recall 15% | Credibility 15% | Discoverability 15% | Extensibility 10% | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firstchair | 7 → 1.75 | 9 → 1.80 | 8 → 1.20 | 6 → 0.90 | 8 → 1.20 | 7 → 0.70 | 7.55 |
| Stagecall | 6 → 1.50 | 8 → 1.60 | 7 → 1.05 | 7 → 1.05 | 8 → 1.20 | 8 → 0.80 | 7.20 |
| Leadline | 6 → 1.50 | 8 → 1.60 | 5 → 0.75 | 7 → 1.05 | 7 → 1.05 | 7 → 0.70 | 6.65 |

- Firstchair: credibility is the weak score; it can read as whimsical.
  Ski slang ("first chair" = first lift of the day) is a harmless second
  meaning.
- Stagecall: the stage manager calls each cue; the controller runs
  plan, review and synthesis stages. The phrase is less familiar than
  either word.
- Leadline: pronunciation splits between LEED-line and LED-line (a
  sounding line). That split costs recall.

## Screen of finalists

| Name | PyPI | npm | crates.io | GitHub (repos with name) | Web collisions |
| --- | --- | --- | --- | --- | --- |
| Firstchair | 404 | 404 | 404 | 39; largest 1★ | None found in software or AI |
| Stagecall | 404 | 404 | 404 | 5; largest 1★ | StageCaller, an iOS MIDI cue app ([App Store](https://apps.apple.com/us/app/stagecaller/id665909386)) |
| Leadline | 404 | 404 | 200 | 67; largest 5★ (cloudflare-apps/LeadLine) | None found in software or AI |

## Rejected this round

| Name | Why | Source |
| --- | --- | --- |
| Parley | Two coding-agent coordination tools already use it | https://www.nuget.org/packages/parley-cli, https://www.everydev.ai/tools/parley |
| Confer | `confer-cli`, coordination for fleets of AI agents | https://docs.rs/crate/confer-cli/0.4.8 |
| Convoke | `convoke-agents` npm, agent teams | https://socket.dev/npm/package/convoke-agents |
| Callboard | CallBoard, coordination dashboard for Claude Code and Codex | https://mcpmarket.com/zh/server/callboard |
| Patchbay | n0 Rust crate; `patchbai` multi-agent orchestrator on PyPI | https://pypi.org/project/patchbai/ |
| Trestle | IBM/OSCAL `compliance-trestle` ships a `trestle` CLI | https://github.com/oscal-compass/compliance-trestle |
| Callsheet | Casey Liss's well-known iOS app | https://caseyliss.com/callsheet |
| Crewcall | CrewCall AI call-centre software; too close to CrewAI | https://www.softwareadvice.com.au/software/775040/CrewCall-AI |
| Plait | Drawnix/Worktile plait (15k★); PyPI, npm, crates taken | https://github.com/worktile/plait |
| Roundhouse | chucknorris/roundhouse DB migrations (918★) | https://github.com/chucknorris/roundhouse |
| Signalbox, Runsheet, Cuesheet, Downbeat, Cuecard, Railyard, Tallyman | Taken on PyPI | pypi.org/pypi/&lt;name&gt;/json returned 200 |
| Stagehand | Browserbase Stagehand (26k★), AI browser automation | https://github.com/browserbase/stagehand |
| Interlock, Setlist, Shotcaller, Bandstand, Headset | Taken on npm and/or crowded on GitHub | registry checks above |

Category note: names in this space are crowded. Coral, Tutti, Chorus,
Bernstein, Relay and Skiff already coordinate Claude Code and Codex.
