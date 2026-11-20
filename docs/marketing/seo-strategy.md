# SEO strategy

No search volumes, difficulty scores, or ranks are stated here. None
were measured. The phrases below are language that appeared on pages
opened on 2026-11-19, or questions a reader of this repository can
already ask. That is intent evidence, not demand.

## Questions the page should answer

- What does this CLI do on a clean machine with no API keys?
- Does it launch Codex, Claude Code, or Grok?
- Where are run records stored, and are secrets written down?
- How is this different from a multi-agent terminal that already runs those tools?
- What is still on the roadmap?

## Language seen on adjacent pages

Retrieved 2026-11-19.

| Phrase on the page | Page | Use it? |
| --- | --- | --- |
| "multi-agent coding terminal" for Claude Code and Codex | https://skiff.solutionscay.com/ | Only to contrast. We do not ship that. |
| LLM routing across providers | https://github.com/NVIDIA-NeMo/Switchyard | Not our feature. Do not bid on "router" as if we are one. |
| "guardrails and a guided path for coding agents" | https://npm.io/package/fairlead | Adjacent. Our shipped guardrail is limits, redaction, and disabled live adapters. |
| Coding-agent workflow from a GitHub issue to a pull request | https://pypi.org/project/keel-workflow/ | Not shipped. Do not target "merge the PR" queries. |
| Local-first orchestration for AI coding CLIs | This repo's `pyproject.toml` description | Yes. This is our sentence. |

## Clusters to write toward

Each cluster is a page we can support with the repository. No cluster
asks the site to rank for a feature we do not have.

1. Local synthetic handoff. Queries in the reader's words: "run a coding agent workflow offline", "demo a plan review synthesis CLI". Proof: README quick start.
2. Discover CLIs without launching them. "check if claude code is installed from a script". Proof: `doctor`.
3. Limits and failure codes. "timeout a subprocess and keep a record". Proof: CLI flags and the error table in the UX audit.
4. Secret handling in local run records. "redact api keys in logs". Proof: `redaction.py` behavior described in the README.
5. Comparison, only where we opened the other project. "claude swap vs a multi-provider controller". Proof: `docs/upstream-review.md`. Say what we do not copy.

Do not build a cluster around quotas, cost, or "bypass rate limits."

## Technical

- One canonical host, chosen when a site exists. Until then the canonical URL is the GitHub repository: `https://github.com/GrayManSam/triadmux`.
- Titles and descriptions live in `site-map-and-page-copy.md`. They use TriadMux until the name is approved, and they mention Benchdog only as a provisional name on the brand index.
- `robots.txt` for a future static site: allow `/`, disallow nothing we do not have. Do not publish the private mirror.
- Sitemap: the routes in the site map, when those routes exist. They do not exist yet.
- Open Graph image: generate from direction A when the name is approved. The prototype is not that image.
- Structured data, when a site exists: `SoftwareSourceCode` with `codeRepository` pointing at the public GitHub URL, `license` MIT, `programmingLanguage` Python, `version` 0.0.0. `SoftwareApplication` `applicationCategory` DeveloperApplication, `operatingSystem` the ones CI actually runs. Do not mark `offers` or a price.
- Internal links: README to roadmap, to-do, upstream review, provider contracts, and this brand index.
- Performance: the prototype is one HTML file with inline CSS and SVG, no third-party requests. A production site should stay that way unless a maintainer approves an analytics tool. No analytics tag is included.

## Measurement, proposed

These are targets to adopt later, not current numbers. Baseline is
"not measured."

- Documentation to a local install: count `pip install` only if the maintainer later chooses privacy-respecting analytics. Until then, do not invent a rate.
- First run: a person can finish `triadmux run --demo` from the README without a secret.
- GitHub: stars and visitors, read from GitHub after 30 days, compared with the day the README opening changes. No target number until that baseline exists.
- Search: indexing of the README and the brand index, checked in Search Console if the maintainer adds the property. Not checked for this note.
- Onboarding drop-off: requires a site event we do not have. Leave it unmeasured.
