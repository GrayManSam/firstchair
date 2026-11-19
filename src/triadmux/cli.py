"""Command-line entry point."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__
from .workflow import demo_plan, demo_review, demo_synthesize, record_path, run_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="triadmux")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--state-dir", type=Path, default=Path(".triadmux"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Discover provider executables on PATH")
    run = commands.add_parser("run", help="Run the synthetic leader/reviewer workflow")
    run.add_argument("--demo", action="store_true", required=True)
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
            result = run_workflow(
                args.task, args.state_dir, demo_plan, demo_review, demo_synthesize
            )
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
