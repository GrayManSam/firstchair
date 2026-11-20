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

from firstchair.cli import main
from firstchair.live import build_command, live_environment


TASK = "Plan the sorting of sample cards."
PLAN = "Group the cards by color."
REVIEW = "Check the labels before sorting."
RESULT = "Check the labels, then group the cards by color."

FAKE_PROVIDER = r"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

provider = Path(sys.argv[0]).name
args = sys.argv[1:]
fixture = Path(os.environ["FIRSTCHAIR_TEST_FIXTURE"])
behavior = os.environ.get("FIRSTCHAIR_TEST_BEHAVIOR", "success")

def emit(event):
    print(json.dumps(event))

call = {"provider": provider, "args": args}
if "--version" not in args:
    call["stdin"] = sys.stdin.read()
    if "--prompt-file" in args:
        path = Path(args[args.index("--prompt-file") + 1])
        call["prompt_file"] = path.read_text(encoding="utf-8")
with (fixture / "calls.jsonl").open("a", encoding="utf-8") as log:
    print(json.dumps(call), file=log)

if "--version" in args:
    versions = {
        "codex": "codex-cli 0.171.0",
        "claude": "2.1.329 (Claude Code)",
        "grok": "grok 1.0.77 (000000000000) [stable]",
    }
    if provider == "codex" and behavior == "unsupported":
        versions["codex"] = "codex-cli 0.190.0"
    print(versions[provider])
    sys.exit(0)

if behavior == "timeout":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(8)"])
    (fixture / "grandchild.pid").write_text(str(child.pid), encoding="utf-8")
    time.sleep(8)
    sys.exit(0)

if provider == "codex":
    synthesizing = "Reviewer's feedback:" in call["stdin"]
    text = RESULT if synthesizing else PLAN
    usage = {"input_tokens": 17, "output_tokens": 7} if synthesizing else {
        "input_tokens": 11, "output_tokens": 3
    }
    emit({"type": "thread.started", "thread_id": "fixture-thread"})
    emit({"type": "turn.started"})
    emit({"type": "item.completed",
          "item": {"id": "fixture-item", "type": "agent_message", "text": text}})
    emit({"type": "turn.completed", "usage": usage})
elif provider == "claude":
    if behavior == "claude_429":
        emit({"type": "result", "subtype": "error_during_execution",
              "is_error": True, "api_error_status": 429, "result": "Fixture error"})
        sys.exit(1)
    emit({"type": "result", "subtype": "success", "is_error": False, "result": PLAN,
          "usage": {"input_tokens": 11, "output_tokens": 3}})
else:
    emit({"type": "text", "data": REVIEW[:9]})
    emit({"type": "text", "data": REVIEW[9:]})
    emit({"type": "usage", "usage": {"input_tokens": 13, "output_tokens": 5}})
    emit({"type": "end", "stopReason": "end_turn"})
"""


class LivePolicyTests(unittest.TestCase):
    def test_read_only_commands(self):
        workspace = Path("sample-workspace")
        prompt_file = workspace / "prompt.txt"

        argv, use_stdin = build_command("codex", None, prompt_file)
        self.assertTrue(use_stdin)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        self.assertEqual(argv[argv.index("--config") + 1], "mcp_servers={}")

        for directory, tools in [(None, ""), (workspace, "Read,Grep,Glob")]:
            with self.subTest(workspace=directory):
                argv, use_stdin = build_command("claude", directory, prompt_file)
                self.assertTrue(use_stdin)
                self.assertEqual(argv[argv.index("--tools") + 1], tools)
                self.assertIn("--strict-mcp-config", argv)
                self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")

        argv, use_stdin = build_command("grok", workspace, prompt_file)
        self.assertFalse(use_stdin)
        self.assertIn(("--deny", "mcp__*"), tuple(zip(argv, argv[1:])))
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(argv[argv.index("--prompt-file") + 1], str(prompt_file))

    def test_live_environment_filters_credentials_and_unrelated_variables(self):
        homes = {
            "codex": "CODEX_HOME",
            "claude": "CLAUDE_CONFIG_DIR",
            "grok": "GROK_HOME",
        }
        excluded = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "FIXTURE_UNRELATED")
        with tempfile.TemporaryDirectory() as directory:
            home = str(Path(directory) / "home")
            settings = {"HOME": home, **dict.fromkeys(excluded, "fixture-value")}
            settings.update({variable: str(Path(directory) / name) for name, variable in homes.items()})
            with patch.dict(os.environ, settings, clear=True):
                for provider, variable in homes.items():
                    with self.subTest(provider=provider):
                        environment = live_environment(provider)
                        self.assertEqual(environment["HOME"], home)
                        self.assertEqual(environment[variable], settings[variable])
                        for name in (*excluded, *(set(homes.values()) - {variable})):
                            self.assertNotIn(name, environment)


@unittest.skipUnless(os.name == "posix", "requires executable Python scripts with POSIX shebangs")
class LiveCLITests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.state = self.fixture / "runs"
        constants = f"PLAN = {PLAN!r}\nREVIEW = {REVIEW!r}\nRESULT = {RESULT!r}\n"
        for provider in ("codex", "claude", "grok"):
            script = self.fixture / provider
            script.write_text(f"#!{sys.executable}\n{constants}{FAKE_PROVIDER}", encoding="utf-8")
            script.chmod(0o700)
        self.enterContext(patch.dict(os.environ, {
            "PATH": os.pathsep.join(filter(None, (str(self.fixture), os.environ.get("PATH")))),
            "HOME": str(self.fixture / "home"),
            "CODEX_HOME": str(self.fixture / "codex-home"),
            "CLAUDE_CONFIG_DIR": str(self.fixture / "claude-home"),
            "GROK_HOME": str(self.fixture / "grok-home"),
            "FIRSTCHAIR_TEST_FIXTURE": str(self.fixture),
            "FIRSTCHAIR_TEST_BEHAVIOR": "success",
        }))

    def cli(self, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["--state-dir", str(self.state), *args])
        self.assertEqual(code, expected, stderr.getvalue() or stdout.getvalue())
        return stdout.getvalue(), stderr.getvalue()

    def run_live(self, *options, provider="codex", expected=0):
        return self.cli("run", "--provider", provider, *options, TASK, expected=expected)

    def saved_record(self, stdout):
        record = json.loads(stdout)
        paths = list(self.state.glob("*.json"))
        self.assertEqual([path.name for path in paths], [f"{record['run_id']}.json"])
        self.assertEqual(json.loads(paths[0].read_text(encoding="utf-8")), record)
        return record

    def calls(self):
        path = self.fixture / "calls.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_codex_grok_workflow_saves_stages_and_measured_usage(self):
        stdout, _ = self.run_live("--reviewer", "grok")
        record = self.saved_record(stdout)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["result"], RESULT)
        self.assertEqual(
            {stage: (data["provider"], data["text"]) for stage, data in record["stages"].items()},
            {"plan": ("codex", PLAN), "review": ("grok", REVIEW), "synthesize": ("codex", RESULT)},
        )
        self.assertEqual(record["usage"], {
            "provenance": "measured", "input_tokens": 41, "output_tokens": 15,
        })
        plan, review, synthesis = [call for call in self.calls() if "--version" not in call["args"]]
        self.assertEqual([call["provider"] for call in (plan, review, synthesis)], ["codex", "grok", "codex"])
        self.assertIn(TASK, plan["stdin"])
        self.assertIn(PLAN, review["prompt_file"])
        self.assertEqual(review["stdin"], "")
        self.assertIn(REVIEW, synthesis["stdin"])

    def test_text_format_prints_result_section(self):
        stdout, _ = self.run_live("--format", "text")
        self.assertIn(f"## Result\n\n{RESULT}", stdout)

    def test_unsupported_version_is_rejected_before_record_creation(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_TEST_BEHAVIOR": "unsupported"}):
            stdout, stderr = self.run_live(expected=1)
        self.assertEqual(stdout, "")
        self.assertIn("not ready", stderr)
        self.assertIn("unsupported_provider_version", stderr)
        self.assertFalse(self.state.exists())
        self.assertEqual(self.calls(), [{"provider": "codex", "args": ["--version"]}])

    def test_claude_rate_limit_fails_plan_without_stage_output(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_TEST_BEHAVIOR": "claude_429"}):
            stdout, _ = self.run_live(provider="claude", expected=1)
        record = self.saved_record(stdout)
        self.assertEqual((record["status"], record["stage"], record["error"]),
                         ("failed", "plan", "rate_limited"))
        self.assertEqual(record["stages"], {})
        self.assertNotIn("result", record)

    def test_reviewer_failure_preserves_plan(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_TEST_BEHAVIOR": "claude_429"}):
            stdout, _ = self.run_live("--reviewer", "claude", expected=1)
        record = self.saved_record(stdout)
        self.assertEqual((record["status"], record["stage"], record["error"]),
                         ("failed", "review", "rate_limited"))
        self.assertEqual(set(record["stages"]), {"plan"})
        self.assertEqual(record["stages"]["plan"]["text"], PLAN)
        self.assertNotIn("result", record)

    def test_timeout_kills_grandchild(self):
        with patch.dict(os.environ, {"FIRSTCHAIR_TEST_BEHAVIOR": "timeout"}):
            stdout, _ = self.run_live("--timeout", "1", expected=1)
        record = self.saved_record(stdout)
        self.assertEqual((record["status"], record["stage"], record["error"]),
                         ("failed", "plan", "provider_timeout"))
        pid = int((self.fixture / "grandchild.pid").read_text(encoding="utf-8"))
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_live_dry_run_reports_read_only_without_record_or_model_calls(self):
        stdout, _ = self.run_live("--dry-run")
        result = json.loads(stdout)
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["permissions"], "read-only")
        self.assertFalse(self.state.exists())
        calls = self.calls()
        self.assertTrue(calls)
        self.assertTrue(all(call["args"] == ["--version"] for call in calls))

    def test_synthetic_provider_rejects_workspace(self):
        _, stderr = self.run_live("--workspace", str(self.fixture), provider="synthetic", expected=1)
        self.assertIn("--workspace", stderr)
        self.assertIn("require a live --provider", stderr)
        self.assertFalse(self.state.exists())

    def test_doctor_reports_versions_and_enabled_contracts(self):
        stdout, _ = self.cli("doctor")
        providers = json.loads(stdout)["providers"]
        for name, version in {"codex": "0.171.0", "claude": "2.1.329", "grok": "1.0.77"}.items():
            with self.subTest(provider=name):
                provider = providers[name]
                self.assertEqual(provider["version"], version)
                self.assertEqual(provider["contract"], "verified")
                self.assertIs(provider["enabled"], True)
        self.assertCountEqual(self.calls(), [
            {"provider": "codex", "args": ["--version"]},
            {"provider": "claude", "args": ["--version"]},
            {"provider": "grok", "args": ["--no-auto-update", "--version"]},
        ])

    def test_offline_doctor_discovers_providers_without_running_them(self):
        stdout, _ = self.cli("doctor", "--offline")
        providers = json.loads(stdout)["providers"]
        for name in ("codex", "claude", "grok"):
            with self.subTest(provider=name):
                self.assertEqual(providers[name]["discovery"], "installed")
                self.assertIs(providers[name]["enabled"], False)
        self.assertEqual(self.calls(), [])
