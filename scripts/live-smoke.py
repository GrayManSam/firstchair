#!/usr/bin/env python3
"""Exercise installed, authenticated provider CLIs from the host terminal."""

import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

MARKER = "TRIADMUX_SMOKE_OK"
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
        "grok", "--no-auto-update", "-p", PROMPT, "--output-format", "streaming-json",
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
    if provider == "Claude Code":
        reply = json.loads(output)
        return (
            isinstance(reply, dict)
            and reply.get("type") == "result"
            and contains_marker(reply.get("result"))
        )
    events = [json.loads(line) for line in output.splitlines() if line.strip()]
    if provider == "Codex":
        return any(
            isinstance(event, dict)
            and event.get("type") == "item.completed"
            and isinstance(item := event.get("item"), dict)
            and item.get("type") == "agent_message"
            and contains_marker(item.get("text"))
            for event in events
        )
    return any(contains_marker(event) for event in events)


def check(provider: str) -> tuple[str, bool]:
    command = COMMANDS[provider]
    if shutil.which(command[0]) is None:
        return "executable missing from PATH", False
    try:
        with tempfile.TemporaryDirectory(prefix="triadmux-live-") as directory:
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
            return "received the expected structured reply", True
    except (ValueError, RecursionError):
        return "invalid structured output", False
    return "expected reply missing", False


def main() -> int:
    with ThreadPoolExecutor(max_workers=len(COMMANDS)) as pool:
        results = list(pool.map(check, COMMANDS))
    for provider, (message, passed) in zip(COMMANDS, results, strict=True):
        print(f"{'PASS' if passed else 'FAIL'} {provider} - {message}")
    return int(not all(passed for _, passed in results))


if __name__ == "__main__":
    raise SystemExit(main())
