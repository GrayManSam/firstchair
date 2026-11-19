"""Run a deterministic three-stage workflow and persist its progress."""

import json
import os
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

from .handoff import WorkerReview, review_assignment, review_text
from .provider import ProviderError
from .redaction import redact_record


def record_path(state_dir: Path, run_id: str) -> Path:
    parsed = UUID(run_id)
    if str(parsed) != run_id:
        raise ValueError("run ID must be a canonical UUID")
    return state_dir / f"{parsed}.json"


def save(path: Path, record: dict[str, object]) -> None:
    redact_record(record)
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


@contextmanager
def _run_lock(path: Path, *, create: bool) -> Iterator[None]:
    if os.name != "posix":
        if not create:
            raise ValueError("run recovery requires POSIX file locking")
        yield
        return

    import fcntl

    # Keep the lock inode stable across atomic replacements of the JSON record.
    lock_path = path.with_suffix(".lock")
    flags = os.O_RDWR | (os.O_CREAT | os.O_EXCL if create else 0)
    try:
        lock = os.open(lock_path, flags, 0o600)
    except FileNotFoundError:
        if create:
            raise
        raise ValueError("run has no recovery lock") from None
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("run is locked by another controller") from None
        yield
    finally:
        os.close(lock)


def recover_workflow(state_dir: Path, run_id: str) -> dict[str, object]:
    """Mark an abandoned run interrupted without replaying its work."""
    path = record_path(state_dir, run_id)
    with _run_lock(path, create=False):
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(record, dict)
            or type(record.get("schema_version")) is not int
            or record["schema_version"] != 1
            or record.get("run_id") != run_id
        ):
            raise ValueError("invalid or unsupported run record")
        if record.get("status") != "running":
            raise ValueError("only running records can be recovered")
        record.update(status="interrupted", error="controller_crash")
        save(path, record)
        return record


def run_workflow[Review: (str, WorkerReview)](
    task: str, state_dir: Path,
    plan: Callable[[str], str], review: Callable[[str], Review], synthesize: Callable[[Review], str],
) -> dict[str, object]:
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_id = str(uuid4())
    path = record_path(state_dir, run_id)
    with _run_lock(path, create=True):
        return _run_stages(path, run_id, task, plan, review, synthesize)


def _run_stages[Review: (str, WorkerReview)](
    path: Path, run_id: str, task: str,
    plan: Callable[[str], str], review: Callable[[str], Review], synthesize: Callable[[Review], str],
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "stage": "plan",
        "usage": {
            "provenance": "unknown",
            "input_tokens": None,
            "output_tokens": None,
        },
    }
    save(path, record)
    value: str | WorkerReview = task
    worker_review = None
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
        if name == "review" and isinstance(value, dict):
            worker_review = value
    record.update(status="completed", result=value)
    if worker_review is not None:
        record["worker_review"] = worker_review
    save(path, record)
    return record


def demo_plan(task: str) -> str:
    return f"Identify the acceptance criteria for: {task}"


def demo_review(assignment: str) -> str:
    return review_text(review_assignment(assignment))


def demo_synthesize(review: str) -> str:
    return f"Demo handoff\n{review}"
