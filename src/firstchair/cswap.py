"""Claude accounts managed by claude-swap (cswap), used as Firstchair seats.

claude-swap (https://github.com/realiti4/claude-swap) stores several Claude
Code logins in numbered slots and reads each one's usage. This bridge is
opt-in: with ``FIRSTCHAIR_CSWAP=1`` set and cswap installed, every slot
shows up here as a Claude profile named ``cswap-<N>``
(``cswap-1``, ``cswap-2``, ...), next to the profiles made with
``firstchair auth login``. Such a profile works anywhere a profile name
does: ``--profile cswap-2``, ``--fallback claude:cswap-3``, and the
``--rotate-accounts`` pool.

What changes for a cswap profile
--------------------------------
* **Launching.** A stage or worker on slot N runs
  ``cswap run N -- <the usual claude arguments>``. cswap points Claude Code
  at that slot's login for this one process and leaves the default login
  and other terminals alone. Since claude-swap 1.2.0, ``cswap run`` writes
  its own notices to stderr, so Claude's JSON on stdout reaches the
  Firstchair parsers unchanged. ``cswap run`` passes the prompt on stdin
  through to Claude.
* **Usage.** The 5-hour and 7-day readings come from ``cswap list --json``,
  which reports what cswap already measured. No prompt is sent, so reading
  usage costs no quota. That is unlike the ``rate_limit_event`` probe used
  for ordinary Claude profiles. A reading cswap considers too old to act on
  (``usageStatus`` other than ``ok``) counts as no reading.
* **Sign-in.** cswap owns these logins. ``firstchair auth login`` does not
  apply. Add or re-login an account with ``cswap add``, as cswap's README
  describes.

Without ``FIRSTCHAIR_CSWAP=1``, a ``cswap-N`` name is an ordinary (and
normally unknown) profile, and nothing here runs.

Version gate
------------
``cswap --version`` must report a version in :data:`VERIFIED` or within
:data:`COMPATIBLE`. 1.2.0 is the floor because earlier ``cswap run``
printed its notices on stdout, mixed into Claude's JSON. An unsupported or
unreadable version fails closed: the profile is refused, the same as an
unsupported provider version.

Firstchair never opens cswap's credential files. It only runs the ``cswap``
command, the same way it only runs ``claude``, ``codex`` and ``grok``.

One caveat. When slot N is cswap's active default login, ``cswap run N``
runs Claude on that default login, and a ``cswap auto`` switch during the
stage can move it to another account. The stage still finishes, just
possibly on a different account than the one ranked.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Sequence
from datetime import datetime

from .provider import ProviderError
from .quota import Quota, Window
from .versions import VERSION

# Profile names for cswap slots. "cswap-" plus the slot number, so the name
# also satisfies accounts.PROFILE_NAME.
PROFILE_PREFIX = "cswap-"
_PROFILE = re.compile(r"cswap-([1-9][0-9]{0,3})")

# The only provider cswap manages.
PROVIDER = "claude"

# Set to "1" to turn the bridge on.
OPT_IN_VARIABLE = "FIRSTCHAIR_CSWAP"

# Versions checked against this module (see docs/provider-contracts.md), and
# the half-open range accepted as compatible.
VERIFIED = ("1.2.0",)
COMPATIBLE = ((1, 2, 0), (1, 3, 0))

# cswap's ``list --json`` contract version this module reads. cswap only adds
# fields within a version, so a newer minor cswap still parses.
SCHEMA_VERSION = 1

# Window lengths in minutes, matching quota.py's Claude reader so the
# rotation compares cswap readings and probe readings on the same footing.
_WINDOWS = (("fiveHour", 5 * 60), ("sevenDay", 7 * 24 * 60))

# ``cswap list`` may refresh stale readings over the network before printing,
# so allow it a while. A slow answer only delays ranking; it never fails a run.
LIST_TIMEOUT_S = 45.0

# Upper bound on what ``cswap list --json`` may print, so a broken install
# cannot fill memory. A hundred accounts take well under 1 MiB.
_MAX_OUTPUT_BYTES = 1024 * 1024


def enabled() -> bool:
    """Has the user opted in with ``FIRSTCHAIR_CSWAP=1``?"""
    return os.environ.get(OPT_IN_VARIABLE) == "1"


def is_cswap_profile(provider: str, profile: str | None) -> bool:
    """Is this seat a cswap slot rather than a ``firstchair auth login`` profile?

    Only when the bridge is enabled; otherwise ``cswap-N`` is just a name.
    """
    return (
        enabled() and provider == PROVIDER and profile is not None
        and _PROFILE.fullmatch(profile) is not None
    )


def slot(profile: str) -> str:
    """The cswap slot number of a ``cswap-<N>`` profile, as a string ("3")."""
    match = _PROFILE.fullmatch(profile)
    if match is None:
        raise ValueError(f"not a cswap profile: {profile}")
    return match.group(1)


def find_cswap(env: dict[str, str] | None = None) -> str | None:
    """Absolute path of the ``cswap`` command on PATH, or None if not installed."""
    path = (env or os.environ).get("PATH")
    found = shutil.which("cswap", path=path)
    return os.path.abspath(found) if found else None


def check_version(output: str) -> str:
    """Accept ``cswap --version`` output ("cswap 1.2.0") or raise ProviderError.

    Anything other than exactly one plain X.Y.Z inside the supported range is
    refused, including local builds such as "1.0.0+local".
    """
    parts = output.split()
    if len(parts) != 2 or parts[0] != "cswap" or not VERSION.fullmatch(parts[1]):
        raise ProviderError("unsupported_provider_version")
    version = parts[1]
    if version in VERIFIED:
        return version
    numbers = tuple(int(n) for n in version.split("."))
    low, high = COMPATIBLE
    if not low <= numbers < high:
        raise ProviderError("unsupported_provider_version")
    return version


def require_cswap(env: dict[str, str] | None = None, *, timeout: float = 20.0) -> str:
    """Path of a supported cswap, or ProviderError.

    ``provider_unavailable`` when it is missing or will not answer, and
    ``unsupported_provider_version`` when it answers with a version outside
    the gate.
    """
    env = dict(env if env is not None else os.environ)
    cswap = find_cswap(env)
    if cswap is None:
        raise ProviderError("provider_unavailable")
    try:
        done = subprocess.run(
            [cswap, "--version"], env=env, capture_output=True, timeout=timeout,
            check=False, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        raise ProviderError("provider_unavailable") from None
    if done.returncode != 0:
        raise ProviderError("provider_unavailable")
    check_version(done.stdout.decode("utf-8", errors="replace").strip())
    return cswap


def environment(source: dict[str, str] | None = None) -> dict[str, str]:
    """Environment for a process on a cswap slot.

    ``CLAUDE_CONFIG_DIR`` is removed because ``cswap run`` sets it to the
    slot's own session profile. The caller removes credential overrides as
    it does for every profile.
    """
    env = dict(source if source is not None else os.environ)
    env.pop("CLAUDE_CONFIG_DIR", None)
    return env


def wrap_command(argv: Sequence[str], profile: str, cswap: str) -> list[str]:
    """Run a Claude argv on a cswap slot.

    ``argv[0]`` is the claude executable and is dropped: ``cswap run`` finds
    Claude Code itself. Everything after it is passed through untouched
    after ``--``.
    """
    return [cswap, "run", slot(profile), "--", *argv[1:]]


def _list_json(cswap: str, env: dict[str, str], timeout: float) -> dict | None:
    """Run ``cswap list --json`` and return the parsed document, or None on any failure."""
    try:
        done = subprocess.run(
            [cswap, "list", "--json"], env=env, capture_output=True,
            timeout=timeout, check=False, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0 or len(done.stdout) > _MAX_OUTPUT_BYTES:
        return None
    try:
        document = json.loads(done.stdout)
    except (ValueError, RecursionError):
        return None
    if not isinstance(document, dict) or document.get("schemaVersion") != SCHEMA_VERSION:
        return None
    return document


def _accounts(document: dict | None) -> list[dict]:
    rows = document.get("accounts") if document else None
    return [row for row in rows or [] if isinstance(row, dict) and isinstance(row.get("number"), int)]


def list_profiles(env: dict[str, str] | None = None, *, timeout: float = LIST_TIMEOUT_S) -> list[dict[str, str]]:
    """Every cswap slot as ``{"provider": "claude", "profile": "cswap-N"}``, by slot.

    Empty when cswap is not installed or cannot answer. Account e-mails are
    deliberately not returned, matching ``firstchair auth list``, which
    shows local aliases only.
    """
    if not enabled():
        return []
    env = dict(env if env is not None else os.environ)
    try:
        cswap = require_cswap(env)
    except ProviderError:
        return []
    numbers = sorted(row["number"] for row in _accounts(_list_json(cswap, env, timeout)))
    return [{"provider": PROVIDER, "profile": f"{PROFILE_PREFIX}{n}"} for n in numbers]


def _epoch(value: object) -> int | None:
    """cswap's ISO ``resetsAt`` ("2026-11-28T23:59:59.99+00:00") as whole Unix seconds."""
    if not isinstance(value, str):
        return None
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def quota_from_row(row: dict, now: float) -> Quota | None:
    """Turn one ``cswap list --json`` account row into a Firstchair Quota.

    Returns None when cswap does not consider the reading fresh enough to
    act on, or reports no window figures. ``allowed`` stays None because
    cswap reports percentages, not a verdict, so the rotation decides from
    the windows as it does for Codex.
    """
    if row.get("usageStatus") != "ok":
        return None
    usage = row.get("usage")
    if not isinstance(usage, dict):
        return None
    windows = []
    for key, minutes in _WINDOWS:
        window = usage.get(key)
        if not isinstance(window, dict):
            continue  # e.g. no five-hour window on some plans
        pct = window.get("pct")
        if not isinstance(pct, (int, float)) or isinstance(pct, bool):
            continue
        used = max(0, min(100, round(pct)))
        windows.append(Window(used, minutes, _epoch(window.get("resetsAt"))))
    if not windows:
        return None
    age = row.get("usageAgeSeconds")
    observed_at = now - age if isinstance(age, (int, float)) and age >= 0 else now
    return Quota(tuple(windows), None, observed_at)


def read_quota(profile: str, env: dict[str, str] | None = None, *, timeout: float = LIST_TIMEOUT_S) -> Quota | None:
    """Current usage of one cswap slot, from ``cswap list --json``. None if unknown."""
    if not enabled():
        return None
    env = dict(env if env is not None else os.environ)
    try:
        cswap = require_cswap(env)
    except ProviderError:
        return None
    wanted = int(slot(profile))
    for row in _accounts(_list_json(cswap, env, timeout)):
        if row["number"] == wanted:
            return quota_from_row(row, time.time())
    return None
