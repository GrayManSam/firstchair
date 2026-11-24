"""Parse the Claude Code headless text result envelope."""

import json
import time
from dataclasses import replace

from .provider import ProviderError
from .quota import parse_claude_stream
from .strict_json import load_json
from .usage import Reply, parse_usage
from .versions import check_version

SUPPORTED_VERSION = "2.1.328"
ERROR_SUBTYPES = (
    "error_during_execution",
    "error_max_budget_usd",
    "error_max_structured_output_retries",
    "error_max_turns",
)


def parse_claude_json(output: bytes, *, version: str, returncode: int) -> Reply:
    """Extract a reply from the already bounded stdout of one JSON-mode run."""
    check_version("claude", version)
    invalid_result = "provider_exit" if returncode != 0 else "malformed_response"
    try:
        result = load_json(output.decode("utf-8"))
    except (ValueError, RecursionError):
        raise ProviderError(invalid_result) from None
    if not isinstance(result, dict) or result.get("type") != "result":
        raise ProviderError(invalid_result)

    if result.get("is_error") is True:
        status = result.get("api_error_status")
        if status == 429:
            raise ProviderError("rate_limited")
        if status in (401, 403):
            raise ProviderError("authorization_failed")
    if returncode != 0:
        raise ProviderError("provider_exit")

    subtype = result.get("subtype")
    is_error = result.get("is_error")
    if is_error is True or subtype in ERROR_SUBTYPES:
        raise ProviderError("provider_turn_failed")
    if subtype != "success" or is_error is not False:
        raise ProviderError("malformed_response")
    if result.get("api_error_status") is not None or result.get("errors"):
        raise ProviderError("provider_turn_failed")

    text = result.get("result")
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("malformed_response")
    return Reply(text, parse_usage(result))


def parse_claude_stream_reply(output: bytes, *, version: str, returncode: int) -> Reply:
    """Extract a reply from one ``stream-json`` run.

    The last ``result`` line is the same envelope JSON mode prints, and it is
    held to the same rules. A ``rate_limit_event`` in the stream adds the
    account's real usage. Output with no result line is judged as a whole,
    so a single JSON-mode envelope is still accepted.
    """
    envelope = output
    for line in reversed(output.splitlines()):
        try:
            message = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(message, dict) and message.get("type") == "result":
            envelope = line
            break
    reply = parse_claude_json(envelope, version=version, returncode=returncode)
    try:
        return replace(reply, quota=parse_claude_stream(output, time.time()))
    except ValueError:
        return reply
