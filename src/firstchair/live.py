"""Read-only live adapters for Codex CLI, Claude Code and Grok Build.

Each stage launches one bounded, non-interactive provider process. The
controller chooses the executable, flags, working directory, environment and
limits. Provider output is parsed fail-closed by a version-gated parser.
"""

import asyncio
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from time import monotonic
from typing import Any

from .accounts import CREDENTIAL_OVERRIDES, HOME_VARIABLE, account_environment
from .claude_json import parse_claude_json
from .codex_jsonl import parse_codex_jsonl
from .grok_jsonl import parse_grok_jsonl
from .provider import ProviderError, _subprocess_environment, run_bounded
from .usage import Reply, Usage
from .versions import check_version, read_version

PROVIDERS = ("codex", "claude", "grok")
MAX_PROMPT_BYTES = 256 * 1024
# Names a signed-in CLI needs to find its own login, config and caches.
_LIVE_ENV_NAMES = frozenset({
    "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "TERM", "TZ",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
})
_PARSERS: dict[str, Callable[..., Reply]] = {
    "codex": parse_codex_jsonl,
    "claude": parse_claude_json,
    "grok": parse_grok_jsonl,
}


@dataclass(frozen=True)
class LiveLimits:
    timeout: float = 600.0
    output_bytes: int = 8 * 1024 * 1024
    input_bytes: int = MAX_PROMPT_BYTES

    def __post_init__(self) -> None:
        if not 0 < self.timeout <= 3600:
            raise ValueError("live stage timeout must be greater than 0 and at most 3600 seconds")
        if type(self.output_bytes) is not int or not 1024 <= self.output_bytes <= 64 * 1024 * 1024:
            raise ValueError("live output limit must be between 1024 and 67108864 bytes")
        if type(self.input_bytes) is not int or not 1 <= self.input_bytes <= MAX_PROMPT_BYTES:
            raise ValueError(f"live prompt limit must be between 1 and {MAX_PROMPT_BYTES} bytes")


def live_environment(provider: str, profile: str | None = None) -> dict[str, str]:
    """Allowlisted environment plus what the CLI needs to find its own login.

    API keys never pass through, so each CLI uses its native sign-in.
    """
    source = account_environment(provider, profile) if profile is not None else dict(os.environ)
    environment = _subprocess_environment()
    for name in (*_LIVE_ENV_NAMES, HOME_VARIABLE[provider]):
        if name in source and name not in CREDENTIAL_OVERRIDES:
            environment[name] = source[name]
    environment["NO_COLOR"] = "1"
    return environment


def provider_version(provider: str, env: dict[str, str] | None = None) -> str:
    """Run `PROVIDER --version` with a short deadline and return X.Y.Z."""
    executable = shutil.which(provider)
    if executable is None:
        raise ProviderError("provider_unavailable")
    argv = [executable, "--version"] if provider != "grok" else [executable, "--no-auto-update", "--version"]
    try:
        with TemporaryDirectory(prefix="firstchair-version-") as cwd:
            result = subprocess.run(
                argv, cwd=cwd, env=env if env is not None else live_environment(provider),
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                errors="replace", timeout=20,
            )
    except (OSError, subprocess.TimeoutExpired):
        raise ProviderError("provider_unavailable") from None
    if result.returncode:
        raise ProviderError("provider_unavailable")
    return read_version(provider, result.stdout)


def readiness(provider: str) -> dict[str, object]:
    """Report executable, version and contract support without running a model."""
    executable = shutil.which(provider)
    report: dict[str, object] = {"executable": executable, "version": None, "contract": "missing"}
    if executable is None:
        return report
    try:
        version = provider_version(provider)
        report["version"] = version
        report["contract"] = check_version(provider, version)
    except ProviderError as error:
        report["contract"] = str(error)
    return report


def build_command(provider: str, workspace: Path | None, prompt_file: Path) -> tuple[tuple[str, ...], bool]:
    """Return a read-only argv and whether the prompt goes to stdin."""
    if provider == "codex":
        argv = (
            "codex", "--ask-for-approval", "never", "exec", "--ephemeral",
            "--sandbox", "read-only", "--skip-git-repo-check", "--color", "never",
            # Drop user-configured MCP servers so tools cannot reach outside the sandbox.
            "--config", "mcp_servers={}", "--json",
        )
        return (*argv, "-"), True
    if provider == "claude":
        tools = "Read,Grep,Glob" if workspace is not None else ""
        argv = (
            "claude", "-p", "--output-format", "json", "--no-session-persistence",
            "--setting-sources", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--tools", tools, "--permission-mode", "dontAsk",
        )
        return argv, True
    if provider == "grok":
        # Grok's read-only sandbox needs bubblewrap. Landlock `workspace` plus
        # deny-by-default permissions and an explicit read-only tool list
        # keeps writes and MCP calls out of reach.
        tools = "read_file,list_dir,grep" if workspace is not None else ""
        argv = (
            "grok", "--no-auto-update", "--prompt-file", str(prompt_file),
            "--output-format", "streaming-json", "--no-subagents", "--disable-web-search",
            "--sandbox", "workspace", "--permission-mode", "dontAsk",
            "--tools", tools, "--deny", "mcp__*", "--deny", "Edit", "--deny", "Write",
            "--deny", "Bash", "--deny", "WebFetch",
        )
        return argv, False
    raise ValueError(f"unknown live provider {provider}")


@dataclass
class LiveProvider:
    """Run one read-only provider turn per call under shared limits."""

    provider: str
    limits: LiveLimits = field(default_factory=LiveLimits)
    workspace: Path | None = None
    profile: str | None = None
    deadline: float | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"unknown live provider {self.provider}")
        if self.workspace is not None:
            self.workspace = self.workspace.resolve()
            if not self.workspace.is_dir():
                raise ValueError("workspace must be an existing directory")

    def prepare(self) -> str:
        """Check the installed version once before any stage runs."""
        if self.version is None:
            env = live_environment(self.provider, self.profile)
            version = provider_version(self.provider, env)
            check_version(self.provider, version)
            self.version = version
        return self.version

    def ask(self, prompt: str) -> Reply:
        version = self.prepare()
        payload = prompt.encode("utf-8")
        if len(payload) > self.limits.input_bytes:
            raise ProviderError("input_limit")
        timeout = self.limits.timeout
        timeout_error = "provider_timeout"
        if self.deadline is not None:
            remaining = self.deadline - monotonic()
            if remaining <= 0:
                raise ProviderError("budget_exhausted")
            if remaining <= timeout:
                timeout, timeout_error = remaining, "budget_exhausted"
        env = live_environment(self.provider, self.profile)
        try:
            with TemporaryDirectory(prefix="firstchair-live-") as scratch:
                prompt_file = Path(scratch) / "prompt.txt"
                prompt_file.write_bytes(payload)
                argv, use_stdin = build_command(self.provider, self.workspace, prompt_file)
                executable = shutil.which(argv[0], path=env.get("PATH"))
                if executable is None:
                    raise ProviderError("provider_unavailable")
                argv = (executable, *argv[1:])
                cwd = str(self.workspace) if self.workspace is not None else scratch
                with TemporaryFile() as request:
                    if use_stdin:
                        request.write(payload)
                        request.seek(0)
                    returncode, output = asyncio.run(
                        _bounded(argv, request, self.limits.output_bytes, cwd, env, timeout, timeout_error)
                    )
        except OSError:
            raise ProviderError("provider_unavailable") from None
        return _PARSERS[self.provider](output, version=version, returncode=returncode)


async def _bounded(
    argv: tuple[str, ...], request, output_bytes: int, cwd: str,
    env: dict[str, str], timeout: float, timeout_error: str,
) -> tuple[int, bytes]:
    try:
        async with asyncio.timeout(timeout):
            return await run_bounded(argv, request, output_bytes, cwd=cwd, env=env)
    except TimeoutError:
        raise ProviderError(timeout_error) from None


PLAN_PROMPT = """You are the lead engineer in a multi-model review. Do not modify files.
Write a concise, concrete plan for the task below: the approach, the steps,
the files or areas likely involved, and how to verify the result.

Task:
{task}
"""

REVIEW_PROMPT = """You are an independent reviewer. Do not modify files.
Critically review the lead's plan for the task below. List concrete problems,
missing steps, risks and a better alternative where one exists. Be specific
and brief. If the plan is sound, say so and name the single most important
verification step.

Task:
{task}

Lead's plan:
{plan}
"""

SYNTHESIS_PROMPT = """You are the lead engineer. Do not modify files.
Produce the final answer for the task below. Incorporate the reviewer's
valid points, reject invalid ones with a short reason, and end with a
numbered list of next actions.

Task:
{task}

Your plan:
{plan}

Reviewer's feedback:
{review}
"""


@dataclass
class LiveSession:
    """Lead plans and synthesizes; the reviewer critiques the plan."""

    lead: LiveProvider
    reviewer: LiveProvider
    task: str = ""
    plan_text: str = ""
    stages: dict[str, dict[str, object]] = field(default_factory=dict)

    def _record(self, stage: str, provider: LiveProvider, reply: Reply) -> str:
        self.stages[stage] = {
            "provider": provider.provider,
            "version": provider.version,
            "text": reply.text,
            "usage": reply.usage.as_record(),
        }
        return reply.text

    def plan(self, task: str) -> str:
        self.task = task
        self.plan_text = self._record("plan", self.lead, self.lead.ask(PLAN_PROMPT.format(task=task)))
        return self.plan_text

    def review(self, plan: str) -> str:
        prompt = REVIEW_PROMPT.format(task=self.task, plan=plan)
        return self._record("review", self.reviewer, self.reviewer.ask(prompt))

    def synthesize(self, review: str) -> str:
        prompt = SYNTHESIS_PROMPT.format(task=self.task, plan=self.plan_text, review=review)
        return self._record("synthesize", self.lead, self.lead.ask(prompt))

    def details(self) -> dict[str, object]:
        return {"stages": self.stages, "usage": total_usage(self.stages)}


def total_usage(stages: dict[str, dict[str, object]]) -> dict[str, object]:
    """Sum measured counts. Mark the total partial when any stage is unknown."""
    usages: list[dict[str, Any]] = [stage["usage"] for stage in stages.values()]  # type: ignore[misc]
    measured = [usage for usage in usages if usage["provenance"] == "measured"]
    if not measured:
        return Usage().as_record()
    return {
        "provenance": "measured" if len(measured) == len(usages) else "partial",
        "input_tokens": sum(usage["input_tokens"] for usage in measured),
        "output_tokens": sum(usage["output_tokens"] for usage in measured),
    }


def describe(providers: dict[str, LiveProvider]) -> dict[str, object]:
    """Dry-run view of the live roles."""
    return {
        role: {
            "provider": provider.provider,
            "workspace": str(provider.workspace) if provider.workspace else "temporary",
            "profile": provider.profile,
            **{key: value for key, value in readiness(provider.provider).items() if key != "executable"},
        }
        for role, provider in providers.items()
    }


def dumps(value: object) -> str:
    return json.dumps(value, indent=2)
