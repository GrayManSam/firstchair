import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from triadmux.workflow import record_path, run_workflow


class WorkflowTests(unittest.TestCase):
    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-m", "triadmux", "--state-dir", directory]
            output = subprocess.check_output(
                [*command, "run", "--demo", "Review the project README"], text=True
            )
            run = json.loads(output)
            self.assertEqual(run["status"], "completed")
            self.assertIn("repeatable validation", run["result"])
            saved = subprocess.check_output([*command, "status", run["run_id"]], text=True)
            self.assertEqual(json.loads(saved), run)

    def test_failed_review_stops_workflow_and_records_failure(self):
        def fail(_):
            raise RuntimeError("private provider diagnostic")

        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            record = run_workflow("task", state_dir, str, fail, self.fail)
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["stage"], "review")
            saved = record_path(state_dir, record["run_id"]).read_text()
            self.assertNotIn("private provider diagnostic", saved)

    def test_invalid_run_id(self):
        with self.assertRaises(ValueError):
            record_path(Path("."), "../outside")
