import unittest

from firstchair.fallback import Attempt, run_stage
from firstchair.provider import ProviderError


class FallbackTests(unittest.TestCase):
    def test_first_provider_succeeds_without_calling_later(self):
        called = []

        def first():
            called.append("codex")
            return "plan"

        def later():
            called.append("claude")
            return "unused"

        value, attempts = run_stage(("codex", "claude"), {"codex": first, "claude": later})
        self.assertEqual(value, "plan")
        self.assertEqual(attempts, (Attempt("codex", None),))
        self.assertEqual(called, ["codex"])

    def test_rate_limited_then_success_records_both_attempts(self):
        called = []

        def limited():
            called.append("codex")
            raise ProviderError("rate_limited")

        def succeeded():
            called.append("claude")
            return {"stage": "plan"}

        def later():
            called.append("grok")
            return "unused"

        value, attempts = run_stage(
            ("codex", "claude", "grok"),
            {"codex": limited, "claude": succeeded, "grok": later},
        )
        self.assertEqual(value, {"stage": "plan"})
        self.assertEqual(attempts, (
            Attempt("codex", "rate_limited"),
            Attempt("claude", None),
        ))
        self.assertEqual(called, ["codex", "claude"])

    def test_unavailable_and_timeout_fall_through(self):
        for code in ("provider_unavailable", "provider_timeout"):
            with self.subTest(code=code):
                called = []

                def failed():
                    called.append("codex")
                    raise ProviderError(code)

                def succeeded():
                    called.append("claude")
                    return "review"

                value, attempts = run_stage(
                    ("codex", "claude"), {"codex": failed, "claude": succeeded},
                )
                self.assertEqual(value, "review")
                self.assertEqual(attempts, (
                    Attempt("codex", code),
                    Attempt("claude", None),
                ))
                self.assertEqual(called, ["codex", "claude"])

    def test_terminal_codes_do_not_call_the_next_provider(self):
        codes = (
            "authorization_failed",
            "malformed_response",
            "unsupported_provider_version",
            "provider_exit",
            "provider_turn_failed",
            "input_limit",
            "output_limit",
            "budget_exhausted",
            "unknown_code",
        )
        for code in codes:
            with self.subTest(code=code):
                error = ProviderError(code)
                called = []

                def failed():
                    called.append("codex")
                    raise error

                def later():
                    called.append("claude")
                    return "unused"

                with self.assertRaises(ProviderError) as caught:
                    run_stage(("codex", "claude"), {"codex": failed, "claude": later})
                self.assertIs(caught.exception, error)
                self.assertEqual(str(caught.exception), code)
                self.assertEqual(called, ["codex"])

    def test_max_attempts_one_does_not_call_the_second_provider(self):
        error = ProviderError("rate_limited")
        called = []

        def failed():
            called.append("codex")
            raise error

        def later():
            called.append("claude")
            return "unused"

        with self.assertRaises(ProviderError) as caught:
            run_stage(
                ("codex", "claude"),
                {"codex": failed, "claude": later},
                max_attempts=1,
            )
        self.assertIs(caught.exception, error)
        self.assertEqual(called, ["codex"])

    def test_last_transient_failure_is_reraised(self):
        first = ProviderError("provider_timeout")
        last = ProviderError("rate_limited")
        called = []

        def fail_first():
            called.append("codex")
            raise first

        def fail_last():
            called.append("claude")
            raise last

        with self.assertRaises(ProviderError) as caught:
            run_stage(("codex", "claude"), {"codex": fail_first, "claude": fail_last})
        self.assertIs(caught.exception, last)
        self.assertEqual(called, ["codex", "claude"])

    def test_attempt_limit_stops_before_a_later_provider(self):
        second = ProviderError("provider_unavailable")
        called = []

        def fail_first():
            called.append("codex")
            raise ProviderError("rate_limited")

        def fail_second():
            called.append("claude")
            raise second

        def later():
            called.append("grok")
            return "unused"

        with self.assertRaises(ProviderError) as caught:
            run_stage(
                ("codex", "claude", "grok"),
                {"codex": fail_first, "claude": fail_second, "grok": later},
            )
        self.assertIs(caught.exception, second)
        self.assertEqual(called, ["codex", "claude"])

    def test_third_provider_succeeds_when_max_attempts_is_three(self):
        called = []

        def fail(name, code):
            def run():
                called.append(name)
                raise ProviderError(code)
            return run

        def succeeded():
            called.append("grok")
            return "synthesis"

        value, attempts = run_stage(
            ("codex", "claude", "grok"),
            {
                "codex": fail("codex", "rate_limited"),
                "claude": fail("claude", "provider_timeout"),
                "grok": succeeded,
            },
            max_attempts=3,
        )
        self.assertEqual(value, "synthesis")
        self.assertEqual(attempts, (
            Attempt("codex", "rate_limited"),
            Attempt("claude", "provider_timeout"),
            Attempt("grok", None),
        ))
        self.assertEqual(called, ["codex", "claude", "grok"])

    def test_a_provider_is_not_retried_when_attempts_remain(self):
        error = ProviderError("provider_timeout")
        called = []

        def failed():
            called.append("codex")
            raise error

        with self.assertRaises(ProviderError) as caught:
            run_stage(("codex",), {"codex": failed}, max_attempts=3)
        self.assertIs(caught.exception, error)
        self.assertEqual(called, ["codex"])

    def test_invalid_inputs_raise_value_error(self):
        called = []

        def ready():
            called.append("codex")
            return "ok"

        cases = (
            ("empty order", (), {"codex": ready}, {}),
            ("duplicate names", ("codex", "codex"), {"codex": ready}, {}),
            ("blank name", ("",), {"": ready}, {}),
            ("order not a tuple", ["codex"], {"codex": ready}, {}),
            ("missing callable", ("codex", "claude"), {"codex": ready}, {}),
            ("non-callable", ("codex",), {"codex": "not-callable"}, {}),
            ("calls not a mapping", ("codex",), None, {}),
            ("max_attempts zero", ("codex",), {"codex": ready}, {"max_attempts": 0}),
            ("max_attempts four", ("codex",), {"codex": ready}, {"max_attempts": 4}),
            ("max_attempts bool", ("codex",), {"codex": ready}, {"max_attempts": True}),
            ("max_attempts float", ("codex",), {"codex": ready}, {"max_attempts": 2.0}),
        )
        for label, order, calls, kwargs in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    run_stage(order, calls, **kwargs)
        self.assertEqual(called, [])

    def test_non_provider_error_propagates_without_the_next_provider(self):
        error = RuntimeError("boom")
        called = []

        def failed():
            called.append("codex")
            raise error

        def later():
            called.append("claude")
            return "unused"

        with self.assertRaises(RuntimeError) as caught:
            run_stage(("codex", "claude"), {"codex": failed, "claude": later})
        self.assertIs(caught.exception, error)
        self.assertEqual(called, ["codex"])
