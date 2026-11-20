import json
import unittest
from dataclasses import asdict, fields

from firstchair.grok_jsonl import GrokFrame, validate_grok_jsonl
from firstchair.provider import ProviderError

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
