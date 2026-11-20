"""Read JSON while rejecting ambiguous keys and non-JSON constants."""

import json


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("non-JSON constant")


def load_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=_json_object, parse_constant=_reject_constant)
