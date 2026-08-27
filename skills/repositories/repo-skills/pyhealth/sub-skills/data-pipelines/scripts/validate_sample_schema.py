#!/usr/bin/env python3
"""Check required keys and patient-disjoint partitions in local JSON samples."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path, help="JSON array of sample objects")
    parser.add_argument("--require", action="append", default=[], help="required key; repeat")
    parser.add_argument("--partition-key", default="partition", help="partition field")
    args = parser.parse_args()
    data = json.loads(args.samples.read_text())
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise SystemExit("samples must be a JSON array of objects")
    missing = {key: i for i, row in enumerate(data) for key in args.require if key not in row}
    partitions = {}
    for row in data:
        if args.partition_key in row:
            partitions.setdefault(row[args.partition_key], set()).add(row.get("patient_id"))
    overlap = {}
    names = list(partitions)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            common = sorted(partitions[left] & partitions[right] - {None})
            if common: overlap[f"{left}|{right}"] = common
    result = {"count": len(data), "missing": missing, "partition_patient_overlap": overlap}
    print(json.dumps(result, indent=2, default=list))
    return 0 if not missing and not overlap else 1

if __name__ == "__main__":
    raise SystemExit(main())
