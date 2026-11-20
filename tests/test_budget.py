import asyncio
import functools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from firstchair.provider import ExecutionLimits, ProviderError, SyntheticProvider, invoke
from firstchair.workflow import record_path, run_workflow


class ExecutionBudgetTests(unittest.TestCase):
    def test_input_limit_counts_unicode_and_json_envelope_bytes(self):
        task = 'é"\n'
        request = b'{"schema_version": 1, "task": "\xc3\xa9\\"\\n"}'
        argv = (
            sys.executable, "-c",
            "import json, sys; "
            "print(json.dumps({'schema_version': 1, 'result': json.load(sys.stdin)['task']}))",
        )
        self.assertEqual(invoke(argv, task, ExecutionLimits(input_bytes=len(request))), task)
        with patch("asyncio.create_subprocess_exec") as spawn:
            with self.assertRaisesRegex(ProviderError, "^input_limit$"):
                invoke(argv, task, ExecutionLimits(input_bytes=len(request) - 1))
            spawn.assert_not_called()

    def test_later_stage_request_uses_same_input_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-m", "firstchair", "--state-dir", directory]
            failed = subprocess.run(
                [*command, "run", "--provider", "synthetic", "--max-input-bytes", "40", "x"],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(failed.returncode, 1, failed.stderr)
            record = json.loads(failed.stdout)
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["stage"], "review")
            self.assertEqual(record["error"], "input_limit")
            saved = subprocess.run(
                [*command, "status", record["run_id"]],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(saved.returncode, 1, saved.stderr)
            self.assertEqual(json.loads(saved.stdout), record)

    def test_invalid_input_limits(self):
        for input_bytes in (0, 65537, 1.5):
            with self.subTest(input_bytes=input_bytes):
                with self.assertRaisesRegex(ValueError, "provider input limit"):
                    ExecutionLimits(input_bytes=input_bytes)

    def test_expired_budget_rejects_next_stage_and_persists_failure(self):
        stages = ("plan", "review", "synthesize")
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("firstchair.provider.monotonic", side_effect=[100, 100, 100.1, 102]),
            patch("asyncio.create_subprocess_exec", wraps=asyncio.create_subprocess_exec) as spawn,
        ):
            provider = SyntheticProvider(ExecutionLimits(), total_timeout=2)
            state_dir = Path(directory)
            run = run_workflow(
                "sample task", state_dir, *(functools.partial(provider.run, stage) for stage in stages)
            )

            spawn.assert_awaited_once()
            self.assertEqual(run["status"], "failed")
            self.assertEqual(run["stage"], "review")
            self.assertEqual(run["error"], "budget_exhausted")
            self.assertEqual(json.loads(record_path(state_dir, run["run_id"]).read_text()), run)

    def test_shortest_timeout_decides_failure_code(self):
        argv = (sys.executable, "-c", "import time; time.sleep(30)")
        cases = (
            (ExecutionLimits(timeout=0.1), 20, "provider_timeout"),
            (ExecutionLimits(timeout=20), 0.1, "budget_exhausted"),
        )
        for limits, remaining, error_code in cases:
            with (
                self.subTest(error_code=error_code),
                patch("firstchair.provider.monotonic", return_value=100),
                self.assertRaisesRegex(ProviderError, f"^{error_code}$"),
            ):
                invoke(argv, "sample task", limits, deadline=100 + remaining)

    def test_invalid_total_timeout(self):
        for total_timeout in (0, -1, float("nan"), float("inf"), 181):
            with self.subTest(total_timeout=total_timeout):
                with self.assertRaisesRegex(ValueError, "total timeout"):
                    SyntheticProvider(ExecutionLimits(), total_timeout=total_timeout)
