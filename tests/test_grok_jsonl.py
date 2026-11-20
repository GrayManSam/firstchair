import json
import unittest
from dataclasses import asdict, fields

from firstchair.grok_jsonl import GrokFrame, parse_grok_jsonl, validate_grok_jsonl
from firstchair.provider import ProviderError
from firstchair.usage import Reply, Usage

PROBE = {"type": "probe", "id": "fixture-0001", "unused": True}
TEXT = {"type": "text", "data": "Invented fragment", "usage": {"input_tokens": 4}}
UNKNOWN = {"type": "fixture_only_event", "note": "not a guide type"}
END = {"type": "end", "stopReason": "end_turn", "text": "Invented closing line"}
ERROR = {"type": "error", "message": "invented framing only"}


def response(*events: object) -> bytes:
    return ("\n".join(json.dumps(event) for event in events) + "\n").encode()


def validate(output: bytes) -> GrokFrame:
    return validate_grok_jsonl(output, version="1.0.77", returncode=0)


class GrokJsonlTests(unittest.TestCase):
    def test_invented_frames_keep_type_order_and_ignore_extra_fields(self):
        output = response(PROBE, TEXT, UNKNOWN, END, ERROR)
        frame = validate(output)
        self.assertIsInstance(frame, GrokFrame)
        self.assertEqual(
            frame,
            GrokFrame(5, ("probe", "text", "fixture_only_event", "end", "error")),
        )
        self.assertEqual(tuple(field.name for field in fields(frame)), ("event_count", "event_types"))
        self.assertNotIn("Invented fragment", repr(asdict(frame)))
        self.assertNotIn("Invented closing line", repr(asdict(frame)))
        self.assertNotIn("input_tokens", repr(asdict(frame)))

    def test_blank_lines_are_skipped(self):
        lines = ["", json.dumps(PROBE), "   ", json.dumps(UNKNOWN), "\t", ""]
        frame = validate("\n".join(lines).encode())
        self.assertEqual(frame, GrokFrame(2, ("probe", "fixture_only_event")))

    def test_unknown_event_types_are_accepted(self):
        frame = validate(response({"type": "zz_not_in_the_guide"}, {"type": "max_turns_reached"}))
        self.assertEqual(frame.event_types, ("zz_not_in_the_guide", "max_turns_reached"))

    def test_text_and_end_do_not_expose_reply_text(self):
        frame = validate(response(TEXT, END))
        self.assertIsInstance(frame, GrokFrame)
        self.assertEqual(asdict(frame), {"event_count": 2, "event_types": ("text", "end")})
        self.assertFalse(hasattr(frame, "text"))
        self.assertFalse(hasattr(frame, "usage"))

    def test_malformed_framing_fails_closed(self):
        cases = (
            b"\xff",
            b'{"type":"probe","type":"end"}\n',
            b'{"type":"text","n":NaN}\n',
            b'["probe"]\n',
            b'"Invented fragment"\n',
            b"null\n",
            b"{}\n",
            b'{"data":"Invented fragment"}\n',
            b'{"type":""}\n',
            b'{"type":"  "}\n',
            b'{"type":1}\n',
            b'{"type":null}\n',
            b"",
            b"\n\n",
            b" \n\t\n",
            b'{"type":"probe"}{"type":"end"}\n',
            b'{"type":\n',
        )
        for output in cases:
            with self.subTest(output=output):
                with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
                    validate(output)

    def test_requires_supported_version_and_successful_process_exit(self):
        output = response(PROBE)
        with self.assertRaisesRegex(ProviderError, "^unsupported_provider_version$"):
            validate_grok_jsonl(output, version="1.0.78", returncode=0)
        with self.assertRaisesRegex(ProviderError, "^provider_exit$"):
            validate_grok_jsonl(output, version="1.0.77", returncode=1)


class GrokReplyTests(unittest.TestCase):
    def test_joins_fragments_and_prefers_end_usage(self):
        counts = {"input_tokens": 4, "output_tokens": 2}
        output = response(
            PROBE, TEXT, UNKNOWN, {"type": "text", "data": " two"},
            {"type": "usage", "usage": {"input_tokens": 1, "output_tokens": 1}},
            {**END, "usage": counts},
        )
        self.assertEqual(
            parse_grok_jsonl(output, version="1.0.78", returncode=0),
            Reply("Invented fragment two", Usage("measured", 4, 2)),
        )

    def test_falls_back_to_last_usage_event(self):
        first = {"type": "usage", "usage": {"input_tokens": 4, "output_tokens": 2}}
        last = {"type": "usage", "usage": {"input_tokens": 5, "output_tokens": 3}}
        output = response(TEXT, first, last, END)
        self.assertEqual(parse_grok_jsonl(output, version="1.0.77", returncode=0).usage,
                         Usage("measured", 5, 3))

    def test_rejects_invalid_streams(self):
        cases = (
            ((TEXT,), "malformed_response"),
            ((TEXT, END, UNKNOWN), "malformed_response"),
            ((TEXT, END, END), "malformed_response"),
            ((TEXT, {**END, "stopReason": "max_turns"}), "provider_turn_failed"),
            ((TEXT, ERROR, END), "provider_turn_failed"),
            ((TEXT, END, ERROR), "provider_turn_failed"),
            (({"type": "text", "data": 4}, END), "malformed_response"),
            (({"type": "text", "data": " \t"}, END), "malformed_response"),
            ((TEXT, {**END, "usage": None}), "malformed_response"),
            ((TEXT, {**END, "usage": {"input_tokens": True}}), "malformed_response"),
        )
        for events, reason in cases:
            with self.subTest(events=events):
                with self.assertRaisesRegex(ProviderError, f"^{reason}$"):
                    parse_grok_jsonl(response(*events), version="1.0.77", returncode=0)

    def test_rejects_blank_lines(self):
        with self.assertRaisesRegex(ProviderError, "^malformed_response$"):
            parse_grok_jsonl(response(TEXT) + b"\n" + response(END), version="1.0.77", returncode=0)
