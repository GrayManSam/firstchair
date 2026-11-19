"""Read explicit controller configuration for synthetic runs."""

import tomllib
from pathlib import Path

TIME_LIMITS = frozenset(("timeout", "total_timeout"))
BYTE_LIMITS = frozenset(("max_input_bytes", "max_output_bytes"))


def read_synthetic_config(path: Path) -> dict[str, int | float]:
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    if set(config) != {"synthetic"} or not isinstance(config["synthetic"], dict):
        raise ValueError("configuration must contain one [synthetic] table")
    limits = config["synthetic"]
    if limits.keys() - TIME_LIMITS - BYTE_LIMITS:
        raise ValueError("unknown synthetic configuration key")
    for key, value in limits.items():
        if key in TIME_LIMITS and type(value) not in (int, float):
            raise ValueError(f"synthetic {key} must be a number")
        if key in BYTE_LIMITS and type(value) is not int:
            raise ValueError(f"synthetic {key} must be an integer")
    return limits
