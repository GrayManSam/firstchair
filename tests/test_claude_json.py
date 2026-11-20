import json
import unittest

from firstchair.claude_json import parse_claude_json
from firstchair.provider import ProviderError
from firstchair.usage import Reply, Usage

SUCCESS = {"type": "result", "subtype": "success", "is_error": False, "result": "Invented reply"}


def parse(result: object) -> Reply:
    return parse_claude_json(json.dumps(result).encode(), version="2.1.328", returncode=0)


class ClaudeJsonTests(unittest.TestCase):
    def test_reads_successful_text_and_ignores_unused_metadata(self):
        result = {**SUCCESS, "result": "  Invented reply.\n", "session_id": "sample-session"}
        self.assertEqual(parse(result), Reply(result["result"], Usage()))

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
            parse_claude_json(output, version="2.2.0", returncode=0)
        with self.assertRaisesRegex(ProviderError, "^provider_exit$"):
            parse_claude_json(output, version="2.1.328", returncode=1)

    def test_classifies_api_errors_on_both_exit_paths(self):
        for returncode in (0, 1):
            for status, reason in (
                (429, "rate_limited"),
                (401, "authorization_failed"),
                (403, "authorization_failed"),
                (500, "provider_exit" if returncode else "provider_turn_failed"),
            ):
                with self.subTest(returncode=returncode, status=status):
                    result = {**SUCCESS, "is_error": True, "api_error_status": status}
                    if status == 429:
                        result["api_error_code"] = "credits_required"
                    with self.assertRaisesRegex(ProviderError, f"^{reason}$"):
                        parse_claude_json(json.dumps(result).encode(), version="2.1.329", returncode=returncode)

    def test_invalid_envelope_on_failed_exit(self):
        for output in (b"\xff", b'{"type":"system","is_error":true,"api_error_status":429}'):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ProviderError, "^provider_exit$"):
                    parse_claude_json(output, version="2.1.328", returncode=1)

    def test_usage(self):
        for counts, expected in (
            ({"input_tokens": 0, "output_tokens": 3}, Usage("measured", 0, 3)),
            ({"input_tokens": 0, "output_tokens": 0}, Usage()),
            ({"output_tokens": 3}, Usage()),
        ):
            with self.subTest(counts=counts):
                self.assertEqual(parse({**SUCCESS, "usage": counts}).usage, expected)

        for counts in (None, [], {"input_tokens": -1}, {"output_tokens": True},
                       {"input_tokens": 1 << 63}, {"output_tokens": "3"}):
            with self.subTest(counts=counts):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse({**SUCCESS, "usage": counts})
