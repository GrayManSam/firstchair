import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ConfigTests(unittest.TestCase):
    def test_configures_limits_and_cli_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "limits.toml"
            config.write_text(
                "[synthetic]\ntimeout = 2.5\ntotal_timeout = 4\nmax_input_bytes = 1\n",
                encoding="utf-8",
            )
            command = [
                sys.executable, "-m", "triadmux", "--state-dir", str(root / "state"),
                "run", "--provider", "synthetic", "--config", str(config),
            ]
            plan = subprocess.check_output(
                [*command, "--dry-run", "--timeout", "3", "Review the README"],
                text=True, timeout=10,
            )
            self.assertEqual(json.loads(plan)["limits"], {
                "stage_timeout": 3,
                "stage_input_bytes": 1,
                "stage_output_bytes": 65536,
                "total_timeout": 4,
            })
            rejected = subprocess.run(
                [*command, "Review the README"], capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(rejected.returncode, 1)
            self.assertEqual(json.loads(rejected.stdout)["error"], "input_limit")

    def test_invalid_config_fails_before_creating_state(self):
        cases = (
            ("[synthetic]\nprovider = 'codex'", "unknown synthetic configuration key"),
            ("[synthetic]\nmax_input_bytes = true", "must be an integer"),
            ("[synthetic]\ntimeout = '2'", "must be a number"),
            ("[synthetic]\ntimeout = 0", "greater than 0"),
            ("synthetic = []", "one [synthetic] table"),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "limits.toml"
            state = root / "state"
            for content, error in cases:
                with self.subTest(content=content):
                    config.write_text(content, encoding="utf-8")
                    command = [
                        sys.executable, "-m", "triadmux", "--state-dir", str(state), "run",
                        "--provider", "synthetic", "--config", str(config), "Review the README",
                    ]
                    rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    self.assertEqual(rejected.returncode, 1)
                    self.assertIn(error, json.loads(rejected.stderr)["error"])
                    self.assertFalse(state.exists())
