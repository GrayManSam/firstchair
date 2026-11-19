"""Command-line entry point."""

import argparse
import json
import shutil
import sys
from functools import partial
from pathlib import Path

from . import __version__
from .provider import ExecutionLimits, SyntheticProvider
from .workflow import demo_plan, demo_review, demo_synthesize, record_path, run_workflow


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
    run.add_argument("task")
    status = commands.add_parser("status", help="Read a run record")
    status.add_argument("run_id")
    args = parser.parse_args(argv)

    try:
        if args.command == "doctor":
            result = {
                "providers": {
                    provider: {"executable": shutil.which(executable), "auth": "unchecked"}
                    for provider, executable in (
                        ("codex", "codex"), ("claude", "claude"), ("grok", "grok")
                    )
                }
            }
        elif args.command == "run":
            if not args.task.strip():
                raise ValueError("task must contain text")
            if args.provider:
                defaults = ExecutionLimits()
                provider = SyntheticProvider(ExecutionLimits(
                    defaults.timeout if args.timeout is None else args.timeout,
                    defaults.output_bytes if args.max_output_bytes is None else args.max_output_bytes,
                ))
                stages = tuple(
                    partial(provider.run, stage) for stage in ("plan", "review", "synthesize")
                )
            else:
                if args.timeout is not None or args.max_output_bytes is not None:
                    raise ValueError("execution limits require --provider")
                stages = (demo_plan, demo_review, demo_synthesize)
            result = run_workflow(args.task, args.state_dir, *stages)
        else:
            path = record_path(args.state_dir, args.run_id)
            result = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(result, dict):
                raise ValueError("invalid run record")
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return int(result.get("status") in {"failed", "interrupted"})
