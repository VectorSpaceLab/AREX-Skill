#!/usr/bin/env python3
"""Validate Simple Transformers NER and QA data without importing the package."""
import argparse
import csv
import json
import sys
from pathlib import Path


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"line {i}: invalid JSON: {e}") from e
    return rows


def validate_ner_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("empty NER CSV")
    required = {"sentence_id", "words", "labels"}
    for i, row in enumerate(rows, 1):
        missing = [c for c in required if c not in row or not str(row[c]).strip()]
        if missing:
            raise ValueError(f"row {i}: missing {missing}")
        for c in ["x0", "y0", "x1", "y1"]:
            if c in row and str(row[c]).strip():
                try:
                    v = int(row[c])
                except ValueError:
                    raise ValueError(f"row {i}: {c} must be int")
                if not 0 <= v <= 1000:
                    raise ValueError(f"row {i}: {c} must be in [0, 1000]")
    return len(rows)


def validate_conll(path):
    count = 0
    sentence_has_token = False
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip():
                sentence_has_token = False
                continue
            parts = line.split()
            if len(parts) < 2:
                raise ValueError(f"line {i}: expected at least word and label")
            if not parts[-1]:
                raise ValueError(f"line {i}: empty label")
            count += 1
            sentence_has_token = True
    if count == 0:
        raise ValueError("CoNLL file has no tokens")
    return count


def validate_qa_records(records, predict=False):
    if not isinstance(records, list) or not records:
        raise ValueError("QA data must be a non-empty list")
    question_count = 0
    ids = set()
    for ci, ctx in enumerate(records, 1):
        if not isinstance(ctx, dict):
            raise ValueError(f"context {ci}: expected object")
        context = ctx.get("context")
        qas = ctx.get("qas")
        if not isinstance(context, str) or not context:
            raise ValueError(f"context {ci}: context must be non-empty string")
        if not isinstance(qas, list) or not qas:
            raise ValueError(f"context {ci}: qas must be non-empty list")
        for qi, qa in enumerate(qas, 1):
            qid = qa.get("id")
            if qid in ids:
                raise ValueError(f"duplicate QA id: {qid}")
            ids.add(qid)
            if not qid or not qa.get("question"):
                raise ValueError(f"context {ci} qa {qi}: id and question are required")
            question_count += 1
            if predict:
                continue
            impossible = bool(qa.get("is_impossible", False))
            answers = qa.get("answers")
            if impossible:
                if answers not in ([], None):
                    raise ValueError(f"context {ci} qa {qi}: impossible question should have empty answers")
                continue
            if not isinstance(answers, list) or not answers:
                raise ValueError(f"context {ci} qa {qi}: non-impossible question needs answers")
            for ai, ans in enumerate(answers, 1):
                text = ans.get("text")
                start = ans.get("answer_start")
                if not isinstance(text, str) or not isinstance(start, int):
                    raise ValueError(f"context {ci} qa {qi} answer {ai}: text str and answer_start int required")
                if context[start:start + len(text)] != text:
                    raise ValueError(f"context {ci} qa {qi} answer {ai}: text does not match context at answer_start")
    return question_count


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Simple Transformers NER/QA data files.")
    parser.add_argument("--task", choices=["ner-csv", "ner-conll", "qa-json", "qa-jsonl", "qa-predict-json"], required=True)
    parser.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.task == "ner-csv":
            n = validate_ner_csv(args.input)
        elif args.task == "ner-conll":
            n = validate_conll(args.input)
        elif args.task == "qa-json":
            n = validate_qa_records(load_json(args.input), predict=False)
        elif args.task == "qa-jsonl":
            n = validate_qa_records(load_jsonl(args.input), predict=False)
        else:
            n = validate_qa_records(load_json(args.input), predict=True)
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"ok: validated {n} item(s) for {args.task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
