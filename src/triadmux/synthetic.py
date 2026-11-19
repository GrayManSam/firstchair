"""Credential-free subprocess used to exercise the provider boundary."""

import json
import os
import sys
from threading import Thread

from .handoff import read_review, review_assignment, review_text
from .workflow import demo_plan, demo_synthesize


def _synthesize(review: object) -> str:
    return demo_synthesize(review_text(read_review(review)))


STAGES = {"plan": demo_plan, "review": review_assignment, "synthesize": _synthesize}


def _watch_controller(reader: int) -> None:
    # The controller writes no bytes. Its exit makes this read return EOF.
    try:
        os.read(reader, 1)
    finally:
        os._exit(1)


def main() -> None:
    if len(sys.argv) > 2:
        reader = int(sys.argv[2])
        os.set_inheritable(reader, False)
        Thread(target=_watch_controller, args=(reader,), daemon=True).start()
    request = json.load(sys.stdin)
    if (
        not isinstance(request, dict)
        or type(request.get("schema_version")) is not int
        or request["schema_version"] != 1
        or "task" not in request
    ):
        raise SystemExit("invalid synthetic request")
    stage = sys.argv[1]
    task = request["task"]
    if stage != "synthesize" and not isinstance(task, str):
        raise SystemExit("invalid synthetic task")
    result = STAGES[stage](task)
    print(json.dumps({"schema_version": 1, "result": result}))


if __name__ == "__main__":
    main()
