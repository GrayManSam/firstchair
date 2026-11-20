import json
import os
import tempfile
import unittest
from pathlib import Path

from firstchair.workflow import demo_plan, record_path, run_workflow


def _contains(secret: str, value: object) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, dict):
        return any(_contains(secret, item) for item in value.values())
    if isinstance(value, list):
        return any(_contains(secret, item) for item in value)
    return False


class RedactionTests(unittest.TestCase):
    def test_secret_is_absent_from_returned_record_and_saved_json(self):
        name = "XAI_API_KEY"
        previous = os.environ.get(name)
        secret = "xai-test-secret-value"
        os.environ[name] = secret
        try:
            def passthrough(value):
                return value

            with tempfile.TemporaryDirectory() as directory:
                state_dir = Path(directory)
                record = run_workflow(secret, state_dir, passthrough, passthrough, passthrough)
                saved = record_path(state_dir, record["run_id"]).read_text(encoding="utf-8")
                self.assertGreaterEqual(len(secret), 12)
                self.assertIn("[redacted]", record["result"])
                self.assertIn("[redacted]", saved)
                self.assertFalse(_contains(secret, record))
                self.assertFalse(secret in saved)
                self.assertFalse(secret in json.dumps(record))
        finally:
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous

    def test_short_secret_is_left_unchanged(self):
        name = "XAI_API_KEY"
        previous = os.environ.get(name)
        secret = "shortsecret"
        os.environ[name] = secret
        try:
            def passthrough(value):
                return value

            with tempfile.TemporaryDirectory() as directory:
                state_dir = Path(directory)
                record = run_workflow(secret, state_dir, passthrough, passthrough, passthrough)
                saved = record_path(state_dir, record["run_id"]).read_text(encoding="utf-8")
                self.assertLess(len(secret), 12)
                self.assertNotIn("[redacted]", record["result"])
                self.assertNotIn("[redacted]", saved)
                self.assertTrue(record["result"] == secret)
                self.assertTrue(json.loads(saved)["result"] == secret)
        finally:
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous

    def test_demo_plan_result_without_secret_is_unchanged(self):
        name = "XAI_API_KEY"
        previous = os.environ.get(name)
        secret = "xai-test-secret-value"
        os.environ[name] = secret
        try:
            def passthrough(value):
                return value

            task = "Review the project README"
            expected = demo_plan(task)
            with tempfile.TemporaryDirectory() as directory:
                state_dir = Path(directory)
                record = run_workflow(task, state_dir, demo_plan, passthrough, passthrough)
                saved = record_path(state_dir, record["run_id"]).read_text(encoding="utf-8")
                self.assertIn("Identify the acceptance criteria for:", record["result"])
                self.assertNotIn("[redacted]", record["result"])
                self.assertNotIn("[redacted]", saved)
                self.assertTrue(record["result"] == expected)
                self.assertTrue(json.loads(saved)["result"] == expected)
                self.assertFalse(secret in record["result"])
        finally:
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous
