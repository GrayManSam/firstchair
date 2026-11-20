import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


@unittest.skipUnless(os.name == "posix", "requires POSIX process and file locks")
class OrphanWorkerTests(unittest.TestCase):
    def test_synthetic_worker_exits_after_controller_sigkill(self):
        import fcntl

        # Replace the plan callback in the bundled worker, leaving its startup,
        # lifetime pipe and controller subprocess boundary intact.
        worker = """
import fcntl
import os
import time
from pathlib import Path

from firstchair import synthetic

def block(task):
    path = Path(os.environ["FIRSTCHAIR_TEST_WORKER_LOCK"])
    with path.open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path.with_suffix(".ready").touch()
        time.sleep(10)
    return task

synthetic.STAGES["plan"] = block
synthetic.main()
"""
        controller = """
import asyncio
import sys
from unittest.mock import patch

from firstchair.cli import main

spawn = asyncio.create_subprocess_exec
worker_source = sys.argv[2]

async def spawn_blocked_worker(program, module_flag, module, *args, **kwargs):
    return await spawn(program, "-c", worker_source, *args, **kwargs)

with patch("asyncio.create_subprocess_exec", spawn_blocked_worker):
    raise SystemExit(main([
        "--state-dir", sys.argv[1], "run", "--provider", "synthetic",
        "--timeout", "20", "Synthetic task",
    ]))
"""
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            lock_path = state_dir / "worker.lock"
            lock_path.touch()
            env = dict(os.environ, FIRSTCHAIR_TEST_WORKER_LOCK=str(lock_path))
            with subprocess.Popen(
                [sys.executable, "-c", controller, directory, worker],
                env=env, stdout=subprocess.DEVNULL,
            ) as process:
                try:
                    ready = lock_path.with_suffix(".ready")
                    deadline = time.monotonic() + 5
                    while not ready.exists() and time.monotonic() < deadline:
                        if process.poll() is not None:
                            break
                        time.sleep(0.01)
                    self.assertTrue(ready.exists(), "synthetic worker did not start")
                    with lock_path.open("r+") as lock:
                        with self.assertRaises(BlockingIOError):
                            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        process.kill()
                        self.assertEqual(process.wait(timeout=5), -signal.SIGKILL)
                        deadline = time.monotonic() + 3
                        while True:
                            try:
                                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                                break
                            except BlockingIOError:
                                if time.monotonic() >= deadline:
                                    self.fail("synthetic worker retained its lock after controller exit")
                                time.sleep(0.01)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait(timeout=5)
