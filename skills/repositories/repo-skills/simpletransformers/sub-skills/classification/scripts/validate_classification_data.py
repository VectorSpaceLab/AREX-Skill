#!/usr/bin/env python3
"""Validate Simple Transformers classification data files without importing the package.

Examples:
  python validate_classification_data.py --task single --input train.csv
  python validate_classification_data.py --task multilabel --input multilabel.jsonl --num-labels 6
  python validate_classification_data.py --task layoutlm --input layout.jsonl
"""
import argparse
import ast
import csv
import json
import os
import sys
from pathlib import Path


def load_records(path):
    p = Path(path)
    if not p.exists():
        raise ValueError(f"input file does not exist: {path}")
    if p.suffix.lower() == ".jsonl":
        rows = []
        with p.open(encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"line {i}: invalid JSONL: {e}") from e
                if not isinstance(obj, dict):
                    raise ValueError(f"line {i}: expected JSON object")
                rows.append(obj)
        return rows
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_value(value):
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[") or s.startswith("{") or s.startswith("("):
            try:
                return ast.literal_eval(s)
            except Exception:
                return value
    return value


def require(row, cols, row_no):
    missing = [c for c in cols if c not in row or row[c] in (None, "")]
    if missing:
        raise ValueError(f"row {row_no}: missing required column(s): {', '.join(missing)}")


def as_number(value, integer=False):
    value = parse_value(value)
    if integer:
        if isinstance(value, bool):
            raise ValueError("boolean is not a valid integer class label")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
        raise ValueError(f"expected integer label, got {value!r}")
    try:
        return float(value)
    except Exception as e:
        raise ValueError(f"expected numeric label, got {value!r}") from e


def parse_list(value, name):
    value = parse_value(value)
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list, got {value!r}")
    return list(value)


def check_label(row, row_no, multilabel=False, regression=False, num_labels=None):
    label = parse_value(row.get("labels"))
    if multilabel:
        values = parse_list(label, "labels")
        if num_labels is not None and len(values) != num_labels:
            raise ValueError(f"row {row_no}: labels length {len(values)} != num_labels {num_labels}")
        bad = [v for v in values if v not in (0, 1, "0", "1")]
        if bad:
            raise ValueError(f"row {row_no}: multilabel values must be 0/1, got {bad[:3]!r}")
    elif regression:
        as_number(label, integer=False)
    else:
        as_number(label, integer=True)


def validate(args):
    rows = load_records(args.input)
    if not rows:
        raise ValueError("input contains no records")
    for i, row in enumerate(rows, 1):
        row = {k: parse_value(v) for k, v in row.items()}
        if args.task == "single":
            require(row, ["text", "labels"], i)
            if not isinstance(row["text"], str) or not row["text"].strip():
                raise ValueError(f"row {i}: text must be a non-empty string")
            check_label(row, i, regression=args.regression)
        elif args.task == "sentence-pair":
            require(row, ["text_a", "text_b", "labels"], i)
            if not str(row["text_a"]).strip() or not str(row["text_b"]).strip():
                raise ValueError(f"row {i}: text_a and text_b must be non-empty")
            check_label(row, i, regression=args.regression)
        elif args.task == "multilabel":
            require(row, ["text", "labels"], i)
            check_label(row, i, multilabel=True, num_labels=args.num_labels)
        elif args.task == "layoutlm":
            require(row, ["text", "labels", "x0", "y0", "x1", "y1"], i)
            words = str(row["text"]).split()
            coords = {name: parse_list(row[name], name) for name in ["x0", "y0", "x1", "y1"]}
            for name, vals in coords.items():
                if len(vals) != len(words):
                    raise ValueError(f"row {i}: {name} length {len(vals)} != word count {len(words)}")
                for v in vals:
                    if not isinstance(v, int) or not 0 <= v <= 1000:
                        raise ValueError(f"row {i}: {name} values must be int in [0, 1000], got {v!r}")
            for j, (x0, y0, x1, y1) in enumerate(zip(coords["x0"], coords["y0"], coords["x1"], coords["y1"]), 1):
                if x0 > x1 or y0 > y1:
                    raise ValueError(f"row {i}, box {j}: require x0<=x1 and y0<=y1")
        elif args.task == "multimodal":
            require(row, [args.text_column, args.label_column, args.image_column], i)
            image_value = row[args.image_column]
            images = parse_list(image_value, args.image_column) if str(image_value).strip().startswith("[") else [image_value]
            if args.check_image_exists:
                if not args.image_root:
                    raise ValueError("--check-image-exists requires --image-root")
                for image in images:
                    if not (Path(args.image_root) / str(image)).exists():
                        raise ValueError(f"row {i}: image not found under image root: {image}")
    return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Simple Transformers classification tabular data.")
    parser.add_argument("--task", choices=["single", "sentence-pair", "multilabel", "layoutlm", "multimodal"], required=True)
    parser.add_argument("--input", required=True, help="CSV or JSONL file")
    parser.add_argument("--regression", action="store_true", help="Allow float labels for single/sentence-pair tasks")
    parser.add_argument("--num-labels", type=int, help="Expected multilabel vector length")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="labels")
    parser.add_argument("--image-column", default="images")
    parser.add_argument("--image-root")
    parser.add_argument("--check-image-exists", action="store_true")
    args = parser.parse_args(argv)
    try:
        count = validate(args)
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"ok: validated {count} {args.task} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
