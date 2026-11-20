import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from firstchair.release_tag import (
    changelog_notes,
    is_prerelease,
    parse_release_tag,
    validate_release,
)

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = """# Changelog

## Unreleased

## 0.1.0a1

- First alpha notes.

## 0.0.0

- Bootstrap notes.
"""


class ReleaseTagTests(unittest.TestCase):
    def test_roadmap_tags_match_package_versions(self):
        cases = {
            "v0.0.0": True,
            "v0.1.0a1": True,
            "v0.1.0a2": True,
            "v0.1.0b1": True,
            "v0.1.0rc1": True,
            "v0.1.0rc10": True,
            "v0.1.0": False,
            "v0.1.1": False,
            "v1.0.0": False,
            "v10.20.30": False,
        }
        for tag, prerelease in cases.items():
            with self.subTest(tag=tag):
                version = parse_release_tag(tag)
                self.assertEqual(version, tag[1:])
                self.assertEqual(is_prerelease(version), prerelease)

    def test_rejects_non_public_tag_names(self):
        for tag in (
            "0.1.0",
            "V0.1.0",
            "v0.1",
            "v0.1.0.0",
            "v01.2.3",
            "v0.1.0a",
            "v0.1.0a01",
            "v0.1.0alpha1",
            "v0.1.0-a1",
            "v0.1.0rc1a1",
            "v0.1.0.dev1",
            "v0.1.0+local",
            "refs/tags/v0.1.0",
        ):
            with self.subTest(tag=tag):
                with self.assertRaisesRegex(ValueError, "tag must be"):
                    parse_release_tag(tag)

    def test_release_notes_come_from_the_version_section(self):
        release = validate_release("v0.1.0a1", "0.1.0a1", CHANGELOG)
        self.assertTrue(release.prerelease)
        self.assertEqual(release.notes, "- First alpha notes.\n")
        notes = changelog_notes(
            "# Changelog\n\n## Unreleased\n\n## 0.1.0\n\n- Stable notes.\n",
            "0.1.0",
        )
        self.assertEqual(notes, "- Stable notes.\n")
        self.assertFalse(is_prerelease("0.1.0"))

    def test_rejects_version_mismatch_and_unreleased_notes(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_release("v0.1.0a1", "0.1.0a2", CHANGELOG)
        with self.assertRaisesRegex(ValueError, "Unreleased"):
            validate_release(
                "v0.1.0a1",
                "0.1.0a1",
                CHANGELOG.replace("## Unreleased\n", "## Unreleased\n\n- Still drafting.\n"),
            )
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_release(
                "v0.1.0a1",
                "0.1.0a1",
                "# Changelog\n\n## Unreleased\n\n## 0.1.0a1\n\n## 0.0.0\n\n- Old.\n",
            )

    def test_checkout_changelog_has_notes_for_its_package_version(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        notes = changelog_notes(changelog, version) if "## Unreleased\n\n## " in changelog else None
        if notes is None:
            # Drafted notes under Unreleased block tagging until they move to a version.
            with self.assertRaisesRegex(ValueError, "Unreleased"):
                validate_release(f"v{version}", version, changelog)
        else:
            self.assertEqual(validate_release(f"v{version}", version, changelog).notes, notes)

    def test_cli_writes_prerelease_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                '[project]\nversion = "0.1.0a1"\n', encoding="utf-8"
            )
            (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            notes = root / "notes.md"
            output = root / "github-output.txt"
            completed = subprocess.run(
                [
                    sys.executable, "-m", "firstchair.release_tag", "v0.1.0a1",
                    "--pyproject", root / "pyproject.toml",
                    "--changelog", root / "CHANGELOG.md",
                    "--notes", notes,
                    "--github-output", output,
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "prerelease=true")
            self.assertEqual(notes.read_text(encoding="utf-8"), "- First alpha notes.\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "prerelease=true\n")

    def test_release_workflow_uses_the_checker_and_annotated_tags(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("python -m firstchair.release_tag", workflow)
        self.assertIn('git cat-file -t "$GITHUB_REF_NAME"', workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertNotIn("--generate-notes", workflow)
        self.assertIn("refs/tags/", workflow)
