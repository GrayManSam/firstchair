"""Structured review carried from the synthetic worker to synthesis."""

from typing import TypedDict


class WorkerReview(TypedDict):
    assignment: str
    validation_step: str


def review_assignment(assignment: str) -> WorkerReview:
    return {
        "assignment": assignment,
        "validation_step": "Record an expected result and a repeatable validation step.",
    }


def read_review(value: object) -> WorkerReview:
    if not isinstance(value, dict) or value.keys() != {"assignment", "validation_step"}:
        raise ValueError("invalid worker review")
    assignment = value["assignment"]
    validation_step = value["validation_step"]
    if any(not isinstance(text, str) or not text.strip() for text in (assignment, validation_step)):
        raise ValueError("invalid worker review")
    return {"assignment": assignment, "validation_step": validation_step}


def review_text(review: WorkerReview) -> str:
    return f"{review['assignment']}\n{review['validation_step']}"
