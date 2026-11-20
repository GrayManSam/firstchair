# Rename migration plan

Status: **executed 2026-11-20** with `{name}` = `firstchair`, `{Name}` =
Firstchair, `{slug}` = `firstchair`. Code and docs: commit "Rename TriadMux
to Firstchair" on branch `rename-firstchair` (not pushed, not merged).
GitHub: `GrayManSam/triadmux` → `GrayManSam/firstchair` (public, 301
redirect verified) and `GrayManSam/triadmux-private` →
`GrayManSam/firstchair-private` (private). Local remotes updated. No
domain registered and nothing published to PyPI.

Executed beyond this plan: `scripts/delegate.py` (untracked maintainer
tooling) uses `.firstchair/delegations/` and `FIRSTCHAIR_WORKTREE_ROOT`,
and still finds delegations and worktrees under the former names.

Retrieval date for the current tree: 2026-11-19. Local `main` matches
`origin/main` at the commit that recorded the public repository.

## Rules

- Preserve git history. Rename with `git mv` where a path changes.
- Keep the MIT license and the Claude Swap attribution in
  `docs/upstream-review.md`. The project is not Claude Swap.
- Ship one release that accepts the old command and the old state
  directory, prints a short deprecation notice, and writes new state.
- Do not delete old state. Copy or read it in place.
- A corrected name gets a new package version and a new tag. Do not reuse
  `v0.0.0`.
- The package version stays `0.0.0` until the alpha gates in `ROADMAP.md`
  are met. A rename is not those gates.

## Old-to-new mapping

The placeholder `{name}` is the approved lowercase CLI and import name.
`{Name}` is the display name. `{slug}` is the GitHub repository name.

| Surface | Current | After approval |
| --- | --- | --- |
| Display name | TriadMux | {Name} |
| Python distribution | triadmux | {name} |
| Import package | triadmux | {name} |
| CLI binary | triadmux | {name} |
| Module path | src/triadmux/ | src/{name}/ |
| Console script | triadmux = triadmux.cli:main | {name} = {name}.cli:main |
| State directory | .triadmux/ | .{name}/ |
| Temp workspace prefix | triadmux-workspace- | {name}-workspace- |
| Live-smoke temp prefix | triadmux-live- | {name}-live- |
| Test env prefix | TRIADMUX_TEST_ | {NAME}_TEST_ |
| Release tag message | TriadMux {version} | {Name} {version} |
| GitHub public repo | GrayManSam/triadmux | GrayManSam/{slug} only if a move is approved |
| GitHub private mirror | GrayManSam/triadmux-private | Decide separately. Do not make it public. |
| Local remote `origin` | https://github.com/GrayManSam/triadmux.git | Unchanged until the move is approved |
| Plugin id | triadmux | {name} |
| Skill | triadmux-check | {name}-check |

`{name}` must be a valid Python identifier: lowercase ASCII letters, no
hyphen, not a stdlib module. `{slug}` may match `{name}`.

## Compatibility window

1. Release N (the first release that introduces the name) installs `{name}`
   and keeps a `triadmux` console script that execs the same `main` and
   prints one stderr line: `{Name} replaces triadmux. The triadmux command
   will be removed in the next minor release.`
2. If `.triadmux/` exists and `.{name}/` does not, read `.triadmux/`. Do
   not move it automatically. Print the path that was read.
3. `TRIADMUX_TEST_` remains accepted beside the new prefix for one release
   so existing tests and local hooks keep working.
4. Release N+1 removes the `triadmux` script, stops reading `.triadmux/`,
   and drops the old env prefix. Document that in the changelog before
   tagging.
5. Docs keep a one-line alias: "Formerly TriadMux."

## GitHub

Do this only after the name is approved and the maintainer asks for the
move.

- Rename the public repository in GitHub settings so
  `github.com/GrayManSam/triadmux` redirects to the new slug. GitHub serves
  that redirect for git fetches and the website.
- Leave the private mirror private. Point the local `private` remote at
  the renamed mirror only if that repo is renamed too.
- Update `origin` with `git remote set-url`. Do not force-push.
- Re-run Actions on the default branch after the rename. Required checks
  are not green today: the 2026-11-19 macOS 3.12 job failed in
  `test_provider_child_receives_allowlisted_names_only`.
- Branch protection and the `v*` tag rules are still open work. Add them
  before the first public tag, whether or not the name changes.
- PyPI project `triadmux` has not been published by this repository. If a
  new name is uploaded later, yanking is not a rename. Publish once under
  the approved name.

## Docs and release notes

Update in the same commit as the code rename, still only after approval:

- README opening, command examples, state-dir paragraph.
- ROADMAP title, CONTRIBUTING release commands, SECURITY advisory text,
  CHANGELOG entry under a new version heading. Leave `## Unreleased` empty
  only when tagging.
- `docs/upstream-review.md` keeps the Claude Swap facts and adds the former
  name.
- `.github` issue templates, `ci.yml` install check, `release.yml` tag
  message and release title.
- `.grok` plugin name, agent name, and skill path.
- `.agents/skills/triadmux-check/`.

Search the tree for `triadmux`, `TriadMux`, and `triad-mux` and expect the
only remaining hits to be the deprecation notice, the changelog, and the
upstream attribution.

## User config

- Run records are JSON files under the state directory. Their schema does
  not store the product name. Old records stay valid.
- `limits.toml` keys are `[synthetic]`, not the product name. Leave them.
- No account credentials are stored by the controller. Do not migrate
  provider logins.

## Rollback

- The rename commit is a normal commit. Revert it to restore the old
  command.
- If a GitHub rename already happened, rename the repository back. The
  redirect follows the current name.
- If a wheel was uploaded, do not delete the file. Publish a later version
  that restores the `triadmux` script and say so in the release notes.
- State already written to `.{name}/` is left in place. The restored
  `triadmux` command must still accept `--state-dir`.

## Validation checklist

- [x] Approved spelling is written into this table in place of `{name}`.
- [x] `pip install .` (temp venv) creates the new command and the temporary
      `triadmux` alias.
- [x] `{name} --version` prints the unchanged version.
- [ ] `{name} doctor` and `triadmux doctor` both discover providers and do
      not launch them.
- [ ] `{name} run --demo` writes a record and redacts a long secret.
- [x] A fixture `.triadmux/` is read when `.{name}/` is absent.
- [x] `PYTHONPATH=src python -m unittest discover -s tests -v` passes (82 tests).
- [x] `git grep -i triadmux` matches only the alias, changelog, and
      attribution.
- [x] Public and private remotes still point at the intended repositories.
- [x] No tag is created unless the changelog gate passes.

## Files that carry the current name

Distribution and CLI: `pyproject.toml`, `src/triadmux/`, `LICENSE`.

Commands and tests: `src/triadmux/cli.py`, `src/triadmux/provider.py`,
`src/triadmux/release_tag.py`, `scripts/live-smoke.py`, `tests/`.

Docs: `README.md`, `ROADMAP.md`, `TODO.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `AGENTS.md`, `docs/grok-handoff.md`,
`docs/provider-contracts.md`, `docs/upstream-review.md`.

Automation and agents: `.github/workflows/ci.yml`,
`.github/workflows/release.yml`, `.github/ISSUE_TEMPLATE/`,
`.grok/config.toml`, `.grok/plugins/triadmux/`, `.grok/agents/triadmux.md`,
`.agents/skills/triadmux-check/SKILL.md`.
