"""Bounded execution for the bundled synthetic provider protocol."""

import asyncio
import json
import math
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from tempfile import TemporaryFile
from typing import BinaryIO

MAX_TASK_BYTES = 64 * 1024


class ProviderError(Exception):
    """A stable failure code safe to persist in a workflow record."""


@dataclass(frozen=True)
class ExecutionLimits:
    timeout: float = 5.0
    output_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        if not math.isfinite(self.timeout) or not 0 < self.timeout <= 60:
            raise ValueError("provider timeout must be greater than 0 and at most 60 seconds")
        if not 1 <= self.output_bytes <= 1024 * 1024:
            raise ValueError("provider output limit must be between 1 and 1048576 bytes")


async def _read_response(
    argv: tuple[str, ...], request: BinaryIO, limits: ExecutionLimits
) -> bytes:
    use_process_group = os.name == "posix"
    process = await asyncio.create_subprocess_exec(
        *argv, stdin=request, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        start_new_session=use_process_group,
    )
    assert process.stdout is not None
    try:
        async with asyncio.timeout(limits.timeout):
            try:
                await process.stdout.readexactly(limits.output_bytes + 1)
            except asyncio.IncompleteReadError as end:
                # EOF alone is insufficient. A provider can close stdout before exiting.
                if await process.wait():
                    raise ProviderError("provider_exit")
                return end.partial
            raise ProviderError("output_limit")
    except BaseException:
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


def invoke(argv: tuple[str, ...], task: str, limits: ExecutionLimits) -> str:
    """Send one request over stdin and validate the single JSON result."""
    payload = json.dumps({"schema_version": 1, "task": task}, ensure_ascii=False).encode()
    if len(payload) > MAX_TASK_BYTES:
        raise ProviderError("input_limit")
    try:
        with TemporaryFile() as request:
            request.write(payload)
            request.seek(0)
            output = asyncio.run(_read_response(argv, request, limits))
    except TimeoutError:
        raise ProviderError("provider_timeout") from None
    except OSError:
        raise ProviderError("provider_unavailable") from None

    try:
        response = json.loads(output)
    except (ValueError, RecursionError):
        raise ProviderError("malformed_response") from None
    if (
        not isinstance(response, dict)
        or type(response.get("schema_version")) is not int
        or response["schema_version"] != 1
        or not isinstance(response.get("result"), str)
        or not response["result"].strip()
    ):
        raise ProviderError("malformed_response")
    return response["result"]


@dataclass(frozen=True)
class SyntheticProvider:
    limits: ExecutionLimits

    def run(self, stage: str, task: str) -> str:
        return invoke((sys.executable, "-m", "triadmux.synthetic", stage), task, self.limits)
