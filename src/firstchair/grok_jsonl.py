"""Validate Grok Build 1.0.77 streaming-json framing without accepting a result."""

from dataclasses import dataclass

from .provider import ProviderError
from .strict_json import load_json

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

    try:
        events = [
            load_json(line)
            for line in output.decode("utf-8").split("\n")
            if line.strip()
        ]
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None

    kinds: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            raise ProviderError("malformed_response")
        kind = event.get("type")
        if not isinstance(kind, str) or not kind.strip():
            raise ProviderError("malformed_response")
        kinds.append(kind)
    if not kinds:
        raise ProviderError("malformed_response")
    return GrokFrame(len(kinds), tuple(kinds))
