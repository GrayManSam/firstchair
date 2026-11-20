"""Inspect bounded Grok Build streaming-json output."""

from dataclasses import dataclass

from .provider import ProviderError
from .strict_json import load_json
from .usage import Reply, parse_usage
from .versions import check_version

SUPPORTED_VERSION = "1.0.77"


@dataclass(frozen=True)
class GrokFrame:
    event_count: int
    event_types: tuple[str, ...]


def validate_grok_jsonl(output: bytes, *, version: str, returncode: int) -> GrokFrame:
    """Check type-tagged JSONL from an already bounded invocation."""
    if version != SUPPORTED_VERSION:
        raise ProviderError("unsupported_provider_version")
    if returncode != 0:
        raise ProviderError("provider_exit")

    events = _read_events(output, allow_blank_lines=True)
    return GrokFrame(len(events), tuple(event["type"] for event in events))


def _read_events(output: bytes, *, allow_blank_lines: bool) -> list[dict]:
    try:
        events = [
            load_json(line)
            for line in output.decode("utf-8").removesuffix("\n").split("\n")
            if not allow_blank_lines or line.strip()
        ]
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None

    if not events:
        raise ProviderError("malformed_response")
    for event in events:
        if not isinstance(event, dict):
            raise ProviderError("malformed_response")
        kind = event.get("type")
        if not isinstance(kind, str) or not kind.strip():
            raise ProviderError("malformed_response")
    return events


def parse_grok_jsonl(output: bytes, *, version: str, returncode: int) -> Reply:
    """Extract a reply from one successful, already bounded invocation."""
    check_version("grok", version)
    if returncode != 0:
        raise ProviderError("provider_exit")
    events = _read_events(output, allow_blank_lines=False)
    if any(event["type"] == "error" for event in events):
        raise ProviderError("provider_turn_failed")
    ends = [event for event in events if event["type"] == "end"]
    if len(ends) != 1 or ends[0] is not events[-1]:
        raise ProviderError("malformed_response")
    end = ends[0]
    if end.get("stopReason") != "end_turn":
        raise ProviderError("provider_turn_failed")

    fragments: list[str] = []
    usage_event = {}
    for event in events:
        if event["type"] == "text":
            fragment = event.get("data")
            if not isinstance(fragment, str):
                raise ProviderError("malformed_response")
            fragments.append(fragment)
        elif event["type"] == "usage":
            usage_event = event
    text = "".join(fragments)
    if not text.strip():
        raise ProviderError("malformed_response")
    return Reply(text, parse_usage(end if "usage" in end else usage_event))
