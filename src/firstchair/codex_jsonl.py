"""Parse a bounded response from a single Codex CLI turn."""

from .provider import ProviderError
from .strict_json import load_json
from .usage import Reply, Usage, parse_usage
from .versions import check_version

SUPPORTED_VERSION = "0.170.0"
ITEM_EVENTS = {"item.started", "item.updated", "item.completed"}
EXTRA_TOKEN_FIELDS = (
    "cached_input_tokens",
    "cache_write_input_tokens",
    "reasoning_output_tokens",
)

CodexUsage = Usage
CodexReply = Reply


def parse_codex_jsonl(output: bytes, *, version: str, returncode: int) -> Reply:
    """Inspect stdout from an already bounded invocation and its process exit code."""
    check_version("codex", version)
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
            usage = parse_usage(event, extra_fields=EXTRA_TOKEN_FIELDS)
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
    return Reply(text, usage)
