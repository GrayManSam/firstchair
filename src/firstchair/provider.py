"""Bounded execution for the bundled synthetic provider protocol."""

import asyncio
import json
import os
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory, TemporaryFile
from time import monotonic
from typing import BinaryIO

from .handoff import WorkerReview, read_review

MAX_TASK_BYTES = 64 * 1024


class ProviderError(Exception):
    """A stable failure code safe to persist in a workflow record."""


@dataclass(frozen=True)
class ExecutionLimits:
    timeout: float = 5.0
    output_bytes: int = 64 * 1024
    input_bytes: int = MAX_TASK_BYTES

    def __post_init__(self) -> None:
        if not 0 < self.timeout <= 60:
            raise ValueError("provider timeout must be greater than 0 and at most 60 seconds")
        if not 1 <= self.output_bytes <= 1024 * 1024:
            raise ValueError("provider output limit must be between 1 and 1048576 bytes")
        if type(self.input_bytes) is not int or not 1 <= self.input_bytes <= MAX_TASK_BYTES:
            raise ValueError(f"provider input limit must be between 1 and {MAX_TASK_BYTES} bytes")


async def _read_response(
    argv: tuple[str, ...], request: BinaryIO, limits: ExecutionLimits,
    deadline: float | None, pass_fds: tuple[int, ...],
) -> bytes:
    timeout = limits.timeout
    timeout_error = "provider_timeout"
    if deadline is not None:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise ProviderError("budget_exhausted")
        if remaining <= timeout:
            timeout = remaining
            timeout_error = "budget_exhausted"

    try:
        async with asyncio.timeout(timeout):
            return await _run_process(argv, request, limits.output_bytes, pass_fds)
    except TimeoutError:
        raise ProviderError(timeout_error) from None


_SUBPROCESS_ENV_ALLOWLIST = frozenset({
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "LANGUAGE",
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSAFEPATH",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "PYTHONNOUSERSITE",
    "PYTHONLEGACYWINDOWSSTDIO",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "LIBPATH",
})
# TRIADMUX_TEST_ is the former name. Accept it for one release.
_SUBPROCESS_ENV_PREFIXES = ("FIRSTCHAIR_TEST_", "TRIADMUX_TEST_")


def _subprocess_environment() -> dict[str, str]:
    # Pass an explicit allowlist so provider children do not inherit credentials.
    # Relative PYTHONPATH entries follow cwd. Resolve them against the controller
    # before the child starts in its workspace so imports stay the same.
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in _SUBPROCESS_ENV_ALLOWLIST or name.startswith(_SUBPROCESS_ENV_PREFIXES)
    }
    pythonpath = environment.get("PYTHONPATH")
    if pythonpath is not None:
        environment["PYTHONPATH"] = os.pathsep.join(
            entry if entry == "" or os.path.isabs(entry) else os.path.abspath(entry)
            for entry in pythonpath.split(os.pathsep)
        )
    return environment


async def _run_process(
    argv: tuple[str, ...], request: BinaryIO, output_bytes: int, pass_fds: tuple[int, ...]
) -> bytes:
    use_process_group = os.name == "posix"
    # Remove the directory only after this function has waited on the child.
    with TemporaryDirectory(prefix="firstchair-workspace-") as workspace:
        spawn = {
            "stdin": request,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL,
            "cwd": workspace,
            "start_new_session": use_process_group,
            "pass_fds": pass_fds,
            "env": _subprocess_environment(),
        }
        launch = asyncio.create_task(asyncio.create_subprocess_exec(*argv, **spawn))
        process = None
        try:
            process = await asyncio.shield(launch)
            assert process.stdout is not None
            try:
                await process.stdout.readexactly(output_bytes + 1)
            except asyncio.IncompleteReadError as end:
                # EOF alone is insufficient. A provider can close stdout before exiting.
                if await process.wait():
                    raise ProviderError("provider_exit")
                return end.partial
            raise ProviderError("output_limit")
        except BaseException as error:
            if process is None:
                if not isinstance(error, asyncio.CancelledError):
                    raise
                # Let an in-flight launch hand back the process so it can be reaped.
                try:
                    process = await launch
                except Exception:
                    raise error from None
            assert process.stdout is not None
            try:
                if use_process_group:
                    # The leader may have exited while a child still holds stdout open.
                    os.killpg(process.pid, signal.SIGKILL)
                elif process.returncode is None:
                    process.kill()
            except ProcessLookupError:
                pass
            while await process.stdout.read(65536):
                pass
            await process.wait()
            raise


def invoke(
    argv: tuple[str, ...], task: str, limits: ExecutionLimits, *,
    deadline: float | None = None, pass_fds: tuple[int, ...] = (),
) -> str:
    """Send one request over stdin and validate the single JSON result."""
    return _invoke(argv, task, limits, _read_text, deadline, pass_fds)


def _read_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text result")
    return value


def _invoke[Result](
    argv: tuple[str, ...], task: str | WorkerReview, limits: ExecutionLimits,
    decode: Callable[[object], Result], deadline: float | None, pass_fds: tuple[int, ...],
) -> Result:
    payload = json.dumps({"schema_version": 1, "task": task}, ensure_ascii=False).encode()
    if len(payload) > limits.input_bytes:
        raise ProviderError("input_limit")
    try:
        with TemporaryFile() as request:
            request.write(payload)
            request.seek(0)
            output = asyncio.run(_read_response(argv, request, limits, deadline, pass_fds))
    except OSError:
        raise ProviderError("provider_unavailable") from None

    try:
        response = json.loads(output)
        if (
            not isinstance(response, dict)
            or type(response.get("schema_version")) is not int
            or response["schema_version"] != 1
        ):
            raise ValueError("invalid result envelope")
        result = decode(response.get("result"))
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None
    if deadline is not None and monotonic() >= deadline:
        raise ProviderError("budget_exhausted")
    return result


@dataclass(frozen=True)
class SyntheticProvider:
    """Run the stages of one workflow under shared limits."""

    limits: ExecutionLimits
    total_timeout: float | None = None
    _deadline: float | None = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.total_timeout is not None:
            if not 0 < self.total_timeout <= 180:
                raise ValueError("total timeout must be greater than 0 and at most 180 seconds")
            object.__setattr__(self, "_deadline", monotonic() + self.total_timeout)

    def run(self, stage: str, task: str | WorkerReview) -> str | WorkerReview:
        argv = (sys.executable, "-m", "firstchair.synthetic", stage)
        decode = read_review if stage == "review" else _read_text
        if os.name != "posix":
            return _invoke(argv, task, self.limits, decode, self._deadline, ())
        try:
            reader, writer = os.pipe()
        except OSError:
            raise ProviderError("provider_unavailable") from None
        try:
            # Only the worker inherits the reader. Controller exit closes the writer.
            return _invoke(
                (*argv, str(reader)), task, self.limits, decode, self._deadline, (reader,),
            )
        finally:
            os.close(writer)
            os.close(reader)
