"""Report provider discovery and readiness without starting provider processes."""

import shutil

LIVE_PROVIDERS = ("codex", "claude", "grok")
OFFLINE_MODES = ("demo", "synthetic")


def provider_inventory() -> dict[str, dict[str, str | bool | None]]:
    """Describe the bundled provider and the live executables found on PATH."""
    providers: dict[str, dict[str, str | bool | None]] = {}
    for provider in LIVE_PROVIDERS:
        executable = shutil.which(provider)
        providers[provider] = {
            "executable": executable,
            "auth": "unchecked",
            "discovery": "installed" if executable else "missing",
            "readiness": "unverified" if executable else "missing",
            "enabled": False,
        }
    providers["synthetic"] = {
        "executable": None,
        "auth": "not_required",
        "discovery": "bundled",
        "readiness": "ready",
        "enabled": True,
    }
    return providers


def routing_explanation(selected: str) -> dict[str, str]:
    """Explain the explicit offline selection without discovering executables."""
    if selected not in OFFLINE_MODES:
        raise ValueError("routing requires an offline mode")
    reasons = {
        mode: "selected" if mode == selected else "requires_explicit_selection"
        for mode in OFFLINE_MODES
    }
    reasons.update(dict.fromkeys(LIVE_PROVIDERS, "adapter_unavailable"))
    return reasons
