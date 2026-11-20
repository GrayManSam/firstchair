import unittest
from unittest.mock import patch

from firstchair.inventory import provider_inventory, routing_explanation


class ProviderInventoryTests(unittest.TestCase):
    def test_routing_explains_both_offline_modes_without_path_discovery(self):
        with patch("firstchair.inventory.shutil.which") as find:
            for selected, alternate in (("demo", "synthetic"), ("synthetic", "demo")):
                with self.subTest(selected=selected):
                    self.assertEqual(
                        routing_explanation(selected),
                        {
                            selected: "selected",
                            alternate: "requires_explicit_selection",
                            "codex": "adapter_unavailable",
                            "claude": "adapter_unavailable",
                            "grok": "adapter_unavailable",
                        },
                    )
            with self.assertRaisesRegex(ValueError, "offline mode"):
                routing_explanation("codex")
        find.assert_not_called()

    def test_path_discovery_does_not_enable_live_providers(self):
        executables = {"codex": "fixture/codex"}
        with patch("firstchair.inventory.shutil.which", side_effect=executables.get):
            providers = provider_inventory()

        self.assertEqual(
            providers["codex"],
            {
                "executable": "fixture/codex",
                "auth": "unchecked",
                "discovery": "installed",
                "readiness": "unverified",
                "enabled": False,
            },
        )
        for name in ("claude", "grok"):
            with self.subTest(provider=name):
                self.assertEqual(
                    providers[name],
                    {
                        "executable": None,
                        "auth": "unchecked",
                        "discovery": "missing",
                        "readiness": "missing",
                        "enabled": False,
                    },
                )

    def test_bundled_provider_is_ready_without_an_external_executable(self):
        with patch("firstchair.inventory.shutil.which", return_value=None):
            providers = provider_inventory()

        self.assertEqual(
            providers["synthetic"],
            {
                "executable": None,
                "auth": "not_required",
                "discovery": "bundled",
                "readiness": "ready",
                "enabled": True,
            },
        )
