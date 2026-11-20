"""Command-line entry point."""

import argparse
import json
import sys
from time import monotonic
from functools import partial
from pathlib import Path

from . import __version__, accounts
from .config import read_synthetic_config
from .delegation import configure_parser as configure_delegate_parser
from .delegation import execute as execute_delegation
from .inventory import provider_inventory, routing_explanation
from .live import PROVIDERS as LIVE_PROVIDERS
from .live import LiveLimits, LiveProvider, LiveSession, describe, readiness
from .provider import ExecutionLimits, ProviderError, SyntheticProvider
from .state_listing import list_runs
from .workflow import (
    demo_plan,
    demo_review,
    demo_synthesize,
    recover_workflow,
    record_path,
    run_workflow,
)

STAGES = ("plan", "review", "synthesize")
STATE_DIR = Path(".firstchair")
LEGACY_STATE_DIR = Path(".triadmux")
LEGACY_NOTICE = (
    "Firstchair replaces triadmux. "
    "The triadmux command will be removed in the next minor release."
)


def default_state_dir() -> Path:
    """Read the former TriadMux state directory until the new one exists."""
    if not STATE_DIR.exists() and LEGACY_STATE_DIR.is_dir():
        print(f"Reading former state directory {LEGACY_STATE_DIR}/", file=sys.stderr)
        return LEGACY_STATE_DIR
    return STATE_DIR


def legacy_main(argv: list[str] | None = None) -> int:
    print(LEGACY_NOTICE, file=sys.stderr)
    return main(argv, prog="triadmux")


def main(argv: list[str] | None = None, prog: str = "firstchair") -> int:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--state-dir", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Discover providers and check their versions")
    doctor.add_argument("--offline", action="store_true", help="Only search PATH; do not run --version")
    run = commands.add_parser("run", help="Run a plan, review and synthesis workflow")
    modes = run.add_mutually_exclusive_group(required=True)
    modes.add_argument("--demo", action="store_true")
    modes.add_argument(
        "--provider", choices=("synthetic", *LIVE_PROVIDERS),
        help="Lead provider. Live providers run read-only with your existing sign-in",
    )
    run.add_argument("--reviewer", choices=LIVE_PROVIDERS, help="Live reviewer provider (default: the lead)")
    run.add_argument("--workspace", type=Path, help="Directory live providers may read (default: an empty temp dir)")
    run.add_argument("--profile", help="Named account profile for the lead (see firstchair auth)")
    run.add_argument("--reviewer-profile", help="Named account profile for the reviewer")
    run.add_argument("--timeout", type=float, default=None, help="Per-stage timeout in seconds")
    run.add_argument("--max-output-bytes", type=int, default=None, help="Provider output limit")
    run.add_argument("--max-input-bytes", type=int, help="Maximum bytes in each provider request")
    run.add_argument("--total-timeout", type=float, help="Time budget across all stages")
    run.add_argument("--config", type=Path, help="TOML file with synthetic execution limits")
    run.add_argument("--dry-run", action="store_true", help="Show the execution plan without running it")
    run.add_argument("--format", choices=("json", "text"), default="json", help="Output format")
    run.add_argument("task", help="Task text, or - to read it from stdin")
    status = commands.add_parser("status", help="Read a run record")
    status.add_argument("run_id")
    commands.add_parser("runs", help="List saved run summaries")
    recover = commands.add_parser("recover", help="Mark an abandoned run interrupted")
    recover.add_argument("run_id")
    delegate = commands.add_parser("delegate", help="Dispatch workers in isolated Git worktrees")
    configure_delegate_parser(delegate)
    auth = commands.add_parser("auth", help="Manage named provider logins")
    accounts.configure_parser(auth)
    args = parser.parse_args(argv)
    if args.command == "auth":
        return accounts.execute(args)
    if args.command == "delegate":
        return execute_delegation(args)
    if args.state_dir is None:
        args.state_dir = default_state_dir()

    try:
        if args.command == "doctor":
            providers = provider_inventory()
            if not args.offline:
                for name in LIVE_PROVIDERS:
                    report = readiness(name)
                    contract = report["contract"]
                    supported = contract in ("verified", "compatible")
                    providers[name].update(
                        version=report["version"], contract=contract,
                        readiness="ready" if supported else providers[name]["readiness"],
                        enabled=supported,
                    )
            result = {"providers": providers}
        elif args.command == "run":
            if args.task == "-":
                args.task = sys.stdin.read()
            if not args.task.strip():
                raise ValueError("task must contain text")
            live = args.provider in LIVE_PROVIDERS
            live_only = (args.reviewer, args.workspace, args.profile, args.reviewer_profile)
            if not live and any(value is not None for value in live_only):
                raise ValueError("--reviewer, --workspace and --profile require a live --provider")
            overrides = {
                "timeout": args.timeout,
                "max_output_bytes": args.max_output_bytes,
                "max_input_bytes": args.max_input_bytes,
                "total_timeout": args.total_timeout,
            }
            overrides = {key: value for key, value in overrides.items() if value is not None}
            details = None
            if live:
                if args.config is not None:
                    raise ValueError("--config applies to --provider synthetic")
                defaults = LiveLimits()
                limits = LiveLimits(
                    timeout=overrides.get("timeout", defaults.timeout),
                    output_bytes=overrides.get("max_output_bytes", defaults.output_bytes),
                    input_bytes=overrides.get("max_input_bytes", defaults.input_bytes),
                )
                total = overrides.get("total_timeout")
                if total is not None and not 0 < total <= 4 * 3600:
                    raise ValueError("total timeout must be greater than 0 and at most 14400 seconds")
                deadline = None if total is None else monotonic() + total
                lead = LiveProvider(args.provider, limits, args.workspace, args.profile, deadline)
                reviewer_name = args.reviewer or args.provider
                if reviewer_name == args.provider and args.reviewer_profile in (None, args.profile):
                    reviewer = lead
                else:
                    reviewer = LiveProvider(
                        reviewer_name, limits, args.workspace,
                        args.reviewer_profile or (args.profile if reviewer_name == args.provider else None),
                        deadline,
                    )
                session = LiveSession(lead, reviewer)
                stages = (session.plan, session.review, session.synthesize)
                details = session.details
            elif args.provider:
                settings = read_synthetic_config(args.config) if args.config is not None else {}
                settings.update(overrides)
                defaults = ExecutionLimits()
                limits = ExecutionLimits(
                    timeout=settings.get("timeout", defaults.timeout),
                    output_bytes=settings.get("max_output_bytes", defaults.output_bytes),
                    input_bytes=settings.get("max_input_bytes", defaults.input_bytes),
                )
                provider = SyntheticProvider(limits, total_timeout=settings.get("total_timeout"))
                stages = tuple(partial(provider.run, stage) for stage in STAGES)
            else:
                if overrides or args.config is not None:
                    raise ValueError("execution configuration requires --provider")
                stages = (demo_plan, demo_review, demo_synthesize)
            if args.dry_run and live:
                result = {
                    "status": "planned",
                    "provider": args.provider,
                    "selection": "explicit",
                    "roles": describe({"lead": lead, "reviewer": reviewer}),
                    "stages": {"plan": "lead", "review": "reviewer", "synthesize": "lead"},
                    "limits": {
                        "stage_timeout": limits.timeout,
                        "stage_output_bytes": limits.output_bytes,
                        "stage_input_bytes": limits.input_bytes,
                        "total_timeout": total,
                    },
                    "permissions": "read-only",
                }
            elif args.dry_run:
                result = {
                    "status": "planned",
                    "provider": args.provider or "demo",
                    "selection": "explicit",
                    "routing": routing_explanation(args.provider or "demo"),
                    "stages": STAGES,
                }
                if args.provider:
                    result["limits"] = {
                        "stage_timeout": limits.timeout,
                        "stage_output_bytes": limits.output_bytes,
                        "stage_input_bytes": limits.input_bytes,
                        "total_timeout": provider.total_timeout,
                    }
                    # Provider stages use a controller temp dir, not the repo cwd.
                    result["workspace"] = "temporary"
            else:
                if live:
                    # Reject an unsupported CLI before a run record is created.
                    for provider in {id(lead): lead, id(reviewer): reviewer}.values():
                        try:
                            provider.prepare()
                        except ProviderError as error:
                            raise ValueError(
                                f"{provider.provider} is not ready: {error}. Run firstchair doctor"
                            ) from None
                result = run_workflow(args.task, args.state_dir, *stages, details=details)
        elif args.command == "recover":
            result = recover_workflow(args.state_dir, args.run_id)
        elif args.command == "runs":
            result = {"runs": list_runs(args.state_dir)}
        else:
            path = record_path(args.state_dir, args.run_id)
            result = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(result, dict):
                raise ValueError("invalid run record")
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1

    if args.command == "run" and args.format == "text" and "run_id" in result:
        _print_text(result)
    else:
        print(json.dumps(result, indent=2))
    if args.command == "recover":
        return 0
    return int(result.get("status") in {"failed", "interrupted"})


def _print_text(record: dict[str, object]) -> None:
    """Human-readable run summary. The JSON record stays on disk."""
    stages = record.get("stages")
    if isinstance(stages, dict):
        for name in ("plan", "review"):
            stage = stages.get(name)
            if isinstance(stage, dict):
                print(f"## {name.title()} ({stage.get('provider')})\n\n{stage.get('text', '').strip()}\n")
    if record.get("status") == "completed":
        print(f"## Result\n\n{str(record.get('result', '')).strip()}\n")
    else:
        print(f"## {record.get('status')}: {record.get('error', 'unknown')}\n")
    usage = record.get("usage")
    if isinstance(usage, dict) and usage.get("provenance") != "unknown":
        print(f"Tokens ({usage['provenance']}): {usage['input_tokens']} in, {usage['output_tokens']} out")
    print(f"Run {record['run_id']} · firstchair status {record['run_id']}", file=sys.stderr)
