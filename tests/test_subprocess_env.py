import os
import sys
import unittest

from firstchair.provider import ExecutionLimits, invoke


_SECRET_NAMES = ("XAI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HOME")
_EXACT_ALLOWLIST = frozenset({
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
_TEST_PREFIXES = ("FIRSTCHAIR_TEST_", "TRIADMUX_TEST_")


def _allowed(name: str) -> bool:
    return name in _EXACT_ALLOWLIST or name.startswith(_TEST_PREFIXES)


class SubprocessEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.secret = "invented-provider-secret"
        names = (
            *_SECRET_NAMES,
            "FIRSTCHAIR_TEST_MARKER",
            "FIRSTCHAIR_TEST_WORKER_LOCK",
        )
        self._saved = {name: os.environ.get(name) for name in names}
        for name in _SECRET_NAMES:
            os.environ[name] = self.secret
        os.environ["FIRSTCHAIR_TEST_MARKER"] = "present"
        os.environ["FIRSTCHAIR_TEST_WORKER_LOCK"] = "worker-lock"

    def tearDown(self):
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_provider_child_receives_allowlisted_names_only(self):
        script = """
import json
import os
print(json.dumps({
    "schema_version": 1,
    "result": ",".join(sorted(os.environ)),
}))
"""
        result = invoke((sys.executable, "-c", script), "task", ExecutionLimits())
        keys = set(result.split(","))
        self.assertTrue(keys)
        self.assertTrue(all(_allowed(name) for name in keys))
        self.assertIn("FIRSTCHAIR_TEST_MARKER", keys)
        self.assertIn("FIRSTCHAIR_TEST_WORKER_LOCK", keys)
        for name in _SECRET_NAMES:
            self.assertNotIn(name, keys)
        self.assertNotIn(self.secret, result)

    def test_relative_pythonpath_keeps_empty_entries(self):
        raw = os.pathsep.join(("relative-entry", "", os.path.abspath("abs-entry")))
        previous = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = raw
        script = """
import json
import os
print(json.dumps({"schema_version": 1, "result": os.environ["PYTHONPATH"]}))
"""
        try:
            result = invoke((sys.executable, "-c", script), "task", ExecutionLimits())
            self.assertEqual(
                result,
                os.pathsep.join((
                    os.path.abspath("relative-entry"),
                    "",
                    os.path.abspath("abs-entry"),
                )),
            )
            self.assertEqual(os.environ["PYTHONPATH"], raw)
            self.assertNotIn(self.secret, result)
        finally:
            if previous is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous
