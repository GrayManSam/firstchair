"""Parse the candidate Claude Code 2.1.328 headless text result envelope."""

from .provider import ProviderError
from .strict_json import load_json

SUPPORTED_VERSION = "2.1.328"
ERROR_SUBTYPES = (
    "error_during_execution",
    "error_max_budget_usd",
    "error_max_structured_output_retries",
    "error_max_turns",
)


def parse_claude_json(output: bytes, *, version: str, returncode: int) -> str:
    """Extract text from the already bounded stdout of one JSON-mode run."""
    if version != SUPPORTED_VERSION:
        raise ProviderError("unsupported_provider_version")
    if returncode != 0:
        raise ProviderError("provider_exit")
    try:
        result = load_json(output.decode("utf-8"))
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None
    if not isinstance(result, dict) or result.get("type") != "result":
        raise ProviderError("malformed_response")

    subtype = result.get("subtype")
    is_error = result.get("is_error")
    if is_error is True or subtype in ERROR_SUBTYPES:
        raise ProviderError("provider_turn_failed")
    if subtype != "success" or is_error is not False:
        raise ProviderError("malformed_response")
    if result.get("api_error_status") is not None or result.get("errors"):
        raise ProviderError("provider_turn_failed")

    text = result.get("result")
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("malformed_response")
    return text
