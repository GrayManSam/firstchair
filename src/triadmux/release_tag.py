"""Validate the public Git tag used for a GitHub Release."""

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

_NUMBER = r"0|[1-9][0-9]*"
_TAG = re.compile(
    rf"^v((?:{_NUMBER})\.(?:{_NUMBER})\.(?:{_NUMBER})(?:(?:a|b|rc)(?:{_NUMBER}))?)$"
)
_PRERELEASE = re.compile(rf"(?:a|b|rc)(?:{_NUMBER})$")


@dataclass(frozen=True)
class ReleaseTag:
    tag: str
    version: str
    prerelease: bool
    notes: str


def parse_release_tag(tag: str) -> str:
    """Return the package version encoded by a public release tag."""
    match = _TAG.fullmatch(tag)
    if match is None:
        raise ValueError("tag must be vX.Y.Z with an optional aN, bN, or rcN suffix")
    return match.group(1)


def is_prerelease(version: str) -> bool:
    """Bootstrap, alpha, beta, and release-candidate versions publish as prereleases."""
    return version == "0.0.0" or _PRERELEASE.search(version) is not None


def _section(changelog: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}[ \t]*$", re.MULTILINE)
    matches = list(pattern.finditer(changelog))
    if len(matches) != 1:
        raise ValueError(f"changelog needs exactly one {heading} heading")
    rest = changelog[matches[0].end():]
    next_heading = re.search(r"^## ", rest, re.MULTILINE)
    body = rest[:next_heading.start()] if next_heading is not None else rest
    return body.strip()


def changelog_notes(changelog: str, version: str) -> str:
    """Return the public notes for one version and require an empty Unreleased section."""
    notes = _section(changelog, version)
    if not notes:
        raise ValueError("changelog version section is empty")
    if _section(changelog, "Unreleased"):
        raise ValueError("move Unreleased notes under the version heading before tagging")
    return notes + "\n"


def validate_release(tag: str, package_version: str, changelog: str) -> ReleaseTag:
    """Check a tag against the package version and changelog."""
    version = parse_release_tag(tag)
    if version != package_version:
        raise ValueError("tag does not match the package version")
    notes = changelog_notes(changelog, version)
    return ReleaseTag(tag, version, is_prerelease(version), notes)


def _read_package_version(path: Path) -> str:
    version = tomllib.loads(path.read_text(encoding="utf-8"))["project"]["version"]
    if not isinstance(version, str):
        raise ValueError("package version is missing")
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m triadmux.release_tag")
    parser.add_argument("tag")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    try:
        release = validate_release(
            args.tag,
            _read_package_version(args.pyproject),
            args.changelog.read_text(encoding="utf-8"),
        )
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr)
        return 1
    if args.notes is not None:
        args.notes.write_text(release.notes, encoding="utf-8")
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"prerelease={str(release.prerelease).lower()}\n")
    print(f"prerelease={str(release.prerelease).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
