import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from firstchair.accounts import account_environment, claude_failure, profile_home
from firstchair.cli import main


@unittest.skipUnless(hasattr(os, "getuid"), "POSIX account permissions")
class AccountTests(unittest.TestCase):
    def setUp(self):
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        self.state = Path(state.name)
        environment = patch.dict(os.environ, {"XDG_STATE_HOME": state.name})
        environment.start()
        self.addCleanup(environment.stop)

    def test_each_account_has_its_own_private_provider_home(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "invented"}):
            for provider, variable in (("codex", "CODEX_HOME"),
                                       ("claude", "CLAUDE_CONFIG_DIR"), ("grok", "GROK_HOME")):
                work = account_environment(provider, "work", create=True)
                personal = account_environment(provider, "personal", create=True)
                self.assertNotEqual(work[variable], personal[variable])
                self.assertNotIn("OPENAI_API_KEY", work)
                self.assertEqual(Path(work[variable]).stat().st_mode & 0o777, 0o700)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["auth", "list"]), 0)
        self.assertEqual(len(json.loads(output.getvalue())["profiles"]), 6)

    def test_device_auth_uses_native_commands_for_codex_and_grok(self):
        for provider in ("codex", "grok"):
            with (
                patch("firstchair.accounts.shutil.which", return_value="/fake/" + provider),
                patch("firstchair.accounts.sys.stdin.isatty", return_value=True),
                patch("firstchair.accounts.subprocess.run") as run,
            ):
                run.return_value.returncode = 0
                self.assertEqual(main(["auth", "login", provider, "work", "--device-auth"]), 0)
                self.assertEqual(run.call_args.args[0], (provider, "login", "--device-auth"))

    def test_claude_probe_returns_only_classification(self):
        payload = {"type": "result", "is_error": True, "api_error_status": 429,
                   "result": "invented private data"}
        result = subprocess.CompletedProcess([], 1, stdout=json.dumps(payload))
        output = io.StringIO()
        with (
            patch("firstchair.accounts.shutil.which", return_value="/fake/claude"),
            patch("firstchair.accounts.subprocess.run", return_value=result),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(main(["auth", "check", "claude", "--probe"]), 1)
        self.assertEqual(json.loads(output.getvalue()), {"provider": "claude", "status": "rate_limited"})

    def test_profiles_reject_traversal_symlinks_and_shared_permissions(self):
        with self.assertRaisesRegex(ValueError, "profile names"):
            profile_home("codex", "../elsewhere", create=True)
        home = profile_home("codex", "work", create=True)
        home.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "private"):
            profile_home("codex", "work")
        (home.parent / "personal").symlink_to(home, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            profile_home("codex", "personal")

    def test_storage_rejects_git_checkouts(self):
        (self.state / ".git").mkdir()
        (self.state / ".git/HEAD").write_text("ref: refs/heads/main\n")
        with self.assertRaisesRegex(ValueError, "outside Git"):
            profile_home("codex", "work", create=True)


class ClaudeFailureTests(unittest.TestCase):
    def test_structured_rate_limit_and_authorization(self):
        for status, reason in ((429, "rate_limited"), (401, "authorization_failed")):
            payload = {"type": "result", "is_error": True, "api_error_status": status}
            self.assertEqual(claude_failure(json.dumps(payload)), reason)
        self.assertEqual(claude_failure("429 in unstructured output"), "provider_exit")
