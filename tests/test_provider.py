import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from firstchair.provider import ExecutionLimits, ProviderError, SyntheticProvider, invoke


class ProviderTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "requires POSIX signals")
    def test_sigint_during_launch_reaps_worker_and_persists_interrupt(self):
        # Hold the process handle until the controller has received SIGINT.
        script = """
import asyncio
import os
import signal
import sys
from unittest.mock import patch

from firstchair.cli import main

spawn = asyncio.create_subprocess_exec
workers = []

async def interrupt_on_launch(*args, **kwargs):
    worker = await spawn(sys.executable, "-c", "import time; time.sleep(30)", **kwargs)
    workers.append(worker)
    os.kill(os.getpid(), signal.SIGINT)
    await asyncio.sleep(0)
    return worker

with patch("asyncio.create_subprocess_exec", interrupt_on_launch):
    status = main(["--state-dir", sys.argv[1], "run", "--provider", "synthetic", "task"])

assert [worker.returncode for worker in workers] == [-signal.SIGKILL]
raise SystemExit(status)
"""
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run(
                [sys.executable, "-c", script, directory],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(run.returncode, 1, run.stderr)
            record = json.loads(run.stdout)
            self.assertEqual(record["status"], "interrupted")
            self.assertEqual(record["stage"], "plan")
            saved = subprocess.run(
                [sys.executable, "-m", "firstchair", "--state-dir", directory,
                 "status", record["run_id"]],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(saved.returncode, 1, saved.stderr)
            self.assertEqual(json.loads(saved.stdout), record)

    def test_synthetic_subprocess_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-m", "firstchair", "--state-dir", directory]
            run = subprocess.run(
                [*command, "run", "--provider", "synthetic", "Review the README"],
                capture_output=True, text=True, check=True, timeout=10,
            )
            record = json.loads(run.stdout)
            self.assertEqual(record["status"], "completed")
            self.assertIn("Review the README", record["result"])
            review = record["worker_review"]
            self.assertIn("Review the README", review["assignment"])
            self.assertIn(review["validation_step"], record["result"])
            saved = subprocess.check_output(
                [*command, "status", record["run_id"]], text=True, timeout=10
            )
            self.assertEqual(json.loads(saved), record)

    def test_synthetic_review_requires_structured_result(self):
        for malformed in (
            "plain text",
            {"assignment": "Review the README"},
            {"assignment": "Review the README", "validation_step": ""},
        ):
            response = json.dumps({"schema_version": 1, "result": malformed}).encode()
            with (
                self.subTest(result=malformed),
                patch("firstchair.provider._read_response", return_value=response),
                self.assertRaisesRegex(ProviderError, "^malformed_response$"),
            ):
                SyntheticProvider(ExecutionLimits()).run("review", "synthetic assignment")

    def test_output_limit_failure_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-m", "firstchair", "--state-dir", directory]
            run = subprocess.run(
                [*command, "run", "--provider", "synthetic", "--max-output-bytes", "1", "task"],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(run.returncode, 1)
            record = json.loads(run.stdout)
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["stage"], "plan")
            self.assertEqual(record["error"], "output_limit")
            saved = subprocess.run(
                [*command, "status", record["run_id"]],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(json.loads(saved.stdout), record)

    def test_invalid_limits(self):
        for timeout, output_bytes in [(0, 5), (float("nan"), 5), (61, 5), (1, 0)]:
            with self.subTest(timeout=timeout, output_bytes=output_bytes):
                with self.assertRaises(ValueError):
                    ExecutionLimits(timeout, output_bytes)

    def test_classified_subprocess_failures(self):
        cases = (
            ("print('not JSON')", "malformed_response"),
            ('print(\'{"schema_version":true,"result":"value"}\')', "malformed_response"),
            ("raise SystemExit(2)", "provider_exit"),
            ("import time; time.sleep(30)", "provider_timeout"),
            ("import os, time; os.close(1); time.sleep(30)", "provider_timeout"),
        )
        for script, code in cases:
            with self.subTest(code=code, script=script):
                timeout = 0.3 if code == "provider_timeout" else 5
                with self.assertRaisesRegex(ProviderError, f"^{code}$"):
                    invoke((sys.executable, "-c", script), "task", ExecutionLimits(timeout))

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_timeout_stops_child_after_group_leader_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory, "ready")
            late = Path(directory, "late")
            child = (
                "from pathlib import Path; import time; "
                f"Path({str(ready)!r}).touch(); time.sleep(1.2); Path({str(late)!r}).touch()"
            )
            leader = f"import subprocess, sys; subprocess.Popen([sys.executable, '-c', {child!r}])"
            with self.assertRaisesRegex(ProviderError, "^provider_timeout$"):
                invoke((sys.executable, "-c", leader), "task", ExecutionLimits(0.6))
            self.assertTrue(ready.exists())
            time.sleep(0.8)
            self.assertFalse(late.exists())
