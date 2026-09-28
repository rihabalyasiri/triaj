# writer.py
import csv
from contextlib import contextmanager
from pathlib import Path

FIELDS = [
    "id",
    "message",
    "queue",
    "priority",
    # fields from NLI classifier
    "predicted_topic",
    "confidence",
    "predicted_priority",
    "priority_score",
    "urgency",
    # fields from action decision
    "action",
    "escalated",
    # fields from LLM check
    "ambiguous",
    "ambiguity_reason",
    "follow_up_questions",
    "customer_reply",
    "status",
    "error",
]
OUT_PATH = Path("triage_results.csv")


@contextmanager
def open_results(path: Path = OUT_PATH):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        yield writer