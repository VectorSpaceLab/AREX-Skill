#!/usr/bin/env python3
"""Evaluate GSM8K prediction records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_predictions(predictions: list[dict]) -> dict:
    total = len(predictions)
    correct = 0
    rows = []
    for item in predictions:
        ok = item.get("selected_answer") == item.get("gold_answer")
        correct += int(ok)
        rows.append({"problem_id": item.get("problem_id"), "correct": ok, "prediction": item.get("selected_answer"), "gold": item.get("gold_answer")})
    return {"sample_count": total, "correct_count": correct, "solve_rate": correct / total if total else 0.0, "items": rows}


def evaluate_file(predictions_path: str, output_path: str) -> dict:
    predictions = json.loads(Path(predictions_path).read_text(encoding="utf-8"))
    result = evaluate_predictions(predictions)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(evaluate_file(args.predictions, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
