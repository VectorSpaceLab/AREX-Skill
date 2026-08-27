#!/usr/bin/env python3
"""Validate Simple Transformers generative workflow data without model imports."""
import argparse
import csv
import json
import sys


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def require(row, cols, row_no):
    missing = [c for c in cols if c not in row or not str(row[c]).strip()]
    if missing:
        raise ValueError(f"row {row_no}: missing {missing}")


def validate_csv(path, cols):
    rows = read_csv(path)
    if not rows:
        raise ValueError("CSV has no rows")
    for i, row in enumerate(rows, 1):
        require(row, cols, i)
    return len(rows)


def validate_lm(path):
    nonempty = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                nonempty += 1
    if nonempty == 0:
        raise ValueError("language modeling text has no non-empty lines")
    return nonempty


def validate_t5_predict(path):
    count = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            text = line.strip()
            if not text:
                continue
            count += 1
            if ": " not in text:
                raise ValueError(f"line {i}: T5 prediction input should include 'prefix: input_text'")
    if count == 0:
        raise ValueError("prediction file has no non-empty lines")
    return count


def validate_convai(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, (list, dict)):
        raise ValueError("ConvAI data should be a JSON list or object")
    # Conservative structural check: avoid enforcing one dataset variant.
    text = json.dumps(data)
    for key in ["personality", "utterances"]:
        if key not in text:
            raise ValueError(f"ConvAI data does not contain expected key fragment: {key}")
    return len(data) if isinstance(data, list) else 1


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate Simple Transformers generative data files.")
    p.add_argument("--task", choices=["lm-text", "t5-csv", "seq2seq-csv", "t5-predict-lines", "convai-json"], required=True)
    p.add_argument("--input", required=True)
    args = p.parse_args(argv)
    try:
        if args.task == "lm-text":
            n = validate_lm(args.input)
        elif args.task == "t5-csv":
            n = validate_csv(args.input, ["prefix", "input_text", "target_text"])
        elif args.task == "seq2seq-csv":
            n = validate_csv(args.input, ["input_text", "target_text"])
        elif args.task == "t5-predict-lines":
            n = validate_t5_predict(args.input)
        else:
            n = validate_convai(args.input)
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"ok: validated {n} item(s) for {args.task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
