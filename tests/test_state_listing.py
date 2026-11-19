import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from triadmux.state_listing import list_runs


class StateListingTests(unittest.TestCase):
    def test_summaries_are_sorted_and_omit_private_record_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            first = "00000000-0000-4000-8000-000000000001"
            second = "00000000-0000-4000-8000-000000000002"
            legacy = {"run_id": first, "status": "completed", "stage": "synthesize"}
            current = {"run_id": second, "status": "running", "stage": "review"}
            self._write(
                state_dir, second, dict(
                    current, schema_version=1, task="private task",
                    usage={"provenance": "unknown"},
                ),
            )
            self._write(state_dir, first, dict(legacy, schema_version=1, result="private result"))
            command = [sys.executable, "-m", "triadmux", "--state-dir", directory]
            output = subprocess.check_output([*command, "runs"], text=True, timeout=5)
            self.assertEqual(json.loads(output), {"runs": [legacy, current]})

    def test_skips_invalid_and_unrelated_records(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            for index, fields in enumerate((
                {"stage": "private stage"},
                {"status": ["private status"]},
                {"schema_version": 2},
                {"run_id": "00000000-0000-4000-8000-000000000009"},
            )):
                run_id = f"00000000-0000-4000-8000-00000000000{index}"
                record = dict(schema_version=1, run_id=run_id, status="running", stage="plan")
                self._write(state_dir, run_id, dict(record, **fields))
            (state_dir / "00000000-0000-4000-8000-000000000004.json").write_bytes(bytes([255]))
            (state_dir / "00000000-0000-4000-8000-000000000005.json").write_text(
                '{"task":"private payload"', encoding="utf-8",
            )
            (state_dir / "00000000-0000-4000-8000-000000000006.json").mkdir()
            (state_dir / "00000000-0000-4000-8000-000000000007.lock").touch()
            (state_dir / ".atomic-write").touch()
            self._write(state_dir, "manual", record)
            self.assertEqual(list_runs(state_dir), [])

    @unittest.skipUnless(os.name == "posix", "requires POSIX symbolic links")
    def test_does_not_follow_symbolic_link_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_dir = root / "state"
            state_dir.mkdir()
            run_id = "00000000-0000-4000-8000-000000000001"
            outside = self._write(root, run_id, {
                "schema_version": 1, "run_id": run_id, "status": "running", "stage": "plan",
            })
            (state_dir / outside.name).symlink_to(outside)
            self.assertEqual(list_runs(state_dir), [])

    def test_runs_command_leaves_missing_state_directory_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory, "missing")
            command = [sys.executable, "-m", "triadmux", "--state-dir", str(state_dir)]
            output = subprocess.check_output([*command, "runs"], text=True, timeout=5)
            self.assertEqual(json.loads(output), {"runs": []})
            self.assertFalse(state_dir.exists())

    @staticmethod
    def _write(state_dir, run_id, record):
        path = state_dir / f"{run_id}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path
