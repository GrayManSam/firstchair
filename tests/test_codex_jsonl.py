import json
import unittest

from triadmux.codex_jsonl import CodexReply, CodexUsage, parse_codex_jsonl
from triadmux.provider import ProviderError

THREAD_STARTED = {"type": "thread.started", "thread_id": "00000000-0000-4000-8000-000000000001"}
TURN_STARTED = {"type": "turn.started"}
AGENT_MESSAGE = {
    "type": "item.completed",
    "item": {"id": "item_1", "type": "agent_message", "text": "Invented reply"},
}
TURN_COMPLETED = {"type": "turn.completed"}


def response(*events: object) -> bytes:
    return ("\n".join(json.dumps(event) for event in events) + "\n").encode()


def parse(output: bytes) -> CodexReply:
    return parse_codex_jsonl(output, version="0.170.0", returncode=0)


class CodexJsonlTests(unittest.TestCase):
    def test_returns_last_completed_agent_message_with_measured_usage(self):
        warning = {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "error", "message": "Invented warning"},
        }
        reply = {
            "type": "item.completed",
            "item": {"id": "item_2", "type": "agent_message", "text": "Final invented reply"},
        }
        completion = {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 12,
                "cached_input_tokens": 1,
                "cache_write_input_tokens": 0,
                "output_tokens": 3,
                "reasoning_output_tokens": 0,
            },
        }
        output = response(THREAD_STARTED, TURN_STARTED, warning, AGENT_MESSAGE, reply, completion)
        self.assertEqual(parse(output), CodexReply("Final invented reply", CodexUsage("measured", 12, 3)))

    def test_missing_and_ambiguous_usage_are_unknown(self):
        completions = (
            TURN_COMPLETED,
            {**TURN_COMPLETED, "usage": {"output_tokens": 3}},
            {**TURN_COMPLETED, "usage": {"input_tokens": 0, "output_tokens": 0}},
        )
        for completion in completions:
            with self.subTest(completion=completion):
                output = response(THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, completion)
                self.assertEqual(parse(output).usage, CodexUsage())

    def test_malformed_token_counts_fail_closed(self):
        for usage in (
            [],
            None,
            {"output_tokens": True},
            {"input_tokens": -1},
            {"cached_input_tokens": 0.5},
            {"cache_write_input_tokens": 1 << 63},
            {"reasoning_output_tokens": "4"},
        ):
            with self.subTest(usage=usage):
                completion = {**TURN_COMPLETED, "usage": usage}
                output = response(THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, completion)
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse(output)

    def test_failure_events_override_a_successful_turn(self):
        for failure in (
            {"type": "turn.failed", "error": {"message": "private generated detail"}},
            {"type": "error", "message": "private generated detail"},
        ):
            for events in (
                (THREAD_STARTED, TURN_STARTED, failure, AGENT_MESSAGE, TURN_COMPLETED),
                (THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, TURN_COMPLETED, failure),
            ):
                with self.subTest(kind=failure["type"], is_last=events[-1] is failure):
                    with self.assertRaisesRegex(ProviderError, "^provider_turn_failed$"):
                        parse(response(*events))

    def test_requires_ordered_single_turn_and_completed_nonblank_reply(self):
        blank = {**AGENT_MESSAGE, "item": {**AGENT_MESSAGE["item"], "text": " \n"}}
        cases = (
            (THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE),
            (THREAD_STARTED, AGENT_MESSAGE, TURN_COMPLETED),
            (THREAD_STARTED, TURN_STARTED, TURN_COMPLETED, AGENT_MESSAGE),
            (THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, TURN_COMPLETED, TURN_COMPLETED),
            (THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, blank, TURN_COMPLETED),
            (THREAD_STARTED, TURN_STARTED, TURN_COMPLETED),
        )
        for events in cases:
            with self.subTest(events=events):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse(response(*events))

    def test_invalid_lines_and_unknown_event_types_are_rejected(self):
        output = response(THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, TURN_COMPLETED)
        for tail in (
            b"\xff\n",
            b'"private generated detail"\n',
            b'{"type":"turn.new"}\n',
            b'{"type":"error","type":"ignored"}\n',
            b'{"type":"turn.completed","usage":{"input_tokens":NaN}}\n',
            b'{"type":\n',
        ):
            with self.subTest(tail=tail):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    parse(output + tail)

    def test_requires_supported_version_and_successful_process_exit(self):
        output = response(THREAD_STARTED, TURN_STARTED, AGENT_MESSAGE, TURN_COMPLETED)
        with self.assertRaisesRegex(ProviderError, "^unsupported_provider_version$"):
            parse_codex_jsonl(output, version="0.170.1", returncode=0)
        with self.assertRaisesRegex(ProviderError, "^provider_exit$"):
            parse_codex_jsonl(output, version="0.170.0", returncode=1)
