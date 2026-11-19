# Contributing to TriadMux

Use Python 3.12 or later. For an isolated local checkout, run these commands
from the repository root.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip check
triadmux --version
```

Use synthetic inputs and fake provider executables in automated tests.
Record platform, provider CLI version, and evidence for any manual integration test.

## Development lifecycle

1. Open an issue or select a [roadmap](ROADMAP.md) item. Record the user-visible
   behavior, acceptance criteria, and any change to process, storage, or provider
   permissions.
2. Branch from current `main` and keep each pull request focused. Use descriptive
   commits. Include a regression test for behavior changes and update usage
   documentation and the changelog when users are affected.
3. Open a pull request with the issue, validation performed, and any integration
   gaps. CI tests the installed package. Changes to release, credential, or process
   handling need a maintainer review.
4. After CI passes and review conversations are resolved, squash merge into
   `main`. Keep the default branch available for release candidates.
5. Triage regressions against the affected version. Revert a faulty change
   through a pull request and publish a new patch version. Publish advisories
   for security fixes through the private process in [SECURITY.md](SECURITY.md).

## Repository administration

Use GitHub Free with standard hosted runners. After the first CI run completes,
require pull requests and the `CI required` job on `main`. Require conversation
resolution and linear history, disable force pushes and deletions, and enable
squash merges. Require an approving review when a second maintainer is available.
Enable private vulnerability reporting in repository security settings.
Protect the `v*` tag namespace against updates and deletion and limit release tag
creation to maintainers where repository permissions allow.

[GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage) ·
[Branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) ·
[Private vulnerability reporting settings](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)

## Releasing

Merge a pull request that updates `[project].version` in `pyproject.toml` and
records the changes in the changelog. Wait for green CI on the target commit.
Create and push a matching annotated tag from `main`. Use `v0.0.0` for the
bootstrap milestone, `v0.1.0a1` for the first alpha, `v0.1.0b1` for beta,
`v0.1.0rc1` for a release candidate, and `v0.1.0` for the first regular release.

```sh
git switch main
git pull --ff-only
git tag -a v0.1.0a1 -m 'TriadMux 0.1.0a1'
git push origin refs/tags/v0.1.0a1
```

The workflow validates the version and commit, runs CI, and publishes the
wheel, source distribution, and SHA-256 checksum file on GitHub Releases.
Bootstrap, alpha, beta, and release candidate tags publish as prereleases.
Verify the release notes, assets, and checksums after publish. If the workflow
fails before publication, inspect the failure and rerun the workflow for a
transient error. For source defects, fix the issue on `main` and use a new tag
for the corrected version.
