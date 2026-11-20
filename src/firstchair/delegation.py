#!/usr/bin/env python3
"""Dispatch a bounded task from a lead agent session to a Codex or Grok worker.

Each task runs headless in its own git worktree outside the checkout, so a
worker never touches the lead's working tree. A ``read`` task runs in a
detached worktree that is removed afterwards. A ``write`` task keeps its
worktree on branch ``delegate/NAME`` for the lead to review, collect and
merge. Workers do not commit, push or install packages. The lead owns Git.

This is maintainer tooling. It launches the real provider CLIs with the
maintainer's existing logins. CI uses synthetic worker commands.
Job metadata goes to the ignored ``.firstchair/delegations/NAME/`` directory.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .accounts import account_environment
from .codex_jsonl import CodexUsage, parse_codex_jsonl
from .provider import ProviderError
from .redaction import redact_record

DESCRIPTION = "Dispatch a bounded task to a Codex or Grok worker in a git worktree."
PROVIDERS = ("codex", "grok")
LEAD_NAMES = {"claude": "Claude Code", "codex": "Codex", "grok": "Grok Build"}
WORKER_ORDER = {
    "claude": {"read": ("grok", "codex"), "write": ("codex", "grok")},
    "codex": {"read": ("grok",), "write": ("grok",)},
    "grok": {"read": ("codex",), "write": ("codex",)},
}
MODES = ("read", "write")
BRANCH_PREFIX = "delegate/"
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
DEFAULT_TIMEOUT = {"read": 600, "write": 1800}
REPLY_LIMIT = 20_000
USAGE_LOG_LIMIT = 2 * 1024 * 1024
# Delegation logs and run records never travel into a worker's worktree.
STATE_EXCLUDES = (":(exclude).firstchair", ":(exclude).triadmux")

PREAMBLE = """\
You are a {provider} worker dispatched by the lead {lead} session for the
Firstchair repository. You run headless, so nobody can answer questions mid-task.

Rules for this task:
- Read AGENTS.md first and follow it, plus any instructions below.
- Mode: {mode}. {mode_rule}
- Do not run git commit, push, merge, rebase, reset, checkout or branch commands.
  Do not install packages. Do not use the network except for your own model API.
- Never read or copy .firstchair/, .triadmux/, credentials, transcripts or account data.
  Use invented fixtures only.
- Stay inside the scope below. If it is ambiguous, pick the safest reading and say so.

End your reply with these sections, in this order:
## Summary
## Files changed
## Verification
(exact commands you ran and their results; say if you skipped any)
## Open issues

Task:
"""

MODE_RULES = {
    "read": "Do not create, edit or delete files. Investigate and report only.",
    "write": (
        "Edit files in this worktree to complete the task and run the project tests "
        "(PYTHONPATH=src python -m unittest discover -s tests -v) before you finish."
    ),
}


class DelegateError(Exception):
    """A usage or environment problem reported without a traceback."""


@dataclass(frozen=True)
class Job:
    provider: str
    mode: str
    name: str
    repo: Path
    worktree: Path
    log_dir: Path
    timeout: float
    model: str | None = None
    effort: str | None = None
    lead: str = "claude"

    @property
    def branch(self) -> str | None:
        return BRANCH_PREFIX + self.name if self.mode == "write" else None


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ("git", "-C", str(repo), *args), capture_output=True, text=True, check=False
    )
    if check and result.returncode:
        raise DelegateError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def repo_root(start: Path) -> Path:
    try:
        return Path(git(start, "rev-parse", "--show-toplevel").strip())
    except DelegateError:
        raise DelegateError(f"{start} is not inside a git repository") from None


def worktree_root(repo: Path, legacy: bool = False) -> Path:
    # TRIADMUX_WORKTREE_ROOT and ~/.cache/triadmux are the former names. New
    # worktrees use the Firstchair names; old ones stay findable for one release.
    variable = "TRIADMUX_WORKTREE_ROOT" if legacy else "FIRSTCHAIR_WORKTREE_ROOT"
    base = os.environ.get(variable) or (None if legacy else os.environ.get("TRIADMUX_WORKTREE_ROOT"))
    if base:
        return Path(base).expanduser().resolve() / repo.name
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    product = "triadmux" if legacy else "firstchair"
    return Path(cache).expanduser().resolve() / product / "worktrees" / repo.name


def delegation_dir(repo: Path, name: str) -> Path:
    """Logs for NAME. Delegations started before the rename stay under .triadmux/."""
    legacy = repo / ".triadmux" / "delegations" / name
    if legacy.is_dir() and not (repo / ".firstchair" / "delegations" / name).exists():
        return legacy
    return repo / ".firstchair" / "delegations" / name


def default_name(provider: str) -> str:
    return f"{provider}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def check_name(name: str) -> str:
    if not NAME_PATTERN.fullmatch(name):
        raise DelegateError("name must be 1-63 characters of a-z, 0-9, '.', '_' or '-'")
    return name


def build_prompt(job: Job, task: str) -> str:
    preamble = PREAMBLE.format(
        provider=LEAD_NAMES[job.provider], lead=LEAD_NAMES[job.lead],
        mode=job.mode, mode_rule=MODE_RULES[job.mode],
    )
    return preamble + task.strip() + "\n"


def build_command(job: Job, prompt_file: Path, reply_file: Path) -> tuple[list[str], bool]:
    """Return the worker argv and whether the prompt goes to stdin."""
    if job.provider == "codex":
        sandbox = "workspace-write" if job.mode == "write" else "read-only"
        argv = [
            "codex", "--ask-for-approval", "never", "exec", "--ephemeral",
            "--sandbox", sandbox, "--cd", str(job.worktree), "--color", "never",
            "--json", "--output-last-message", str(reply_file),
        ]
        if job.model:
            argv += ["--model", job.model]
        if job.effort:
            argv += ["--config", f"model_reasoning_effort={json.dumps(job.effort)}"]
        return [*argv, "-"], True

    # Grok's read-only sandbox needs bubblewrap, which cannot start on every host.
    # The Landlock workspace profile limits writes to the disposable worktree,
    # temp dirs and ~/.grok. Read tasks also lose the edit tools.
    argv = [
        "grok", "--no-auto-update", "--prompt-file", str(prompt_file),
        "--cwd", str(job.worktree), "--sandbox", "workspace",
        "--permission-mode", "bypassPermissions", "--output-format", "json",
        "--no-subagents",
    ]
    if job.mode == "read":
        argv += ["--disallowed-tools", "write,search_replace"]
    if job.model:
        argv += ["--model", job.model]
    if job.effort:
        argv += ["--reasoning-effort", job.effort]
    return argv, False


def create_worktree(job: Job) -> None:
    if job.worktree.exists():
        raise DelegateError(f"worktree {job.worktree} already exists; choose another --name")
    job.worktree.parent.mkdir(parents=True, exist_ok=True)
    if job.branch:
        if git(job.repo, "branch", "--list", job.branch).strip():
            raise DelegateError(f"branch {job.branch} already exists; choose another --name")
        git(job.repo, "worktree", "add", "-q", "-b", job.branch, str(job.worktree), "HEAD")
    else:
        git(job.repo, "worktree", "add", "-q", "--detach", str(job.worktree), "HEAD")


def carry_changes(repo: Path, worktree: Path) -> list[str]:
    """Copy the lead's uncommitted tracked diff and untracked files into a new worktree."""
    diff = subprocess.run(
        ("git", "-C", str(repo), "diff", "HEAD", "--binary"), capture_output=True, check=True
    ).stdout
    if diff:
        applied = subprocess.run(
            ("git", "-C", str(worktree), "apply", "--whitespace=nowarn"),
            input=diff, capture_output=True, check=False,
        )
        if applied.returncode:
            raise DelegateError("could not apply uncommitted changes to the worktree")
    untracked = git(
        repo, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", *STATE_EXCLUDES
    ).split("\0")
    for relative in filter(None, untracked):
        target = worktree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Copy a symlink as a link so its target's contents never leave the checkout.
        shutil.copy2(repo / relative, target, follow_symlinks=False)
    status = git(repo, "status", "--porcelain", "--", ".", *STATE_EXCLUDES)
    return [line[3:] for line in status.splitlines()]


def remove_worktree(repo: Path, worktree: Path) -> None:
    if worktree.exists():
        git(repo, "worktree", "remove", "--force", str(worktree))
    git(repo, "worktree", "prune", check=False)


class Terminated(Exception):
    """SIGTERM reached the controller while a worker was running."""


def _on_sigterm(signum: int, frame: object) -> None:
    raise Terminated


def run_worker(argv: list[str], stdin_file: Path | None, job: Job, runtime_dir: Path, env: dict[str, str] | None) -> tuple[int | None, float]:
    """Run one worker in its own process group. Return (exit code or None on timeout, seconds)."""
    started = time.monotonic()
    # A file on stdin cannot block the controller the way a full pipe can, so the
    # timeout covers the whole run, and an early worker exit cannot raise EPIPE.
    with (
        open(stdin_file if stdin_file else os.devnull, "rb") as stdin,
        open(runtime_dir / "stdout.log", "wb") as stdout,
        open(runtime_dir / "stderr.log", "wb") as stderr,
    ):
        try:
            process = subprocess.Popen(
                argv, cwd=job.worktree, stdin=stdin, stdout=stdout, stderr=stderr,
                start_new_session=os.name == "posix", env=env,
                umask=0o077 if env is not None else -1,
            )
        except OSError as error:
            raise DelegateError(f"could not start {argv[0]}: {error.strerror}") from None
        try:
            code: int | None = process.wait(timeout=job.timeout)
        except subprocess.TimeoutExpired:
            code = None
        finally:
            # Also reaps grandchildren that outlive a worker that exited normally.
            _kill_group(process)
    return code, time.monotonic() - started


def _kill_group(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except (ProcessLookupError, PermissionError):
        pass
    process.wait()


def extract_reply(job: Job, reply_file: Path, runtime_dir: Path) -> str:
    if job.provider == "codex":
        return reply_file.read_text(encoding="utf-8", errors="replace") if reply_file.exists() else ""
    raw = (runtime_dir / "stdout.log").read_text(encoding="utf-8", errors="replace")
    try:
        result = json.loads(raw)
    except ValueError:
        return ""
    if isinstance(result, dict) and isinstance(result.get("text"), str):
        return result["text"]
    return ""


def worker_usage(job: Job, returncode: int | None, runtime_dir: Path) -> CodexUsage:
    """Report only telemetry recognized by the versioned offline parser."""
    if job.provider != "codex" or returncode != 0:
        return CodexUsage()
    try:
        version_result = subprocess.run(
            ["codex", "--version"], cwd=job.worktree, capture_output=True,
            timeout=3, check=True, text=True,
        )
        name, version = version_result.stdout.strip().split()
        if name != "codex-cli":
            return CodexUsage()
        with (runtime_dir / "stdout.log").open("rb") as stream:
            output = stream.read(USAGE_LOG_LIMIT + 1)
        if len(output) <= USAGE_LOG_LIMIT:
            return parse_codex_jsonl(output, version=version, returncode=returncode).usage
    except (OSError, ValueError, subprocess.SubprocessError, ProviderError):
        pass
    return CodexUsage()


def worktree_changes(worktree: Path) -> dict[str, str]:
    status = git(worktree, "status", "--short", "--untracked-files=all")
    stat = git(worktree, "diff", "--stat", "HEAD")
    return {"status": status.rstrip(), "diffstat": stat.rstrip()}


def select_worker(provider: str, lead: str, mode: str) -> str:
    if provider != "auto":
        if shutil.which(provider) is None:
            raise DelegateError(f"{provider} is not on PATH")
        return provider
    for candidate in WORKER_ORDER[lead][mode]:
        if shutil.which(candidate) is not None:
            return candidate
    raise DelegateError(f"no eligible {mode} worker for {LEAD_NAMES[lead]} is on PATH")


def dispatch(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or Path.cwd()))
    if args.provider == "auto" and (args.model or args.effort):
        raise DelegateError("--model and --effort require an explicit worker")
    provider = select_worker(args.provider, args.lead, args.mode)
    if args.profile is not None and args.provider == "auto":
        raise DelegateError("--profile requires an explicit worker")
    env = account_environment(provider, args.profile) if args.profile is not None else None
    name = check_name(args.name or default_name(provider))
    timeout = DEFAULT_TIMEOUT[args.mode] if args.timeout is None else args.timeout
    if not math.isfinite(timeout) or timeout <= 0:
        raise DelegateError("--timeout must be a finite positive number")
    if args.dry_run:
        print(json.dumps({
            "status": "planned",
            "lead": args.lead,
            "requested_provider": args.provider,
            "provider": provider,
            "mode": args.mode,
            "timeout_seconds": timeout,
            "model": args.model,
            "effort": args.effort,
            "carry_changes": args.with_changes,
            "account_selection": "named" if args.profile is not None else "default",
        }, indent=2))
        return 0
    task = read_task(args)
    job = Job(
        provider=provider, mode=args.mode, name=name, repo=repo,
        worktree=worktree_root(repo) / name,
        log_dir=repo / ".firstchair" / "delegations" / name,
        timeout=timeout,
        model=args.model, effort=args.effort, lead=args.lead,
    )
    if job.log_dir.exists():
        raise DelegateError(f"log directory {job.log_dir} already exists; choose another --name")
    job.log_dir.mkdir(parents=True, mode=0o700)
    create_worktree(job)
    head = git(job.worktree, "rev-parse", "HEAD").strip()
    keep = job.mode == "write" or args.keep
    carried: list[str] = []
    previous = signal.signal(signal.SIGTERM, _on_sigterm)
    try:
        if args.with_changes:
            carried = carry_changes(repo, job.worktree)
            if job.branch and carried:
                # Keep the lead's carried work in its own commit so the worker's
                # edits stay a separate, cherry-pickable commit after collect.
                git(job.worktree, "add", "--all")
                git(job.worktree, "commit", "-q", "--no-verify", "-m",
                    f"Carry lead's uncommitted changes into delegate {name}")
        baseline = worktree_changes(job.worktree)["status"]
        with tempfile.TemporaryDirectory(prefix="firstchair-delegate-") as scratch:
            runtime_dir = Path(scratch)
            prompt_file = runtime_dir / "prompt.md"
            prompt_file.write_text(build_prompt(job, task), encoding="utf-8")
            reply_file = runtime_dir / "reply.md"
            argv, use_stdin = build_command(job, prompt_file, reply_file)
            code, elapsed = run_worker(argv, prompt_file if use_stdin else None, job, runtime_dir, env)
            usage = worker_usage(job, code, runtime_dir)
            reply = extract_reply(job, reply_file, runtime_dir) if code == 0 else ""
        changes = worktree_changes(job.worktree)
    except Terminated:
        raise DelegateError("terminated by SIGTERM; worker stopped") from None
    finally:
        signal.signal(signal.SIGTERM, previous)
        if not keep:
            remove_worktree(repo, job.worktree)

    status = "timeout" if code is None else ("completed" if code == 0 else "failed")
    summary = {
        "name": name,
        "provider": provider,
        "lead": job.lead,
        "requested_provider": args.provider,
        "mode": job.mode,
        "status": status,
        "exit_code": code,
        "elapsed_seconds": round(elapsed, 1),
        "usage": asdict(usage),
        "base_commit": head,
        "worktree": str(job.worktree) if keep else None,
        "branch": job.branch,
        "carried_changes": carried,
        "logs": str(job.log_dir),
        "changes": changes,
        "reply": reply if len(reply) <= REPLY_LIMIT else reply[:REPLY_LIMIT] + "\n[truncated]",
    }
    if job.mode == "read" and changes["status"] != baseline:
        summary["warning"] = "read task changed files in its disposable worktree; changes discarded"
    redact_record(summary)
    metadata = {key: summary[key] for key in ("name", "provider", "lead", "mode", "status", "usage")}
    (job.log_dir / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if status == "completed" else (124 if code is None else 1)


def read_task(args: argparse.Namespace) -> str:
    if args.prompt_file:
        task = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.task == "-" or args.task is None:
        if sys.stdin.isatty():
            raise DelegateError("pass a task, --prompt-file, or pipe the task on stdin")
        task = sys.stdin.read()
    else:
        task = args.task
    if not task.strip():
        raise DelegateError("task must contain text")
    return task


def delegate_worktrees(repo: Path) -> list[dict[str, str]]:
    roots = {worktree_root(repo), worktree_root(repo, legacy=True)}
    entries, current = [], {}
    for line in git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not line:
            if current:
                entries.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    found = []
    for entry in entries:
        path = Path(entry.get("worktree", ""))
        if path.parent in roots:
            branch = entry.get("branch", "").removeprefix("refs/heads/")
            found.append({"name": path.name, "worktree": str(path), "branch": branch or None})
    return found


def list_jobs(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo or Path.cwd()))
    jobs = []
    for job in delegate_worktrees(repo):
        changes = worktree_changes(Path(job["worktree"]))
        jobs.append({**job, "dirty": bool(changes["status"])})
    branches = [
        line.strip() for line in git(repo, "branch", "--list", BRANCH_PREFIX + "*",
                                     "--format=%(refname:short)").splitlines()
    ]
    print(json.dumps({"worktrees": jobs, "branches": branches}, indent=2))
    return 0


def find_job(repo: Path, name: str) -> dict[str, str]:
    """Find a worktree this script created: delegate branch or detached, with its logs."""
    check_name(name)
    for job in delegate_worktrees(repo):
        if job["name"] != name:
            continue
        owned_branch = job["branch"] in (None, BRANCH_PREFIX + name)
        if not owned_branch or not delegation_dir(repo, name).is_dir():
            raise DelegateError(f"worktree {name} was not created by delegate.py; leaving it alone")
        return job
    raise DelegateError(f"no delegate worktree named {name}")


def collect(args: argparse.Namespace) -> int:
    """Commit a write worker's changes on its branch so the lead can review and merge them."""
    repo = repo_root(Path(args.repo or Path.cwd()))
    job = find_job(repo, args.name)
    if not job["branch"]:
        raise DelegateError(f"{args.name} has no branch; only write tasks can be collected")
    worktree = Path(job["worktree"])
    git(worktree, "add", "--all")
    if not git(worktree, "status", "--porcelain").strip():
        print(json.dumps({"name": args.name, "branch": job["branch"], "committed": False}))
        return 0
    summary_file = delegation_dir(repo, args.name) / "summary.json"
    provider = "worker"
    if summary_file.exists():
        provider = json.loads(summary_file.read_text()).get("provider", provider)
    message = args.message or f"Collect {provider} delegate {args.name}"
    git(worktree, "commit", "-q", "-m", message)
    commit = git(worktree, "rev-parse", "HEAD").strip()
    stat = git(repo, "diff", "--stat", f"HEAD...{job['branch']}", check=False).rstrip()
    print(json.dumps({
        "name": args.name, "branch": job["branch"], "committed": True,
        "commit": commit, "diffstat_vs_head": stat,
    }, indent=2))
    return 0


def finish(args: argparse.Namespace) -> int:
    """Remove a delegate worktree; with --delete-branch also drop its branch."""
    repo = repo_root(Path(args.repo or Path.cwd()))
    job = find_job(repo, args.name)
    worktree = Path(job["worktree"])
    if worktree_changes(worktree)["status"] and not args.force:
        raise DelegateError(f"{args.name} has uncommitted changes; collect it or pass --force")
    remove_worktree(repo, worktree)
    deleted = False
    if args.delete_branch and job["branch"]:
        git(repo, "branch", "-D" if args.force else "-d", job["branch"])
        deleted = True
    print(json.dumps({"name": args.name, "removed": True, "branch_deleted": deleted}))
    return 0


def configure_parser(root: argparse.ArgumentParser) -> None:
    root.add_argument("--repo", help="Repository path (default: current checkout)")
    commands = root.add_subparsers(dest="delegate_command", required=True)

    run = commands.add_parser("run", help="Dispatch one task to a worker")
    run.add_argument("provider", choices=(*PROVIDERS, "auto"))
    run.add_argument("--lead", choices=LEAD_NAMES, default="claude",
                     help="Agent running the lead session (default: claude)")
    run.add_argument("task", nargs="?", help="Task text, or '-' to read stdin")
    run.add_argument("--mode", choices=MODES, default="read")
    run.add_argument("--name", help="Job name; also the worktree and branch suffix")
    run.add_argument("--prompt-file", help="Read the task from this file")
    run.add_argument("--timeout", type=float, help="Seconds before the worker is killed")
    run.add_argument("--profile", help="Use a named login for the explicit worker")
    run.add_argument("--model", help="Provider model override")
    run.add_argument("--effort", help="Provider reasoning effort override")
    run.add_argument("--dry-run", action="store_true", help="Show the selection without launching a worker")
    run.add_argument("--keep", action="store_true", help="Keep a read task's worktree")
    run.add_argument(
        "--with-changes", action="store_true",
        help="Copy the checkout's uncommitted and untracked files into the worktree",
    )
    run.set_defaults(handler=dispatch)

    listing = commands.add_parser("list", help="List delegate worktrees and branches")
    listing.set_defaults(handler=list_jobs)

    gather = commands.add_parser("collect", help="Commit a write task's changes on its branch")
    gather.add_argument("name")
    gather.add_argument("--message", "-m")
    gather.set_defaults(handler=collect)

    done = commands.add_parser("finish", help="Remove a delegate worktree")
    done.add_argument("name")
    done.add_argument("--delete-branch", action="store_true")
    done.add_argument("--force", action="store_true", help="Discard uncommitted or unmerged work")
    done.set_defaults(handler=finish)


def execute(args: argparse.Namespace) -> int:
    try:
        return args.handler(args)
    except (DelegateError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    root = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(root)
    return execute(root.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
