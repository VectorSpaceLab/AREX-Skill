#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_records(path):
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def normalize_answer(text):
    first = str(text).split(".")[0].replace(",", "")
    words = first.split()
    lowered = [word.lower() for word in words]
    return "no" if "no" in lowered or "not" in lowered else "yes"


def safe_div(num, den):
    return float(num) / float(den) if den else 0.0


def evaluate_answers(answers, labels):
    if len(answers) != len(labels):
        raise ValueError("answers and labels must have the same length")
    pred_values = []
    label_values = []
    normalized = []
    for answer, label_record in zip(answers, labels):
        normalized_answer = normalize_answer(answer.get("answer", ""))
        pred = 0 if normalized_answer == "no" else 1
        label = 0 if str(label_record.get("label", "")).lower() == "no" else 1
        pred_values.append(pred)
        label_values.append(label)
        normalized.append({
            "question_id": label_record.get("question_id", answer.get("question_id")),
            "raw_answer": answer.get("answer", ""),
            "normalized_answer": normalized_answer,
            "label": "yes" if label else "no",
        })
    tp = sum(1 for pred, label in zip(pred_values, label_values) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(pred_values, label_values) if pred == 1 and label == 0)
    tn = sum(1 for pred, label in zip(pred_values, label_values) if pred == 0 and label == 0)
    fn = sum(1 for pred, label in zip(pred_values, label_values) if pred == 0 and label == 1)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    return {
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": safe_div(tp + tn, len(pred_values)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "yes_ratio": safe_div(pred_values.count(1), len(pred_values)),
        "normalized_predictions": normalized,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers")
    parser.add_argument("--labels")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = evaluate_answers([{"answer": "Yes, clearly."}, {"answer": "No, not present."}], [{"label": "yes"}, {"label": "no"}])
        assert result["f1"] == 1.0
        print(json.dumps({"ok": True}))
        return
    result = evaluate_answers(read_records(args.answers), read_records(args.labels))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
