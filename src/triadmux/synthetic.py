"""Credential-free subprocess used to exercise the provider boundary."""

import json
import sys

from .workflow import demo_plan, demo_review, demo_synthesize

STAGES = {"plan": demo_plan, "review": demo_review, "synthesize": demo_synthesize}


def main() -> None:
    request = json.load(sys.stdin)
    result = STAGES[sys.argv[1]](request["task"])
    print(json.dumps({"schema_version": 1, "result": result}))


if __name__ == "__main__":
    main()
