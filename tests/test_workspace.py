import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from triadmux.provider import ExecutionLimits, ProviderError, invoke


def _workspace_directories() -> set[Path]:
    roots = {Path(tempfile.gettempdir()), Path.cwd()}
    return {
        path
        for root in roots
        for path in root.glob("triadmux-workspace-*")
        if path.is_dir()
    }


class WorkspaceTests(unittest.TestCase):
    def test_invoke_runs_in_removed_workspace(self):
        script = """
import json
import os
from pathlib import Path
Path("marker").write_text("marker")
print(json.dumps({"schema_version": 1, "result": os.getcwd()}))
"""
        cwd = Path.cwd()
        marker = cwd / "marker"
        try:
            result = invoke((sys.executable, "-c", script), "task", ExecutionLimits())
            workspace = Path(result)
            self.assertTrue(workspace.name.startswith("triadmux-workspace-"))
            self.assertNotEqual(workspace.resolve(), cwd.resolve())
            self.assertFalse(workspace.exists())
            self.assertFalse(marker.exists())
        finally:
            marker.unlink(missing_ok=True)

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_timeout_stops_grandchild_without_leaving_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory, "ready")
            late = Path(directory, "late")
            escaped = Path.cwd() / "escaped"
            before = _workspace_directories()
            child = (
                "from pathlib import Path; import time; "
                f"Path({str(ready)!r}).touch(); time.sleep(1.2); "
                f"Path({str(late)!r}).touch(); Path('escaped').touch()"
            )
            leader = f"import subprocess, sys; subprocess.Popen([sys.executable, '-c', {child!r}])"
            try:
                with self.assertRaisesRegex(ProviderError, "^provider_timeout$"):
                    invoke((sys.executable, "-c", leader), "task", ExecutionLimits(0.6))
                self.assertTrue(ready.exists())
                time.sleep(0.8)
                self.assertFalse(late.exists())
                self.assertFalse(escaped.exists())
                self.assertEqual(_workspace_directories(), before)
            finally:
                escaped.unlink(missing_ok=True)
