"""Exercise firstchair delegate with invented worker executables in a temporary repository."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from firstchair import delegation as delegate
from firstchair.cli import main

FAKE_CODEX = """\
import json, os, sys, time
from pathlib import Path
args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli " + os.environ.get("FAKE_CODEX_VERSION", "0.170.0"))
    sys.exit(0)
prompt = sys.stdin.read()
cwd = Path(args[args.index("--cd") + 1])
if "FAKE_WORKER_DUMP" in os.environ:
    Path(os.environ["FAKE_WORKER_DUMP"]).write_text(json.dumps({
        "env": sorted(os.environ), "prompt": prompt,
        "sees": {path: os.path.exists(path) for path in os.environ.get("FAKE_PROBE", "").split(os.pathsep) if path},
    }))
reply = Path(args[args.index("--output-last-message") + 1])
time.sleep(float(os.environ.get("FAKE_WORKER_SLEEP", "0")))
sys.stderr.write(os.environ.get("FAKE_WORKER_STDERR", ""))
if args[args.index("--sandbox") + 1] == "workspace-write":
    (cwd / "added.txt").write_text("invented change\\n")
reply.write_text("## Summary\\nfake codex saw " + str(len(prompt)) + " bytes\\n")
print('{"type":"thread.started","thread_id":"fixture"}')
for event in (
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"id": "fake", "type": "agent_message", "text": "Fixture"}},
    {"type": "turn.completed", "usage": {
        "input_tokens": 42, "output_tokens": 8, **json.loads(os.environ.get("FAKE_CODEX_CACHE", "{}")),
    }},
):
    print(json.dumps(event))
sys.exit(int(os.environ.get("FAKE_WORKER_EXIT", "0")))
"""

FAKE_GROK = """\
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
if args == ["--no-auto-update", "--version"]:
    print("grok 1.0.77 (invented) [stable]")
    sys.exit(0)
prompt = Path(args[args.index("--prompt-file") + 1]).read_text()
cwd = Path(args[args.index("--cwd") + 1])
if "--disallowed-tools" not in args:
    (cwd / "README.md").write_text("edited by invented grok\\n")
print(json.dumps({
    "text": "## Summary\\nfake grok mode " + ("read" if "--disallowed-tools" in args else "write"),
    "stopReason": "end_turn", **json.loads(os.environ.get("FAKE_GROK_EXTRA", "{}")),
}))
"""


class DelegateTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="firstchair-delegate-test-"))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.repo = self.temp / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("invented project\n")
        self._git("add", "README.md")
        self._git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "-q", "-m", "init")
        bin_dir = self.temp / "bin"
        bin_dir.mkdir()
        for name, body in (("codex", FAKE_CODEX), ("grok", FAKE_GROK)):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n{body}")
            path.chmod(0o755)
        environment = {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "FIRSTCHAIR_WORKTREE_ROOT": str(self.temp / "worktrees"),
            "FIRSTCHAIR_SESSION": "fixture-session",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
        patcher = mock.patch.dict(os.environ, environment)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _git(self, *args):
        return subprocess.run(
            ("git", "-C", str(self.repo), *args), check=True, capture_output=True, text=True
        ).stdout

    def _main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["delegate", "--repo", str(self.repo), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_dry_run_needs_no_task_and_creates_no_worktree_or_state(self):
        code, output, error = self._main("run", "auto", "--lead", "grok", "--dry-run")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)["provider"], "codex")
        self.assertFalse((self.repo / ".firstchair").exists())
        self.assertFalse((self.temp / "worktrees").exists())

    def test_timeout_must_be_finite_and_positive(self):
        for timeout in ("0", "nan", "inf"):
            with self.subTest(timeout=timeout):
                code, output, error = self._main("run", "codex", "--timeout", timeout, "--dry-run")
                self.assertEqual(code, 2)
                self.assertEqual(output, "")
                self.assertIn("finite positive", error)

    def test_auto_dispatch_uses_the_active_lead_and_records_the_worker(self):
        for lead, worker in (("claude", "grok"), ("codex", "grok"), ("grok", "codex")):
            with self.subTest(lead=lead):
                code, output, error = self._main(
                    "run", "auto", "--lead", lead, "--name", lead, "Inspect the README"
                )
                self.assertEqual(code, 0, error)
                summary = json.loads(output)
                self.assertEqual(summary["lead"], lead)
                self.assertEqual(summary["requested_provider"], "auto")
                self.assertEqual(summary["provider"], worker)
                expected_usage = (
                    {"provenance": "measured", "input_tokens": 42, "output_tokens": 8}
                    if worker == "codex"
                    else {"provenance": "unknown", "input_tokens": None, "output_tokens": None}
                )
                self.assertEqual(summary["usage"], expected_usage)

    def test_auto_falls_back_only_to_an_eligible_installed_worker(self):
        with mock.patch.object(delegate.shutil, "which", side_effect={"codex": "/fake/codex", "grok": None}.get):
            self.assertEqual(delegate.select_worker("auto", "claude", "read"), "codex")
            with self.assertRaisesRegex(delegate.DelegateError, "no eligible read worker"):
                delegate.select_worker("auto", "codex", "read")
        # Automatic write selection never reaches Grok, whichever seat leads.
        with mock.patch.object(delegate.shutil, "which", side_effect={"grok": "/fake/grok"}.get):
            for lead in ("claude", "codex"):
                with self.assertRaisesRegex(delegate.DelegateError, "no eligible write worker"):
                    delegate.select_worker("auto", lead, "write")
        for order in delegate.WORKER_ORDER.values():
            self.assertNotIn("grok", order["write"])

    def test_another_session_cannot_collect_or_finish_a_job(self):
        code, out, error = self._main("run", "codex", "Edit", "--mode", "write", "--name", "owned")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(out)["session"], "fixture-session")
        listed = json.loads(self._main("list")[1])
        self.assertEqual(listed["worktrees"][0]["session"], "fixture-session")
        worktree = self.temp / "worktrees" / "repo" / "owned"
        for session in ("other-session", None):
            with self.subTest(session=session):
                environment = {} if session is None else {"FIRSTCHAIR_SESSION": session}
                with mock.patch.dict(os.environ, environment):
                    if session is None:
                        del os.environ["FIRSTCHAIR_SESSION"]
                    for command in (("collect", "owned"), ("finish", "owned", "--delete-branch", "--force")):
                        code, out, error = self._main(*command)
                        self.assertEqual(code, 2, out)
                        self.assertIn("belongs to session fixture-session", error)
                self.assertTrue((worktree / "added.txt").exists())
                self.assertEqual(self._git("log", "--oneline", "delegate/owned").count("\n"), 1)
        # Naming the owner on the command line is the deliberate way across.
        with mock.patch.dict(os.environ, {"FIRSTCHAIR_SESSION": "other-session"}):
            code, _, error = self._main("--session", "fixture-session", "collect", "owned")
            self.assertEqual(code, 0, error)
            code, _, error = self._main("--session", "Not Valid", "finish", "owned")
            self.assertEqual(code, 2)
            self.assertIn("session must be", error)

    def test_a_run_without_a_session_makes_one_and_an_older_job_has_no_owner(self):
        with mock.patch.dict(os.environ):
            del os.environ["FIRSTCHAIR_SESSION"]
            code, out, error = self._main("run", "codex", "Edit", "--mode", "write", "--name", "fresh")
            self.assertEqual(code, 0, error)
            made = json.loads(out)["session"]
            self.assertRegex(made, r"^s-[0-9a-f]{12}$")
            code, _, error = self._main("finish", "fresh", "--force")
            self.assertEqual(code, 2)
            self.assertIn(f"pass --session {made}", error)
            # A job from before sessions existed has no session file.
            (self.repo / ".firstchair" / "delegations" / "fresh" / "session").unlink()
            code, _, error = self._main("finish", "fresh", "--force", "--delete-branch")
            self.assertEqual(code, 0, error)

    def test_rotation_runs_the_worker_under_the_account_with_the_most_room(self):
        from firstchair.accounts import account_environment
        from firstchair.quota import Quota, Window

        state = self.temp / "xdg"
        state.mkdir(mode=0o700)
        used = {None: 95, "spare": 20, "full": 100}

        def reader(provider, profile, **_):
            return Quota((Window(used[profile], 300, 2_000_000_000),), True, time.time())

        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(state)}), \
                mock.patch.object(delegate, "read_quota", side_effect=reader):
            for name in ("spare", "full"):
                account_environment("codex", name, create=True)
            code, out, error = self._main("run", "codex", "Review", "--rotate-accounts", "--dry-run")
            self.assertEqual(code, 0, error)
            planned = json.loads(out)
            self.assertEqual((planned["account_selection"], planned["account"]), ("rotated", "codex:spare"))
            self.assertEqual(
                {item["account"]: item["status"] for item in planned["account_candidates"]},
                {"codex": "over_budget", "codex:spare": "ready", "codex:full": "exhausted"},
            )
            code, out, error = self._main("run", "codex", "Review", "--name", "rotated", "--rotate-accounts")
            self.assertEqual(code, 0, error)
            summary = json.loads(out)
            self.assertEqual(summary["account"], "codex:spare")
            ledger = json.loads((state / "firstchair" / "account-ledger.json").read_text())
            # The finished work is counted against the account that ran it.
            self.assertEqual(len(ledger["accounts"]["codex:spare"]["events"]), 1)
            self.assertEqual(ledger["accounts"]["codex"]["events"], [])
            self.assertNotIn("Review", json.dumps(ledger))

            code, out, error = self._main(
                "run", "codex", "Review", "--rotate-accounts", "--profile", "spare", "--dry-run",
            )
            self.assertEqual(code, 2)
            self.assertIn("leave out --profile", error)
            used.update({None: 100, "spare": 100})
            # Every account full: nothing starts.
            (state / "firstchair" / "account-ledger.json").unlink()
            code, out, error = self._main("run", "codex", "Review", "--name", "none-left", "--rotate-accounts")
            self.assertEqual(code, 2, out)
            self.assertIn("every codex account is out of usage", error)
            self.assertFalse((self.repo / ".firstchair" / "delegations" / "none-left").exists())

    def test_unknown_codex_version_does_not_report_usage(self):
        with mock.patch.dict(os.environ, {"FAKE_CODEX_VERSION": "0.0.0"}):
            code, output, error = self._main("run", "codex", "Inspect the README")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)["usage"]["provenance"], "unknown")

    def test_auto_rejects_worker_specific_overrides(self):
        code, output, error = self._main("run", "auto", "--model", "synthetic", "Review")
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("require an explicit worker", error)

    def test_codex_read_task_uses_read_only_sandbox_and_removes_worktree(self):
        code, out, _ = self._main("run", "codex", "Inspect the README", "--name", "scout")
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(summary["status"], "completed")
        self.assertIn("fake codex saw", summary["reply"])
        self.assertIsNone(summary["worktree"])
        self.assertIsNone(summary["branch"])
        self.assertFalse((self.temp / "worktrees" / "repo" / "scout").exists())
        directory = Path(summary["logs"])
        self.assertEqual(sorted(path.name for path in directory.iterdir()), ["session", "summary.json"])
        self.assertEqual((directory / "session").read_text(), "fixture-session\n")
        saved = json.loads((directory / "summary.json").read_text())
        self.assertNotIn("reply", saved)
        self.assertNotIn("task", saved)

    def test_write_task_keeps_branch_then_collect_and_finish(self):
        code, out, _ = self._main("run", "codex", "Add a file", "--mode", "write", "--name", "w1")
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(summary["branch"], "delegate/w1")
        self.assertIn("?? added.txt", summary["changes"]["status"])
        self.assertFalse((self.repo / "added.txt").exists())

        code, out, err = self._main("finish", "w1")
        self.assertEqual(code, 2)
        self.assertIn("uncommitted changes", err)

        code, out, _ = self._main("collect", "w1")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["committed"])
        self.assertIn("added.txt", self._git("show", "--stat", "delegate/w1"))
        self.assertNotIn("added.txt", self._git("ls-files"))

        code, out, _ = self._main("finish", "w1", "--delete-branch", "--force")
        self.assertEqual(code, 0)
        self.assertEqual(self._git("branch", "--list", "delegate/*").strip(), "")

    def test_grok_read_and_write_commands(self):
        code, out, _ = self._main("run", "grok", "Review", "--name", "g-read")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["reply"], "## Summary\nfake grok mode read")

        for extra in ((), ("--dry-run",)):
            code, out, error = self._main("run", "grok", "Edit", "--mode", "write", "--name", "g-write", *extra)
            self.assertEqual(code, 2)
            self.assertEqual(out, "")
            self.assertIn("--allow-grok-write", error)
        self.assertEqual(self._git("branch", "--list", "delegate/*").strip(), "")
        self.assertFalse((self.repo / ".firstchair" / "delegations" / "g-write").exists())

        code, out, _ = self._main(
            "run", "grok", "Edit", "--mode", "write", "--name", "g-write", "--allow-grok-write",
        )
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertIn("M README.md", summary["changes"]["status"])
        self.assertEqual((self.repo / "README.md").read_text(), "invented project\n")
        listed = json.loads(self._main("list")[1])
        self.assertEqual([job["name"] for job in listed["worktrees"]], ["g-write"])
        self.assertTrue(listed["worktrees"][0]["dirty"])

    def test_failure_and_timeout_exit_codes(self):
        with mock.patch.dict(os.environ, {"FAKE_WORKER_EXIT": "3"}):
            code, out, _ = self._main("run", "codex", "fail", "--name", "bad")
        self.assertEqual((code, json.loads(out)["status"]), (1, "failed"))

        with mock.patch.dict(os.environ, {"FAKE_WORKER_SLEEP": "5"}):
            code, out, _ = self._main("run", "codex", "slow", "--name", "slow", "--timeout", "0.5")
        summary = json.loads(out)
        self.assertEqual((code, summary["status"]), (124, "timeout"))
        self.assertLess(summary["elapsed_seconds"], 4)

    def test_rejects_bad_names_and_reused_names(self):
        code, _, err = self._main("run", "codex", "x", "--name", "../escape")
        self.assertEqual(code, 2)
        self.assertIn("name must be", err)
        self.assertEqual(self._main("run", "codex", "x", "--name", "dup")[0], 0)
        code, _, err = self._main("run", "codex", "x", "--name", "dup")
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_with_changes_carries_uncommitted_work(self):
        (self.repo / "README.md").write_text("lead edit\n")
        (self.repo / "notes").mkdir()
        (self.repo / "notes" / "new.md").write_text("untracked\n")
        code, out, _ = self._main(
            "run", "codex", "Edit", "--mode", "write", "--name", "carry", "--with-changes"
        )
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(summary["carried_changes"]), ["README.md", "notes/"])
        worktree = Path(summary["worktree"])
        self.assertEqual((worktree / "README.md").read_text(), "lead edit\n")
        self.assertEqual((worktree / "notes" / "new.md").read_text(), "untracked\n")
        self.assertIn("lead edit", (self.repo / "README.md").read_text())
        # Carried work is committed on the branch, so only the worker's file is pending.
        self.assertEqual(summary["changes"]["status"], "?? added.txt")
        self.assertEqual(self._git("log", "--format=%s", "-1", "delegate/carry").strip(),
                         "Carry lead's uncommitted changes into delegate carry")

    def test_carried_changes_do_not_trigger_read_warning(self):
        (self.repo / "README.md").write_text("lead edit\n")
        code, out, _ = self._main("run", "codex", "Look", "--name", "quiet", "--with-changes")
        self.assertEqual(code, 0)
        self.assertNotIn("warning", json.loads(out))

    @unittest.skipUnless(os.name == "posix", "requires symlinks")
    def test_untracked_symlink_is_copied_as_a_link(self):
        secret = self.temp / "outside.txt"
        secret.write_text("outside the checkout\n")
        (self.repo / "link.txt").symlink_to(secret)
        code, out, _ = self._main(
            "run", "codex", "Look", "--mode", "write", "--name", "link", "--with-changes"
        )
        self.assertEqual(code, 0)
        copied = Path(json.loads(out)["worktree"]) / "link.txt"
        self.assertTrue(copied.is_symlink())

    def test_refuses_foreign_worktree_under_root(self):
        root = self.temp / "worktrees" / "repo"
        root.mkdir(parents=True)
        self._git("worktree", "add", "-q", "-b", "feature", str(root / "review"), "HEAD")
        code, _, err = self._main("finish", "review", "--delete-branch", "--force")
        self.assertEqual(code, 2)
        self.assertIn("no delegate job record", err)
        self.assertIn("feature", self._git("branch", "--list", "feature"))

    def test_worker_that_ignores_large_prompt_is_reported_not_raised(self):
        quitter = self.temp / "bin" / "codex"
        quitter.write_text(f"#!{sys.executable}\nimport sys\nsys.exit(5)\n")
        code, out, _ = self._main("run", "codex", "x" * 1_000_000, "--name", "quit")
        self.assertEqual((code, json.loads(out)["status"]), (1, "failed"))

    def test_relative_worktree_root_is_resolved(self):
        with mock.patch.dict(os.environ, {"FIRSTCHAIR_WORKTREE_ROOT": "rel-root"}):
            previous = Path.cwd()
            os.chdir(self.temp)
            try:
                self.assertEqual(self._main("run", "codex", "w", "--mode", "write",
                                            "--name", "rel")[0], 0)
                listed = json.loads(self._main("list")[1])
            finally:
                os.chdir(previous)
        self.assertEqual([job["name"] for job in listed["worktrees"]], ["rel"])

    def test_command_flags(self):
        job = delegate.Job(
            provider="codex", mode="write", name="n", repo=Path("/r"), worktree=Path("/w"),
            log_dir=Path("/l"), timeout=1, model="m", effort="high",
        )
        argv, use_stdin = delegate.build_command(job, Path("/p"), Path("/o"))
        self.assertTrue(use_stdin)
        self.assertIn("workspace-write", argv)
        self.assertEqual(argv[-1], "-")
        self.assertIn('model_reasoning_effort="high"', argv)
        grok = delegate.Job(
            provider="grok", mode="read", name="n", repo=Path("/r"), worktree=Path("/w"),
            log_dir=Path("/l"), timeout=1,
        )
        argv, use_stdin = delegate.build_command(grok, Path("/p"), Path("/o"))
        self.assertFalse(use_stdin)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "workspace")
        self.assertIn("--disallowed-tools", argv)
        self.assertIn("--no-subagents", argv)

    def test_worker_gets_the_lead_environment_without_its_secrets(self):
        dump = self.temp / "dump.json"
        lead = {
            "FAKE_WORKER_DUMP": str(dump), "FIXTURE_PLAIN": "kept",
            "FIXTURE_API_KEY": "invented-secret-value", "FIXTURE_TOKEN": "invented-secret-value",
            "XAI_API_KEY": "invented-secret-value", "SSH_AUTH_SOCK": "/invented/agent.sock",
            "FIXTURE_MESSAGING_SOCKET": "/invented/lead.sock", "DATABASE_URL": "invented://u:p@h/d",
        }
        with mock.patch.dict(os.environ, lead):
            code, output, error = self._main("run", "codex", "--name", "env", "Inspect the README")
        self.assertEqual(code, 0, error)
        seen = set(json.loads(dump.read_text())["env"])
        self.assertLessEqual({"PATH", "FIXTURE_PLAIN", "GIT_AUTHOR_NAME"}, seen)
        self.assertFalse(seen & (set(lead) - {"FAKE_WORKER_DUMP", "FIXTURE_PLAIN"}))

    def test_prompt_names_the_project_and_no_firstchair_test_command(self):
        dump = self.temp / "dump.json"
        with mock.patch.dict(os.environ, {"FAKE_WORKER_DUMP": str(dump)}):
            code, _, error = self._main("run", "codex", "--mode", "write", "--name", "main", "Edit it")
            self.assertEqual(code, 0, error)
            prompt = json.loads(dump.read_text())["prompt"]
            self.assertIn("for the\nrepo repository", prompt)
            self.assertNotIn("Firstchair", prompt)
            self.assertNotIn("unittest", prompt)
            # A linked worktree of the project still reports the project's name.
            linked = self.temp / "feature-tree"
            self._git("worktree", "add", "-q", "-b", "feature", str(linked))
            self.assertEqual(delegate.project_name(linked), "repo")

    def test_version_reports_the_commit_it_was_built_from(self):
        import firstchair

        with mock.patch.object(firstchair, "build_commit", return_value="abc1234"):
            self.assertEqual(firstchair.describe_version(), f"{firstchair.__version__} (abc1234)")
        with mock.patch.object(firstchair, "build_commit", return_value=None):
            self.assertEqual(firstchair.describe_version(), firstchair.__version__)
        self._git("commit", "-q", "--allow-empty", "-m", "second")
        head = self._git("rev-parse", "--short", "HEAD").strip()
        self.assertEqual(firstchair.checkout_commit(self.repo), head)
        (self.repo / "README.md").write_text("changed\n")
        self.assertEqual(firstchair.checkout_commit(self.repo), f"{head}, modified")
        self.assertIsNone(firstchair.checkout_commit(self.temp))

    def _records(self):
        return {job["name"]: job for job in json.loads(self._main("list")[1])["jobs"]}

    def test_finish_clears_a_read_job_so_its_name_can_be_used_again(self):
        self.assertEqual(self._main("run", "codex", "x", "--name", "again")[0], 0)
        self.assertEqual(self._records()["again"]["status"], "completed")
        code, _, error = self._main("run", "codex", "x", "--name", "again")
        self.assertIn("delegate finish again", error)
        code, out, error = self._main("finish", "again")
        self.assertEqual((code, json.loads(out)["removed"]), (0, False), error)
        self.assertFalse((self.repo / ".firstchair" / "delegations" / "again").exists())
        self.assertEqual(self._main("run", "codex", "x", "--name", "again")[0], 0)
        code, _, error = self._main("finish", "never-ran")
        self.assertEqual(code, 2)
        self.assertIn("no delegate worktree", error)

    def test_stopped_job_leaves_a_record_and_a_start_that_fails_leaves_none(self):
        with mock.patch.object(delegate, "run_worker", side_effect=delegate.Terminated):
            code, _, error = self._main("run", "codex", "x", "--mode", "write", "--name", "stopped")
        self.assertEqual(code, 2)
        self.assertIn("SIGTERM", error)
        self.assertEqual(self._records()["stopped"]["status"], "terminated")
        code, _, error = self._main("finish", "stopped", "--delete-branch", "--force")
        self.assertEqual(code, 0, error)
        self.assertEqual(self._main("run", "codex", "x", "--name", "stopped")[0], 0)
        # The branch exists, so the worktree cannot be made and the name is not taken.
        self._git("branch", "delegate/taken")
        code, _, error = self._main("run", "codex", "x", "--mode", "write", "--name", "taken")
        self.assertEqual(code, 2)
        self.assertFalse((self.repo / ".firstchair" / "delegations" / "taken").exists())

    def test_running_job_is_listed_and_not_finished_without_force(self):
        seen = {}

        def worker(*_args, **_kwargs):
            seen["record"] = self._records()["live"]
            seen["finish"] = self._main("finish", "live")
            return 0, 1.0

        with mock.patch.object(delegate, "run_worker", side_effect=worker):
            code, out, error = self._main("run", "codex", "x", "--mode", "write", "--name", "live")
        self.assertEqual(code, 0, error)
        self.assertEqual(seen["record"]["status"], "running")
        self.assertIn("elapsed_seconds", seen["record"])
        self.assertEqual(seen["finish"][0], 2)
        self.assertIn("still running", seen["finish"][2])
        self.assertIn("without changing any file", json.loads(out)["warning"])
        # A record whose controller is gone reads as abandoned.
        saved = self.repo / ".firstchair" / "delegations" / "live" / "summary.json"
        saved.write_text(json.dumps({**json.loads(saved.read_text()), "status": "running", "pid": 2 ** 22 + 7}))
        self.assertEqual(self._records()["live"]["status"], "abandoned")

    def test_failed_worker_reports_the_end_of_its_stderr_and_output_file_is_private(self):
        target = self.temp / "summary.json"
        with mock.patch.dict(os.environ, {"FAKE_WORKER_EXIT": "3", "FAKE_WORKER_STDERR": "invented failure\n"}):
            code, out, _ = self._main("run", "codex", "x", "--name", "broken", "--output", str(target))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["stderr_tail"], "invented failure")
        self.assertEqual(json.loads(target.read_text()), json.loads(out))
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("stderr_tail", (self.repo / ".firstchair/delegations/broken/summary.json").read_text())
        code, _, error = self._main("run", "codex", "x", "--name", "nowhere", "--output", str(self.temp / "no" / "f"))
        self.assertEqual(code, 2)
        self.assertFalse((self.repo / ".firstchair" / "delegations" / "nowhere").exists())

    def test_job_from_a_linked_worktree_keeps_its_record_in_the_main_checkout(self):
        linked = self.temp / "feature-tree"
        self._git("worktree", "add", "-q", "-b", "feature", str(linked))
        (linked / "feature.txt").write_text("only on the feature branch\n")
        subprocess.run(("git", "-C", str(linked), "add", "feature.txt"), check=True)
        subprocess.run(("git", "-C", str(linked), "commit", "-q", "-m", "feature"), check=True)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["delegate", "--repo", str(linked), "run", "codex", "x", "--mode", "write", "--name", "side"])
        self.assertEqual(code, 0, err.getvalue())
        summary = json.loads(out.getvalue())
        self.assertEqual(Path(summary["logs"]), self.repo / ".firstchair" / "delegations" / "side")
        worktree = Path(summary["worktree"])
        self.assertEqual(worktree, self.temp / "worktrees" / "repo" / "side")
        self.assertTrue((worktree / "feature.txt").exists())
        self.assertFalse((linked / ".firstchair").exists())
        for checkout in (self.repo, linked):
            status = subprocess.run(
                ("git", "-C", str(checkout), "status", "--porcelain"), capture_output=True, text=True, check=True,
            ).stdout
            self.assertEqual(status, "")
        # Either checkout can list and finish it.
        self.assertIn("side", self._records())
        code, _, error = self._main("finish", "side", "--delete-branch", "--force")
        self.assertEqual(code, 0, error)

    def test_grok_usage_is_measured_and_cached_input_is_reported_beside_the_total(self):
        extra = {"usage": {
            "input_tokens": 100, "cache_read_input_tokens": 70, "cache_creation_input_tokens": 5,
            "output_tokens": 9,
        }}
        with mock.patch.dict(os.environ, {"FAKE_GROK_EXTRA": json.dumps(extra)}):
            code, out, error = self._main("run", "grok", "x", "--name", "g-usage")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(out)["usage"], {
            "provenance": "measured", "input_tokens": 100, "output_tokens": 9,
            "cached_input_tokens": 70, "total_input_tokens": 175,
        })
        with mock.patch.dict(os.environ, {"FAKE_CODEX_CACHE": json.dumps({"cached_input_tokens": 30})}):
            code, out, error = self._main("run", "codex", "x", "--name", "c-usage")
        self.assertEqual(json.loads(out)["usage"], {
            "provenance": "measured", "input_tokens": 42, "output_tokens": 8,
            "cached_input_tokens": 30, "total_input_tokens": 42,
        })
        saved = json.loads((self.repo / ".firstchair/delegations/c-usage/summary.json").read_text())
        self.assertEqual(saved["usage"]["cached_input_tokens"], 30)
        # A malformed count is not reported at all.
        with mock.patch.dict(os.environ, {"FAKE_GROK_EXTRA": json.dumps({"usage": {"input_tokens": -1, "output_tokens": 2}})}):
            code, out, error = self._main("run", "grok", "x", "--name", "g-bad")
        self.assertEqual(json.loads(out)["usage"]["provenance"], "unknown")

    def test_base_starts_the_worktree_from_another_commit(self):
        self._git("checkout", "-q", "-b", "feature")
        (self.repo / "feature.txt").write_text("only on the feature branch\n")
        self._git("add", "feature.txt")
        self._git("commit", "-q", "-m", "feature")
        self._git("checkout", "-q", "main")
        code, out, error = self._main("run", "codex", "x", "--mode", "write", "--name", "based", "--base", "feature")
        self.assertEqual(code, 0, error)
        summary = json.loads(out)
        self.assertTrue((Path(summary["worktree"]) / "feature.txt").exists())
        self.assertEqual(summary["base_commit"], self._git("rev-parse", "feature").strip())
        for arguments in (("--base", "no-such-ref"), ("--base", "feature", "--with-changes")):
            with self.subTest(arguments=arguments):
                code, _, error = self._main("run", "codex", "x", "--name", "refused", *arguments)
                self.assertEqual(code, 2)
                self.assertIn("--base", error)
                self.assertFalse((self.repo / ".firstchair" / "delegations" / "refused").exists())
        self.assertEqual(self._main("run", "codex", "--base", "no-such-ref", "--dry-run")[0], 2)

    def test_diff_and_apply_hand_over_a_write_jobs_edits_with_new_files(self):
        (self.repo / "lead.txt").write_text("lead work in progress\n")
        code, _, error = self._main("run", "codex", "x", "--mode", "write", "--name", "edit", "--with-changes")
        self.assertEqual(code, 0, error)
        code, patch, error = self._main("diff", "edit")
        self.assertEqual(code, 0, error)
        self.assertIn("added.txt", patch)
        self.assertNotIn("lead.txt", patch)
        target = self.temp / "feature-tree"
        self._git("worktree", "add", "-q", "-b", "feature", str(target))
        code, out, error = self._main("apply", "edit", "--to", str(target))
        self.assertEqual((code, json.loads(out)["files"]), (0, ["added.txt"]), error)
        staged = subprocess.run(
            ("git", "-C", str(target), "status", "--porcelain"), capture_output=True, text=True, check=True,
        ).stdout
        self.assertEqual(staged, "A  added.txt\n")
        code, _, error = self._main("apply", "edit", "--to", str(target))
        self.assertEqual(code, 2)
        self.assertIn("nothing was changed", error)
        # The patch is the same after the lead collects the job.
        self.assertEqual(self._main("collect", "edit")[0], 0)
        self.assertEqual(self._main("diff", "edit")[1], patch)
        with mock.patch.dict(os.environ, {"FIRSTCHAIR_SESSION": "other-session"}):
            self.assertEqual(self._main("apply", "edit")[0], 2)
        self.assertEqual(self._main("run", "codex", "x", "--name", "reader")[0], 0)
        self.assertEqual(self._main("diff", "reader")[0], 2)

    def test_confine_builds_a_sandbox_that_hides_the_checkout_and_secret_stores(self):
        home = self.temp / "home"
        for folder in (".ssh", ".codex", ".grok", "private"):
            (home / folder).mkdir(parents=True)
        (home / ".netrc").write_text("invented\n")
        worktree = self.temp / "worktrees" / "repo" / "n"
        worktree.mkdir(parents=True)
        job = delegate.Job(
            provider="codex", mode="read", name="n", repo=self.repo, worktree=worktree,
            log_dir=Path("/l"), timeout=1,
        )
        with mock.patch.object(delegate.Path, "home", return_value=home), \
                mock.patch.object(delegate.shutil, "which", return_value="/fake/bwrap"):
            argv = delegate.confinement(job, [str(home / "private"), str(self.temp)], {})
            with self.assertRaises(delegate.DelegateError):
                delegate.confinement(job, ["relative/path"], {})
        pairs = list(zip(argv, argv[1:]))
        for hidden in (self.repo, home / ".ssh", home / ".grok", home / "private", self.temp):
            self.assertIn(("--tmpfs", str(hidden.resolve())), pairs)
        self.assertIn(("/dev/null", str((home / ".netrc").resolve())), pairs)
        self.assertNotIn(("--tmpfs", str((home / ".codex").resolve())), pairs)
        # Hiding a directory above them still leaves the worktree, the CLI home and Git data.
        tail = argv[argv.index(str(self.temp.resolve())):]
        for kept in (worktree, home / ".codex", self.repo / ".git"):
            self.assertIn(str(kept.resolve()), tail)
        self.assertEqual(argv[-2:], ["--die-with-parent", "--"])
        with mock.patch.object(delegate.shutil, "which", side_effect=lambda name, **_: None if name == "bwrap" else "/x"):
            code, _, error = self._main("run", "codex", "x", "--name", "nobwrap", "--confine")
        self.assertEqual(code, 2)
        self.assertIn("bubblewrap", error)

    @unittest.skipUnless(
        shutil.which("bwrap") and subprocess.run(
            ("bwrap", "--dev-bind", "/", "/", "--tmpfs", "/mnt", "true"), capture_output=True,
        ).returncode == 0,
        "requires a working bubblewrap",
    )
    def test_confined_worker_runs_and_cannot_see_the_main_checkout_or_a_hidden_path(self):
        private = self.temp / "private"
        private.mkdir()
        (private / "statement.txt").write_text("invented\n")
        dump = self.temp / "worktrees" / "dump.json"
        dump.parent.mkdir(parents=True, exist_ok=True)
        probes = [str(self.repo / "README.md"), str(private / "statement.txt"), str(self.temp / "bin" / "codex")]
        with mock.patch.dict(os.environ, {"FAKE_WORKER_DUMP": str(dump), "FAKE_PROBE": os.pathsep.join(probes)}):
            code, out, error = self._main(
                "run", "codex", "x", "--mode", "write", "--name", "boxed", "--hide", str(private),
            )
        self.assertEqual(code, 0, error + out)
        summary = json.loads(out)
        self.assertTrue(summary["confined"])
        self.assertIn("added.txt", summary["changes"]["status"])
        self.assertEqual(list(json.loads(dump.read_text())["sees"].values()), [False, False, True])


if __name__ == "__main__":
    unittest.main()
