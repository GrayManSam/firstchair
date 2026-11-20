"""Regressions for the 0.1.0a1 live adapter review findings."""

import asyncio
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from time import monotonic
from unittest import mock

from firstchair import provider as provider_module
from firstchair.cli import main
from firstchair.live import find_executable, live_environment, total_usage
from firstchair.provider import run_bounded


def _usage(provenance: str, count: int | None) -> dict[str, object]:
    return {"provenance": provenance, "input_tokens": count, "output_tokens": count}


class LiveReviewFixTests(unittest.TestCase):
    def test_secret_looking_test_variables_do_not_reach_live_providers(self):
        settings = {"FIRSTCHAIR_TEST_API_KEY": "invented-secret-value", "FIRSTCHAIR_TEST_MODE": "ok"}
        with mock.patch.dict(os.environ, settings):
            environment = live_environment("codex")
        self.assertNotIn("FIRSTCHAIR_TEST_API_KEY", environment)
        self.assertEqual(environment["FIRSTCHAIR_TEST_MODE"], "ok")

    @unittest.skipUnless(os.name == "posix", "uses a shebang executable")
    def test_relative_path_entry_resolves_to_an_absolute_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = Path(directory, "tools")
            tools.mkdir()
            fake = tools / "codex"
            fake.write_text("#!/bin/sh\necho codex-cli 0.171.0\n", encoding="utf-8")
            fake.chmod(0o755)
            previous = os.getcwd()
            os.chdir(directory)
            try:
                executable = find_executable("codex", {"PATH": "tools"})
            finally:
                os.chdir(previous)
        self.assertTrue(os.path.isabs(executable))
        self.assertEqual(os.path.realpath(executable), os.path.realpath(fake))

    def test_failed_stage_without_counts_makes_total_partial(self):
        stages = {"plan": {"usage": _usage("measured", 5)}}
        self.assertEqual(total_usage(stages, attempted=2)["provenance"], "partial")
        self.assertEqual(total_usage(stages, attempted=1)["provenance"], "measured")
        self.assertEqual(total_usage({"plan": {"usage": _usage("unknown", None)}})["provenance"], "unknown")

    def test_dry_run_rejects_an_invalid_profile_name(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([
                "--state-dir", str(Path(directory, "state")), "run", "--provider", "codex",
                "--profile", "INVALID!", "--dry-run", "task",
            ])
        self.assertEqual(code, 1)
        self.assertIn("profile names", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")

    @unittest.skipUnless(os.name == "posix", "uses setsid to leave the process group")
    def test_timeout_does_not_wait_on_an_escaped_descendant_holding_stdout(self):
        pid_file = Path(tempfile.mkdtemp()) / "escaped.pid"
        script = textwrap.dedent(f"""
            import pathlib, subprocess, sys, time
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
            pathlib.Path({str(pid_file)!r}).write_text(str(child.pid))
            time.sleep(30)
        """)
        self.addCleanup(self._kill_escaped, pid_file)

        async def run() -> None:
            async with asyncio.timeout(0.5):
                await run_bounded(
                    (sys.executable, "-c", script), subprocess.DEVNULL, 1024,
                    cwd=tempfile.gettempdir(), env=dict(os.environ),
                )

        started = monotonic()
        with mock.patch.object(provider_module, "DRAIN_SECONDS", 0.5):
            with self.assertRaises(TimeoutError):
                asyncio.run(run())
        self.assertLess(monotonic() - started, 10)

    @staticmethod
    def _kill_escaped(pid_file: Path) -> None:
        try:
            os.kill(int(pid_file.read_text()), 9)
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    unittest.main()
