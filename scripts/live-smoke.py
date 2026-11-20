#!/usr/bin/env python3
"""Exercise installed, authenticated provider CLIs from the host terminal."""

import argparse
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MARKER = "FIRSTCHAIR_SMOKE_OK"
PROMPT = f"Reply with exactly {MARKER}. Do not use any tools."
TIMEOUT = 90

COMMANDS = {
    "Codex": (
        "codex", "--ask-for-approval", "never", "exec", "--ephemeral",
        "--skip-git-repo-check", "--sandbox", "read-only", "--json", PROMPT,
    ),
    "Claude Code": (
        "claude", "-p", PROMPT, "--tools", "", "--setting-sources", "",
        "--no-session-persistence", "--output-format", "json",
    ),
    "Grok Build": (
        "grok", "--no-auto-update", "-p", PROMPT, "--output-format", "plain",
    ),
}


def contains_marker(value: object) -> bool:
    if isinstance(value, str):
        return value.strip() == MARKER
    if isinstance(value, dict):
        return any(contains_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_marker(item) for item in value)
    return False


def has_reply(provider: str, output: str) -> bool:
    if provider == "Grok Build":
        return output.strip() == MARKER
    if provider == "Claude Code":
        reply = json.loads(output)
        return (
            isinstance(reply, dict)
            and reply.get("type") == "result"
            and contains_marker(reply.get("result"))
        )
    events = [json.loads(line) for line in output.splitlines() if line.strip()]
    return any(
        isinstance(event, dict)
        and event.get("type") == "item.completed"
        and isinstance(item := event.get("item"), dict)
        and item.get("type") == "agent_message"
        and contains_marker(item.get("text"))
        for event in events
    )


def check(provider: str) -> tuple[str, bool]:
    command = COMMANDS[provider]
    if shutil.which(command[0]) is None:
        return "executable missing from PATH", False
    try:
        with tempfile.TemporaryDirectory(prefix="firstchair-live-") as directory:
            result = subprocess.run(
                command, cwd=directory, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, errors="replace", timeout=TIMEOUT,
            )
    except subprocess.TimeoutExpired:
        return f"timed out after {TIMEOUT} seconds", False
    except OSError as error:
        return f"could not start (OS error {error.errno})", False

    if result.returncode:
        diagnostic = result.stderr.casefold()
        if "read-only file system" in diagnostic:
            return "startup failed on a read-only filesystem", False
        if "bwrap" in diagnostic:
            return "Linux sandbox could not initialize", False
        return f"exited with code {result.returncode}", False
    try:
        if has_reply(provider, result.stdout):
            return "received the expected reply", True
    except (ValueError, RecursionError):
        return "invalid structured output", False
    return "expected reply missing", False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path(".firstchair/live-smoke.json"))
    parser.add_argument("--provider", choices=COMMANDS, help="Run just one provider")
    args = parser.parse_args()
    providers = (args.provider,) if args.provider else tuple(COMMANDS)
    with ThreadPoolExecutor(max_workers=len(providers)) as pool:
        results = list(pool.map(check, providers))
    report = {}
    for provider, (message, passed) in zip(providers, results, strict=True):
        print(f"{'PASS' if passed else 'FAIL'} {provider} - {message}")
        report[provider] = {"passed": passed, "message": message}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return int(not all(passed for _, passed in results))


if __name__ == "__main__":
    raise SystemExit(main())
