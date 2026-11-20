"""Parse a bounded response from a single Codex CLI 0.170.0 turn."""

from dataclasses import dataclass
from typing import Literal

from .provider import ProviderError
from .strict_json import load_json

SUPPORTED_VERSION = "0.170.0"
ITEM_EVENTS = {"item.started", "item.updated", "item.completed"}
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
MAX_TOKEN_COUNT = (1 << 63) - 1


@dataclass(frozen=True)
class CodexUsage:
    provenance: Literal["measured", "unknown"] = "unknown"
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class CodexReply:
    text: str
    usage: CodexUsage


def _parse_usage(event: dict[str, object]) -> CodexUsage:
    if "usage" not in event:
        return CodexUsage()
    usage = event["usage"]
    if not isinstance(usage, dict):
        raise ProviderError("malformed_response")
    for field in TOKEN_FIELDS:
        if field in usage:
            count = usage[field]
            if type(count) is not int or not 0 <= count <= MAX_TOKEN_COUNT:
                raise ProviderError("malformed_response")
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    # This version emits a default all-zero usage envelope without telemetry.
    if input_tokens is None or output_tokens is None or not (input_tokens or output_tokens):
        return CodexUsage()
    return CodexUsage("measured", input_tokens, output_tokens)


def parse_codex_jsonl(output: bytes, *, version: str, returncode: int) -> CodexReply:
    """Inspect stdout from an already bounded invocation and its process exit code."""
    if version != SUPPORTED_VERSION:
        raise ProviderError("unsupported_provider_version")
    if returncode != 0:
        raise ProviderError("provider_exit")

    try:
        events = [
            load_json(line)
            for line in output.decode("utf-8").split("\n")
            if line.strip()
        ]
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None

    if any(
        isinstance(event, dict) and event.get("type") in ("error", "turn.failed")
        for event in events
    ):
        raise ProviderError("provider_turn_failed")

    thread_started = False
    turn_started = False
    text = None
    usage = None
    for event in events:
        if not isinstance(event, dict) or not isinstance(kind := event.get("type"), str):
            raise ProviderError("malformed_response")
        if kind == "thread.started":
            if thread_started or not isinstance(event.get("thread_id"), str) or not event["thread_id"]:
                raise ProviderError("malformed_response")
            thread_started = True
        elif kind == "turn.started":
            if not thread_started or turn_started:
                raise ProviderError("malformed_response")
            turn_started = True
        elif kind == "turn.completed":
            if not turn_started or usage is not None:
                raise ProviderError("malformed_response")
            usage = _parse_usage(event)
        elif kind in ITEM_EVENTS:
            item = event.get("item")
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not item["id"]
                or not isinstance(item.get("type"), str)
                or not item["type"]
            ):
                raise ProviderError("malformed_response")
            if kind == "item.completed" and item["type"] == "agent_message":
                message = item.get("text")
                if not turn_started or usage is not None or not isinstance(message, str):
                    raise ProviderError("malformed_response")
                text = message
        else:
            raise ProviderError("malformed_response")

    if usage is None or text is None or not text.strip():
        raise ProviderError("malformed_response")
    return CodexReply(text, usage)
