#!/usr/bin/env python3
"""Create a tiny prediction-only CSV fixture for examples."""
import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a tiny prediction CSV with input columns only.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--rows", type=int, default=4)
    args = parser.parse_args()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["feature_num", "feature_cat"])
        writer.writeheader()
        for i in range(args.rows):
            writer.writerow({"feature_num": i / 10, "feature_cat": "a" if i % 2 else "b"})
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
