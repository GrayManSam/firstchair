import unittest

from firstchair.provider import ProviderError
from firstchair.versions import check_version, read_version


class VersionTests(unittest.TestCase):
    def test_reads_provider_version_formats(self):
        for provider, stdout, expected in (
            ("codex", "codex-cli 0.171.0\n", "0.171.0"),
            ("claude", "2.1.329 (Claude Code)\n", "2.1.329"),
            ("grok", "grok 1.0.77 (000000000000) [stable]\n", "1.0.77"),
        ):
            with self.subTest(provider=provider):
                self.assertEqual(read_version(provider, stdout), expected)
                self.assertEqual(check_version(provider, expected), "verified")

    def test_accepts_compatible_versions(self):
        for provider, version in (("codex", "0.179.0"), ("claude", "2.1.330"), ("grok", "1.0.78")):
            with self.subTest(provider=provider):
                self.assertEqual(check_version(provider, version), "compatible")

    def test_rejects_versions_outside_ranges_and_invalid_strings(self):
        for provider, version in (
            ("codex", "0.169.9"),
            ("codex", "0.180.0"),
            ("claude", "2.1.327"),
            ("claude", "2.2.0"),
            ("grok", "1.0.76"),
            ("grok", "1.1.0"),
            ("grok", "1.0.77-beta"),
            ("grok", "1.0.77+build"),
            ("grok", "1.0.77 extra"),
            ("grok", ""),
            ("unknown", "1.0.77"),
        ):
            with self.subTest(provider=provider, version=version):
                with self.assertRaisesRegex(ProviderError, "^unsupported_provider_version$"):
                    check_version(provider, version)

    def test_rejects_missing_ambiguous_and_malformed_version_output(self):
        for stdout in (
            "", "grok 1.0", "grok 1.0.77 2.0.0", "grok 1.0.77-beta",
            "grok 1.0.77.1", "grok -1.0.77",
        ):
            with self.subTest(stdout=stdout):
                with self.assertRaisesRegex(ProviderError, "^unsupported_provider_version$"):
                    read_version("grok", stdout)
