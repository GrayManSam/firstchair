"""Version gates for the provider output contracts."""

import re
from typing import Literal

from .provider import ProviderError

VERIFIED = {
    "codex": ("0.170.0", "0.171.0"),
    "claude": ("2.1.328", "2.1.329"),
    "grok": ("1.0.77",),
}
COMPATIBLE = {
    "codex": ((0, 170, 0), (0, 180, 0)),
    "claude": ((2, 1, 328), (2, 2, 0)),
    "grok": ((1, 0, 77), (1, 1, 0)),
}

VERSION = re.compile(r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}")
VERSION_CANDIDATE = re.compile(r"(?:^|[\s(\[])([0-9]+(?:\.[0-9]+){2}[^\s()\[\]]*)")


def read_version(provider: str, output: str) -> str:
    candidates = VERSION_CANDIDATE.findall(output)
    if provider not in VERIFIED or len(candidates) != 1 or not VERSION.fullmatch(candidates[0]):
        raise ProviderError("unsupported_provider_version")
    return candidates[0]


def check_version(provider: str, version: str) -> Literal["verified", "compatible"]:
    if provider not in VERIFIED or not VERSION.fullmatch(version):
        raise ProviderError("unsupported_provider_version")
    if version in VERIFIED[provider]:
        return "verified"
    try:
        parts = tuple(int(part) for part in version.split("."))
    except ValueError:
        raise ProviderError("unsupported_provider_version") from None
    low, high = COMPATIBLE[provider]
    if low <= parts < high:
        return "compatible"
    raise ProviderError("unsupported_provider_version")
