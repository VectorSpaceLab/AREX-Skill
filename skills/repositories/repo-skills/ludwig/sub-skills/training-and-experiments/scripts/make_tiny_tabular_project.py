#!/usr/bin/env python3
"""Create a tiny trainable Ludwig tabular project with config and CSV."""
import argparse
import csv
from pathlib import Path

CONFIG = """model_type: ecd
input_features:
  - name: feature_num
    type: number
  - name: feature_cat
    type: category
output_features:
  - name: label
    type: binary
trainer:
  train_steps: 1
  batch_size: 4
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create dataset.csv and config.yaml for a tiny Ludwig train smoke.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--rows", type=int, default=16)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dataset.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["feature_num", "feature_cat", "label"])
        writer.writeheader()
        for i in range(args.rows):
            writer.writerow({"feature_num": i / 10, "feature_cat": "a" if i % 2 else "b", "label": i % 2})
    (out / "config.yaml").write_text(CONFIG, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
