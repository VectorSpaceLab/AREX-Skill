#!/usr/bin/env python3
"""Create a tiny local CSV compatible with TSLib's `--data custom` loader.

This is for smoke tests and command/data validation only. It is not a benchmark
dataset and should not be used for accuracy claims.
"""
from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime, timedelta
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tiny TSLib custom CSV fixture.")
    parser.add_argument("--output", default="dataset/tiny-custom/tiny.csv", help="CSV path to write.")
    parser.add_argument("--rows", type=int, default=96, help="Number of hourly rows to create; use at least seq_len + pred_len + split margin.")
    parser.add_argument("--start", default="2024-01-01 00:00:00", help="Start timestamp in 'YYYY-mm-dd HH:MM:SS' format.")
    parser.add_argument("--target", default="OT", help="Target column name to create.")
    args = parser.parse_args()

    if args.rows < 32:
        parser.error("--rows should be at least 32 for stable train/val/test windows")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "feat_sin", "feat_cos", args.target])
        for i in range(args.rows):
            ts = start + timedelta(hours=i)
            writer.writerow([
                ts.strftime("%Y-%m-%d %H:%M:%S"),
                f"{math.sin(i / 6):.6f}",
                f"{math.cos(i / 8):.6f}",
                f"{0.05 * i + math.sin(i / 12):.6f}",
            ])

    print(out)
    print("Use with: --data custom --root_path", str(out.parent) + "/", "--data_path", out.name, "--target", args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
