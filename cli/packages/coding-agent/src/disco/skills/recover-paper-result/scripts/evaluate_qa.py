#!/usr/bin/env python3
"""Evaluate QA predictions with exact match and token F1."""

from __future__ import annotations

import argparse
import json
import re
import string
from collections import Counter
from pathlib import Path


def normalize_answer(text: str) -> str:
    text = str(text or "").lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    same = sum(common.values())
    if same == 0:
        return 0.0
    precision = same / len(pred_tokens)
    recall = same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, ground_truth: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def read_records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return data["records"]
    raise ValueError("prediction file must be a JSON list, JSONL, or object with records")


def answers_for(record: dict) -> list[str]:
    value = record.get("answers", record.get("answer", record.get("gold", "")))
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", help="JSON/JSONL records with prediction and answer(s).")
    parser.add_argument("--output", required=True, help="Output metrics JSON.")
    args = parser.parse_args()

    records = read_records(Path(args.predictions).expanduser().resolve())
    evaluated = []
    em_values = []
    f1_values = []
    for idx, record in enumerate(records):
        prediction = str(record.get("prediction", record.get("pred", "")))
        answers = answers_for(record)
        best_em = max(exact_match(prediction, answer) for answer in answers)
        best_f1 = max(f1_score(prediction, answer) for answer in answers)
        em_values.append(best_em)
        f1_values.append(best_f1)
        new_record = dict(record)
        new_record["em"] = best_em
        new_record["f1"] = best_f1
        new_record["normalized_prediction"] = normalize_answer(prediction)
        new_record["normalized_answers"] = [normalize_answer(a) for a in answers]
        new_record["index"] = idx
        evaluated.append(new_record)

    result = {
        "sample_count": len(records),
        "metrics": {
            "em": sum(em_values) / len(em_values) if em_values else 0.0,
            "f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
        },
        "records": evaluated,
    }
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
