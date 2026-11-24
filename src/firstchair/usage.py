"""Normalized provider replies and token telemetry."""

from dataclasses import dataclass
from typing import Literal

from .provider import ProviderError
from .quota import Quota

MAX_TOKEN_COUNT = (1 << 63) - 1
TOKEN_FIELDS = ("input_tokens", "output_tokens")


@dataclass(frozen=True)
class Usage:
    provenance: Literal["measured", "unknown"] = "unknown"
    input_tokens: int | None = None
    output_tokens: int | None = None

    def as_record(self) -> dict[str, object]:
        return {
            "provenance": self.provenance,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass(frozen=True)
class Reply:
    text: str
    usage: Usage
    # The account's real usage, when the provider reported it with this reply.
    quota: Quota | None = None


def parse_usage(event: dict[str, object], *, extra_fields: tuple[str, ...] = ()) -> Usage:
    if "usage" not in event:
        return Usage()
    usage = event["usage"]
    if not isinstance(usage, dict):
        raise ProviderError("malformed_response")
    for field in TOKEN_FIELDS + extra_fields:
        if field in usage:
            count = usage[field]
            if type(count) is not int or not 0 <= count <= MAX_TOKEN_COUNT:
                raise ProviderError("malformed_response")
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if input_tokens is None or output_tokens is None or not (input_tokens or output_tokens):
        return Usage()
    return Usage("measured", input_tokens, output_tokens)
