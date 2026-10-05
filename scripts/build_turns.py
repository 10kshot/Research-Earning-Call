"""Build call index and turn-level records from raw StreetEvents XML.

Usage:
    PYTHONPATH=src python3 scripts/build_turns.py 2016 [--all-events] [--source local|supabase]

Writes:
    data/interim/calls_<year>.csv    one row per transcript (all event types)
    data/interim/turns_<year>.jsonl  one row per turn unit (earnings calls only unless --all-events)
    data/interim/parse_errors_<year>.csv
"""

import argparse
import csv
import json
from pathlib import Path

from ccad.sources import get_source
from ccad.transcripts import EARNINGS_EVENT_TYPE, parse_xml

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year")
    ap.add_argument("--all-events", action="store_true")
    ap.add_argument("--source", choices=["local", "supabase"], default="local")
    args = ap.parse_args()

    out = ROOT / "data" / "interim"
    calls, errors, n_turns = [], [], 0
    with open(out / f"turns_{args.year}.jsonl", "w") as turns_f:
        for k, (name, xml) in enumerate(get_source(args.source).iter_xml(int(args.year)), 1):
            try:
                call, turns = parse_xml(xml, name)
            except Exception as e:  # keep going; failures are logged for review
                errors.append({"file_name": name, "error": repr(e)})
                continue
            calls.append(call)
            if args.all_events or call["event_type"] == EARNINGS_EVENT_TYPE:
                for t in turns:
                    turns_f.write(json.dumps(t) + "\n")
                n_turns += len(turns)
            if k % 2000 == 0:
                print(f"{k} files")

    with open(out / f"calls_{args.year}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(calls[0]))
        w.writeheader()
        w.writerows(calls)
    with open(out / f"parse_errors_{args.year}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file_name", "error"])
        w.writeheader()
        w.writerows(errors)
    earnings = [c for c in calls if c["event_type"] == EARNINGS_EVENT_TYPE]
    print(f"{len(calls)} calls parsed ({len(earnings)} earnings calls, "
          f"{sum(c['has_qa'] for c in earnings)} with Q&A), {n_turns} turn units, {len(errors)} errors")


if __name__ == "__main__":
    main()
