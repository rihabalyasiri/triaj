# writer.py

import csv
import json
from pathlib import Path

FIELDS = ["id", "message", "predicted_topic", "priority", "action", "escalated", "error"]

out_path = Path("triage_results.csv")

def write_results(record):
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()

        writer.writerow(record)
        f.flush()   
