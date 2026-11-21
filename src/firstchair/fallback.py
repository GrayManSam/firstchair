"""Eligible-provider fallback for one stage."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TypeVar

from .provider import ProviderError

T = TypeVar("T")

_TRANSIENT_CODES = frozenset({
    "rate_limited",
    "provider_unavailable",
    "provider_timeout",
})


def is_transient(code: str) -> bool:
    """True when another named provider may take over the unfinished stage."""
    return code in _TRANSIENT_CODES


@dataclass(frozen=True)
class Attempt:
    provider: str
    error: str | None  # None when that provider succeeded


def run_stage(
    order: tuple[str, ...],
    calls: Mapping[str, Callable[[], T]],
    *,
    max_attempts: int = 2,
) -> tuple[T, tuple[Attempt, ...]]:
    """Try providers in order until one returns or the failure is terminal.

    max_attempts counts tries and must be an int from 1 through 3.
    order must be a non-empty tuple of unique non-empty strings.
    Each name in order must have a callable in calls.
    A provider is never retried.
    On success, return (value, attempts) with one Attempt per try.
    On a non-transient ProviderError, or when attempts or the list run out,
    re-raise that ProviderError. Do not catch other exceptions.
    """
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError("max_attempts must be an int from 1 through 3")
    if type(order) is not tuple or not order:
        raise ValueError("order must be a non-empty tuple of unique non-empty strings")
    seen: set[str] = set()
    for name in order:
        if type(name) is not str or not name or name in seen:
            raise ValueError("order must be a non-empty tuple of unique non-empty strings")
        seen.add(name)
    if not isinstance(calls, Mapping):
        raise ValueError("each provider in order must have a callable")
    for name in order:
        if not callable(calls.get(name)):
            raise ValueError("each provider in order must have a callable")

    attempts: list[Attempt] = []
    chosen = order[:max_attempts]
    for index, name in enumerate(chosen):
        try:
            value = calls[name]()
        except ProviderError as error:
            code = str(error)
            attempts.append(Attempt(name, code))
            if not is_transient(code) or index + 1 == len(chosen):
                raise
        else:
            attempts.append(Attempt(name, None))
            return value, tuple(attempts)
    raise RuntimeError("fallback order was empty")
