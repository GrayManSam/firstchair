"""The opt-in claude-swap bridge (firstchair/cswap.py), against a synthetic cswap.

No real cswap, account or credential is used. A fake ``cswap`` script on
PATH answers ``--version`` and ``list --json`` with the shape claude-swap
1.2.0 documents in docs/json-output.md. For ``run N -- ARGS`` it records the
call and starts the fake ``claude`` from test_live.py with ARGS, the way
the real ``cswap run`` hands over to Claude Code.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from firstchair import cswap
from firstchair.accounts import account_environment, list_profiles
from firstchair.cli import main
from firstchair.provider import ProviderError
from firstchair.quota import read_quota
from tests.test_live import FAKE_PROVIDER, PLAN, RESULT, REVIEW, TASK

# One account row per slot, as `cswap list --json` prints them. E-mails are
# invented and must never reach Firstchair output.
ROWS = [
    {"number": 1, "email": "one@example.invalid", "active": False, "usageStatus": "ok",
     "usageAgeSeconds": 30,
     "usage": {"fiveHour": {"pct": 12.0, "resetsAt": "2030-01-01T05:00:00+00:00"},
               "sevenDay": {"pct": 40.4, "resetsAt": "2030-01-05T00:00:00+00:00"}}},
    {"number": 2, "email": "two@example.invalid", "active": True, "usageStatus": "ok",
     "usageAgeSeconds": 0,
     "usage": {"sevenDay": {"pct": 83.0, "resetsAt": "2030-01-03T00:00:00Z"}}},
    {"number": 3, "email": "three@example.invalid", "active": False,
     "usageStatus": "unavailable", "usage": None,
     "lastGoodUsage": {"sevenDay": {"pct": 5.0}}},
]

FAKE_CSWAP = r"""
import json
import os
import sys
from pathlib import Path

fixture = Path(os.environ["FIRSTCHAIR_TEST_FIXTURE"])
args = sys.argv[1:]
behavior = os.environ.get("FIRSTCHAIR_TEST_CSWAP", "valid")

if args == ["--version"]:
    print("cswap " + os.environ.get("FIRSTCHAIR_TEST_CSWAP_VERSION", "1.2.0"))
    sys.exit(0)

if args == ["list", "--json"]:
    if behavior == "fail":
        sys.exit(1)
    if behavior == "malformed":
        print("{not json")
        sys.exit(0)
    schema = 2 if behavior == "future-schema" else 1
    print(json.dumps({"schemaVersion": schema, "activeAccountNumber": 2, "accounts": ROWS}))
    sys.exit(0)

if args[:1] == ["run"] and "--" in args:
    split = args.index("--")
    slot = args[1]
    with (fixture / "cswap_calls.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "slot": slot,
            "options": args[2:split],
            "inherited_config_dir": "CLAUDE_CONFIG_DIR" in os.environ,
        }) + "\n")
    # Like the real `cswap run`: point Claude Code at the slot's profile.
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(fixture / f"slot-{slot}"))
    claude = str(fixture / "claude")
    os.execve(claude, [claude, *args[split + 1:]], env)

sys.exit(2)
"""


def _script(path: Path, body: str) -> None:
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(0o700)


@unittest.skipUnless(os.name == "posix", "requires executable Python scripts with POSIX shebangs")
class CswapBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.state = self.fixture / "runs"
        constants = f"PLAN = {PLAN!r}\nREVIEW = {REVIEW!r}\nRESULT = {RESULT!r}\n"
        _script(self.fixture / "claude", constants + FAKE_PROVIDER)
        _script(self.fixture / "cswap", f"ROWS = {ROWS!r}\n" + FAKE_CSWAP)
        self.enterContext(patch.dict(os.environ, {
            "PATH": os.pathsep.join(filter(None, (str(self.fixture), os.environ.get("PATH")))),
            "HOME": str(self.fixture / "home"),
            "XDG_STATE_HOME": str(self.fixture / "state"),
            "CLAUDE_CONFIG_DIR": str(self.fixture / "claude-home"),
            "FIRSTCHAIR_TEST_FIXTURE": str(self.fixture),
            "FIRSTCHAIR_TEST_BEHAVIOR": "success",
            "FIRSTCHAIR_CSWAP": "1",
        }))

    def cswap_calls(self):
        path = self.fixture / "cswap_calls.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def cli(self, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["--state-dir", str(self.state), "--session", "cswap-session", *args])
        self.assertEqual(code, expected, stderr.getvalue() or stdout.getvalue())
        return stdout.getvalue(), stderr.getvalue()

    # -- opt-in ----------------------------------------------------------------

    def test_off_without_the_opt_in(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_CSWAP": ""}):
            self.assertFalse(cswap.is_cswap_profile("claude", "cswap-1"))
            self.assertEqual(cswap.list_profiles(), [])
            self.assertIsNone(cswap.read_quota("cswap-1"))
        self.assertEqual(self.cswap_calls(), [])

    def test_only_claude_and_well_formed_names(self):
        self.assertTrue(cswap.is_cswap_profile("claude", "cswap-12"))
        for provider, profile in (("codex", "cswap-1"), ("claude", "cswap-0"),
                                  ("claude", "cswap-x"), ("claude", "work"), ("claude", None)):
            self.assertFalse(cswap.is_cswap_profile(provider, profile), (provider, profile))

    # -- version gate ----------------------------------------------------------

    def test_version_gate(self):
        self.assertEqual(cswap.check_version("cswap 1.2.0"), "1.2.0")
        self.assertEqual(cswap.check_version("cswap 1.2.7"), "1.2.7")
        for output in ("cswap 1.1.0", "cswap 1.3.0", "cswap 1.0.0+local", "1.2.0", "cswap", ""):
            with self.assertRaises(ProviderError, msg=output):
                cswap.check_version(output)

    def test_unsupported_cswap_fails_closed(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_TEST_CSWAP_VERSION": "1.0.0"}):
            self.assertEqual(cswap.list_profiles(), [])
            self.assertIsNone(cswap.read_quota("cswap-1"))
            self.cli("run", "--provider", "claude", "--profile", "cswap-1", TASK, expected=1)
        self.assertEqual(self.cswap_calls(), [])  # no stage ever started

    def test_missing_cswap_is_unavailable(self):
        (self.fixture / "cswap").unlink()
        self.assertEqual(cswap.list_profiles(), [])
        with self.assertRaises(ProviderError):
            cswap.require_cswap()

    # -- listing and usage -----------------------------------------------------

    def test_slots_join_the_profile_list_without_emails(self):
        self.assertIn({"provider": "claude", "profile": "cswap-2"}, list_profiles())
        listed = json.dumps(cswap.list_profiles())
        self.assertEqual(json.loads(listed), [
            {"provider": "claude", "profile": f"cswap-{n}"} for n in (1, 2, 3)
        ])
        self.assertNotIn("example.invalid", listed)

    def test_valid_reading(self):
        quota = read_quota("claude", "cswap-1")
        self.assertEqual([(w.used_percent, w.minutes) for w in quota.windows],
                         [(12, 300), (40, 10080)])
        self.assertEqual(quota.windows[1].resets_at, 1893801600)
        self.assertIsNone(quota.allowed)
        self.assertAlmostEqual(quota.observed_at, time.time() - 30, delta=5)

    def test_missing_five_hour_window_is_fine(self):
        quota = read_quota("claude", "cswap-2")
        self.assertEqual([(w.used_percent, w.minutes) for w in quota.windows], [(83, 10080)])

    def test_stale_reading_is_no_reading(self):
        # usageStatus "unavailable": cswap itself would not act on it.
        self.assertIsNone(read_quota("claude", "cswap-3"))

    def test_unknown_slot_is_no_reading(self):
        self.assertIsNone(read_quota("claude", "cswap-9"))

    def test_bad_answers_are_no_reading(self):
        for behavior in ("fail", "malformed", "future-schema"):
            with patch.dict(os.environ, {"FIRSTCHAIR_TEST_CSWAP": behavior}):
                self.assertIsNone(read_quota("claude", "cswap-1"), behavior)
                self.assertEqual(cswap.list_profiles(), [], behavior)

    # -- launching -------------------------------------------------------------

    def test_environment_drops_config_home_and_credentials(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "invented"}):
            env = account_environment("claude", "cswap-2")
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        with self.assertRaises(ValueError):
            account_environment("claude", "cswap-2", create=True)

    def test_wrap_command(self):
        self.assertEqual(
            cswap.wrap_command(["/usr/bin/claude", "-p", "--output-format", "json"], "cswap-4", "/bin/cswap"),
            ["/bin/cswap", "run", "4", "--", "-p", "--output-format", "json"],
        )

    def test_run_goes_through_cswap_on_the_named_slot(self):
        stdout, _ = self.cli("run", "--provider", "claude", "--profile", "cswap-2", TASK)
        record = json.loads(stdout)
        self.assertEqual(record["status"], "completed")
        # The fake claude answers every stage with PLAN (see test_live.py).
        self.assertEqual(record["result"], PLAN)
        calls = self.cswap_calls()
        self.assertEqual(len(calls), 3)  # plan, review, synthesize
        self.assertEqual({call["slot"] for call in calls}, {"2"})
        self.assertTrue(all(call["options"] == [] for call in calls))
        # cswap, not Firstchair, chooses the config home.
        self.assertFalse(any(call["inherited_config_dir"] for call in calls))
        self.assertNotIn("example.invalid", stdout)


if __name__ == "__main__":
    unittest.main()
