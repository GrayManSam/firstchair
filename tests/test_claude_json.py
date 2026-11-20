import json
import unittest

from firstchair.claude_json import parse_claude_json
from firstchair.provider import ProviderError

SUCCESS = {"type": "result", "subtype": "success", "is_error": False, "result": "Invented reply"}


def parse(result: object) -> str:
    return parse_claude_json(json.dumps(result).encode(), version="2.1.328", returncode=0)


class ClaudeJsonTests(unittest.TestCase):
    def test_reads_successful_text_and_ignores_unused_metadata(self):
        result = {**SUCCESS, "result": "  Invented reply.\n", "session_id": "sample-session"}
        self.assertEqual(parse(result), result["result"])

    def test_runtime_failure_even_with_text(self):
        cases = (
            {"is_error": True, "errors": ["invented diagnostic"]},
            {"subtype": "error_during_execution"},
            {"subtype": "error_max_turns"},
            {"subtype": "error_max_budget_usd"},
            {"subtype": "error_max_structured_output_retries"},
            {"api_error_status": 401},
            {"errors": ["invented diagnostic"]},
        )
        for failure in cases:
            with self.subTest(fields=failure):
                with self.assertRaisesRegex(ProviderError, "^provider_turn_failed$"):
                    parse({**SUCCESS, **failure})

    def test_requires_success_status_and_nonblank_text(self):
        cases = (
            {"type": "result", "result": "Invented smoke reply"},
            {**SUCCESS, "type": "system"},
            {**SUCCESS, "subtype": "new_subtype"},
            {**SUCCESS, "is_error": 0},
            {**SUCCESS, "result": " \n"},
            {**SUCCESS, "result": {"text": "Invented nested reply"}},
            {**SUCCESS, "result": None, "structured_output": {"answer": "Invented data"}},
            [SUCCESS],
        )
        for result in cases:
            with self.subTest(result=result):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse(result)

    def test_prohibits_invalid_json_and_multiple_objects(self):
        cases = (
            b"\xff",
            b'{"type":"result","subtype":"success","is_error":true,"is_error":false,"result":"test"}',
            b'{"type":"result","subtype":"success","is_error":false,"result":"test","usage":NaN}',
            b"{}\n{}",
        )
        for output in cases:
            with self.subTest(output=output):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse_claude_json(output, version="2.1.328", returncode=0)

    def test_requires_supported_version_and_successful_process_exit(self):
        output = json.dumps(SUCCESS).encode()
        with self.assertRaisesRegex(ProviderError, "^unsupported_provider_version$"):
            parse_claude_json(output, version="2.1.329", returncode=0)
        with self.assertRaisesRegex(ProviderError, "^provider_exit$"):
            parse_claude_json(output, version="2.1.328", returncode=1)
