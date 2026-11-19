"""Run a deterministic three-stage workflow and persist its progress."""

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid4

from .provider import ProviderError

Stage = Callable[[str], str]


def record_path(state_dir: Path, run_id: str) -> Path:
    parsed = UUID(run_id)
    if str(parsed) != run_id:
        raise ValueError("run ID must be a canonical UUID")
    return state_dir / f"{parsed}.json"


def save(path: Path, record: dict[str, object]) -> None:
    stream = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    )
    temporary = Path(stream.name)
    try:
        with stream:
            json.dump(record, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_workflow(
    task: str, state_dir: Path, plan: Stage, review: Stage, synthesize: Stage
) -> dict[str, object]:
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_id = str(uuid4())
    path = record_path(state_dir, run_id)
    record: dict[str, object] = {
        "schema_version": 1, "run_id": run_id, "status": "running", "stage": "plan"
    }
    save(path, record)
    value = task
    for name, stage in (("plan", plan), ("review", review), ("synthesize", synthesize)):
        record["stage"] = name
        save(path, record)
        try:
            value = stage(value)
        except ProviderError as error:
            record.update(status="failed", error=str(error))
            save(path, record)
            return record
        except Exception:
            record.update(status="failed", error="stage_failed")
            save(path, record)
            return record
        except KeyboardInterrupt:
            record["status"] = "interrupted"
            save(path, record)
            return record
    record.update(status="completed", result=value)
    save(path, record)
    return record


def demo_plan(task: str) -> str:
    return f"Identify the acceptance criteria for: {task}"


def demo_review(assignment: str) -> str:
    return f"{assignment}\nRecord an expected result and a repeatable validation step."


def demo_synthesize(review: str) -> str:
    return f"Demo handoff\n{review}"
