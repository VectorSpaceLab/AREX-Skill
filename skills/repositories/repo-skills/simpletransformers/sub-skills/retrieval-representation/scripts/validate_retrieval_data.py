#!/usr/bin/env python3
"""Validate Simple Transformers retrieval/representation data files without optional deps."""
import argparse
import csv
import json
import sys


def validate_csv(path, delimiter=","):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=delimiter))
    if not rows:
        raise ValueError("file has no rows")
    for i, row in enumerate(rows, 1):
        for col in ["query_text", "gold_passage"]:
            if col not in row or not str(row[col]).strip():
                raise ValueError(f"row {i}: missing {col}")
    return len(rows)


def validate_lines(path):
    count = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                count += 1
            elif i == 1:
                raise ValueError("first query line is empty")
    if count == 0:
        raise ValueError("no non-empty queries")
    return count


def validate_jsonl(path, required):
    count = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            count += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"line {i}: invalid JSON: {e}") from e
            missing = [k for k in required if k not in obj or not str(obj[k]).strip()]
            if missing:
                raise ValueError(f"line {i}: missing {missing}")
    if count == 0:
        raise ValueError("JSONL has no records")
    return count


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate Simple Transformers retrieval data shapes.")
    p.add_argument("--task", choices=["retrieval-csv", "tsv", "query-lines", "beir-corpus-jsonl", "beir-queries-jsonl"], required=True)
    p.add_argument("--input", required=True)
    args = p.parse_args(argv)
    try:
        if args.task == "retrieval-csv":
            n = validate_csv(args.input)
        elif args.task == "tsv":
            n = validate_csv(args.input, delimiter="\t")
        elif args.task == "query-lines":
            n = validate_lines(args.input)
        elif args.task == "beir-corpus-jsonl":
            n = validate_jsonl(args.input, ["_id", "text"])
        else:
            n = validate_jsonl(args.input, ["_id", "text"])
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"ok: validated {n} item(s) for {args.task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
