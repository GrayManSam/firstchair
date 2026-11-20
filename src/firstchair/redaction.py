"""Replace secret environment values before run records are stored."""

import os

_MARKERS = ("SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "API_KEY", "_KEY")
_MIN_LENGTH = 12
_REDACTED = "[redacted]"


def _is_secret_name(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in _MARKERS)


def _secret_values() -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for name, value in os.environ.items():
        if len(value) < _MIN_LENGTH or value in seen or not _is_secret_name(name):
            continue
        seen.add(value)
        values.append(value)
    values.sort(key=len, reverse=True)
    return tuple(values)


def _redact(value: object, secrets: tuple[str, ...]) -> object:
    if isinstance(value, str):
        redacted = value
        for secret in secrets:
            if secret in redacted:
                redacted = redacted.replace(secret, _REDACTED)
        return redacted
    if isinstance(value, dict):
        for key in list(value):
            value[key] = _redact(value[key], secrets)
        return value
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _redact(item, secrets)
        return value
    return value


def redact_record(record: dict[str, object]) -> dict[str, object]:
    """Replace secret environment values inside a JSON-like record."""
    secrets = _secret_values()
    if secrets:
        _redact(record, secrets)
    return record
