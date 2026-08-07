#!/usr/bin/env python3
"""Report loop/graph keep-rate from ~/.hermes/state/keep-rate.jsonl.

Usage:
  keep-rate.py             # report; always exit 0 unless log is unreadable
  keep-rate.py --strict    # exit 2 if any loop is below 50%
  keep-rate.py --json      # machine-readable report
"""
import argparse
import collections
import json
import os
import sys

LOG = os.path.expanduser("~/.hermes/state/keep-rate.jsonl")
THRESHOLD = 0.50

parser = argparse.ArgumentParser()
parser.add_argument("--strict", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

rows, bad = [], 0
if os.path.exists(LOG):
    with open(LOG, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or "loop" not in row or "kept" not in row:
                    raise ValueError("missing loop/kept")
                rows.append(row)
            except (json.JSONDecodeError, ValueError) as exc:
                bad += 1
                print(f"warning: skipped malformed keep-rate line {line_no}: {exc}", file=sys.stderr)

counts = collections.defaultdict(lambda: [0, 0])
for row in rows:
    counts[str(row["loop"])][0] += 1
    counts[str(row["loop"])][1] += int(bool(row["kept"]))

report = []
for name, (runs, kept) in sorted(counts.items()):
    rate = kept / runs
    report.append({"loop": name, "runs": runs, "kept": kept, "keep_rate": rate, "below_threshold": rate < THRESHOLD})

if args.json:
    print(json.dumps({"threshold": THRESHOLD, "malformed_lines": bad, "loops": report}, indent=2))
elif not report:
    print("no loop runs logged yet")
else:
    print(f"{'loop':30s} {'runs':>5s} {'kept':>5s} {'keep-rate':>10s}")
    for item in report:
        flag = "  <-- KILL, below 50%" if item["below_threshold"] else ""
        print(f"{item['loop']:30s} {item['runs']:5d} {item['kept']:5d} {item['keep_rate']:9.0%}{flag}")

if args.strict and any(item["below_threshold"] for item in report):
    sys.exit(2)
