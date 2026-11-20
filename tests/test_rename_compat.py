"""Compatibility with the former TriadMux name for one release."""

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from firstchair import cli
from firstchair.provider import _subprocess_environment


@contextlib.contextmanager
def _working_directory(path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class StateDirectoryTests(unittest.TestCase):
    def test_new_directory_is_default_when_neither_exists(self):
        with tempfile.TemporaryDirectory() as directory, _working_directory(directory):
            self.assertEqual(cli.default_state_dir(), Path(".firstchair"))

    def test_former_directory_is_read_when_new_one_is_absent(self):
        with tempfile.TemporaryDirectory() as directory, _working_directory(directory):
            Path(".triadmux").mkdir()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(cli.default_state_dir(), Path(".triadmux"))
            self.assertIn(".triadmux/", stderr.getvalue())
            self.assertTrue(Path(".triadmux").is_dir())

    def test_new_directory_wins_when_both_exist(self):
        with tempfile.TemporaryDirectory() as directory, _working_directory(directory):
            Path(".triadmux").mkdir()
            Path(".firstchair").mkdir()
            self.assertEqual(cli.default_state_dir(), Path(".firstchair"))

    def test_runs_lists_records_from_former_directory(self):
        with tempfile.TemporaryDirectory() as directory, _working_directory(directory):
            Path(".triadmux").mkdir()
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = cli.main(["runs"])
            self.assertEqual(status, 0)
            self.assertIn('"runs"', stdout.getvalue())
            self.assertFalse(Path(".firstchair").exists())


class LegacyCommandTests(unittest.TestCase):
    def test_legacy_command_prints_notice_and_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = cli.legacy_main(["--state-dir", directory, "runs"])
            self.assertEqual(status, 0)
            self.assertIn("Firstchair replaces triadmux", stderr.getvalue())
            self.assertIn('"runs"', stdout.getvalue())

    def test_legacy_command_keeps_its_program_name_in_help(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.legacy_main(["--help"])
        self.assertTrue(stdout.getvalue().startswith("usage: triadmux"))


class EnvironmentPrefixTests(unittest.TestCase):
    def test_former_and_new_test_prefixes_reach_children(self):
        values = {"FIRSTCHAIR_TEST_FLAG": "new", "TRIADMUX_TEST_FLAG": "old", "XAI_API_KEY": "x"}
        with mock.patch.dict(os.environ, values):
            environment = _subprocess_environment()
        self.assertEqual(environment["FIRSTCHAIR_TEST_FLAG"], "new")
        self.assertEqual(environment["TRIADMUX_TEST_FLAG"], "old")
        self.assertNotIn("XAI_API_KEY", environment)


if __name__ == "__main__":
    unittest.main()
