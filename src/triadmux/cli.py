"""Command-line entry point."""

import argparse
import json
import sys
from functools import partial
from pathlib import Path

from . import __version__
from .config import read_synthetic_config
from .inventory import provider_inventory, routing_explanation
from .provider import ExecutionLimits, SyntheticProvider
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="triadmux")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--state-dir", type=Path, default=Path(".triadmux"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Discover provider executables on PATH")
    run = commands.add_parser("run", help="Run the synthetic leader/reviewer workflow")
    modes = run.add_mutually_exclusive_group(required=True)
    modes.add_argument("--demo", action="store_true")
    modes.add_argument("--provider", choices=("synthetic",))
    run.add_argument("--timeout", type=float, default=None, help="Provider timeout in seconds")
    run.add_argument("--max-output-bytes", type=int, default=None, help="Provider output limit")
    run.add_argument("--max-input-bytes", type=int, help="Maximum bytes in each provider request")
    run.add_argument("--total-timeout", type=float, help="Time budget across synthetic stages")
    run.add_argument("--config", type=Path, help="TOML file with synthetic execution limits")
    run.add_argument("--dry-run", action="store_true", help="Show the execution plan without running it")
    run.add_argument("task")
    status = commands.add_parser("status", help="Read a run record")
    status.add_argument("run_id")
    commands.add_parser("runs", help="List saved run summaries")
    recover = commands.add_parser("recover", help="Mark an abandoned run interrupted")
    recover.add_argument("run_id")
    args = parser.parse_args(argv)

    try:
        if args.command == "doctor":
            result = {"providers": provider_inventory()}
        elif args.command == "run":
            if not args.task.strip():
                raise ValueError("task must contain text")
            overrides = {
                "timeout": args.timeout,
                "max_output_bytes": args.max_output_bytes,
                "max_input_bytes": args.max_input_bytes,
                "total_timeout": args.total_timeout,
            }
            overrides = {key: value for key, value in overrides.items() if value is not None}
            if args.provider:
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
            if args.dry_run:
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
                result = run_workflow(args.task, args.state_dir, *stages)
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

    print(json.dumps(result, indent=2))
    if args.command == "recover":
        return 0
    return int(result.get("status") in {"failed", "interrupted"})
