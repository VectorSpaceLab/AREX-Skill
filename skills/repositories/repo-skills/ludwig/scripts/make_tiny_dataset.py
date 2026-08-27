#!/usr/bin/env python3
"""Create a tiny local Ludwig CSV/config fixture.

Example:
    python make_tiny_dataset.py --output-dir /tmp/ludwig-tiny --rows 12
"""
import argparse
import csv
from pathlib import Path

CONFIG = """model_type: ecd
input_features:
  - name: age
    type: number
  - name: segment
    type: category
  - name: note
    type: text
output_features:
  - name: churn
    type: binary
trainer:
  train_steps: 1
  batch_size: 4
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a tiny Ludwig dataset.csv and config.yaml fixture.")
    parser.add_argument("--output-dir", required=True, help="Directory to create or reuse.")
    parser.add_argument("--rows", type=int, default=8, help="Number of rows to write (default: 8).")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dataset.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["age", "segment", "note", "churn"])
        writer.writeheader()
        for i in range(args.rows):
            writer.writerow({
                "age": 20 + i,
                "segment": ["free", "pro", "team"][i % 3],
                "note": f"customer row {i}",
                "churn": int(i % 2 == 0),
            })
    (out / "config.yaml").write_text(CONFIG, encoding="utf-8")
    print(f"wrote {out / 'dataset.csv'}")
    print(f"wrote {out / 'config.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
