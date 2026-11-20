import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from firstchair.usage import Usage


class UsageTests(unittest.TestCase):
    def test_offline_runs_persist_unknown_token_usage(self):
        cases = (
            (["--demo"], "completed", 0),
            (["--provider", "synthetic"], "completed", 0),
            (["--provider", "synthetic", "--max-output-bytes", "1"], "failed", 1),
        )
        for options, expected_status, expected_exit in cases:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                command = [sys.executable, "-m", "firstchair", "--state-dir", directory]
                run = subprocess.run(
                    [*command, "run", *options, "Review the README"],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(run.returncode, expected_exit, run.stderr)
                record = json.loads(run.stdout)
                self.assertEqual(record["status"], expected_status)
                status = subprocess.run(
                    [*command, "status", record["run_id"]],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(status.returncode, expected_exit, status.stderr)
                self.assertEqual(
                    json.loads(status.stdout)["usage"],
                    {"provenance": "unknown", "input_tokens": None, "output_tokens": None},
                )

    def test_status_preserves_legacy_run_without_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            run_id = str(uuid4())
            legacy = {
                "schema_version": 1,
                "run_id": run_id,
                "status": "completed",
                "stage": "synthesize",
                "result": "Synthetic result",
            }
            path = Path(directory, f"{run_id}.json")
            encoded = json.dumps(legacy)
            path.write_text(encoded, encoding="utf-8")
            status = subprocess.run(
                [sys.executable, "-m", "firstchair", "--state-dir", directory, "status", run_id],
                capture_output=True, text=True, timeout=10, check=True,
            )
            self.assertEqual(json.loads(status.stdout), legacy)
            self.assertEqual(path.read_text(encoding="utf-8"), encoded)

    def test_serializes_usage(self):
        self.assertEqual(
            Usage().as_record(),
            {"provenance": "unknown", "input_tokens": None, "output_tokens": None},
        )
        self.assertEqual(
            Usage("measured", 4, 0).as_record(),
            {"provenance": "measured", "input_tokens": 4, "output_tokens": 0},
        )
