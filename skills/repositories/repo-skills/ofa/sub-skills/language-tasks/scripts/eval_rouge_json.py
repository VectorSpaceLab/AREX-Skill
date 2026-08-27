#!/usr/bin/env python3
"""Evaluate Gigaword-style prediction JSON with ROUGE.

This helper is a self-contained replacement for the repo's JSON ROUGE helper.
It expects a JSON list of objects and extracts prediction/reference text by key.

Example:
  python eval_rouge_json.py --predictions test_predict.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List



def compute_rouge(predictions: Iterable[str], references: Iterable[str], use_stemmer: bool = True) -> dict:
    try:
        from rouge_score import rouge_scorer, scoring
    except Exception as exc:  # pragma: no cover - helper diagnostics
        raise RuntimeError(
            "missing optional dependency: rouge_score is required for ROUGE evaluation"
        ) from exc

    rouge_types = ["rouge1", "rouge2", "rougeL", "rougeLsum"]
    scorer = rouge_scorer.RougeScorer(rouge_types=rouge_types, use_stemmer=use_stemmer)
    aggregator = scoring.BootstrapAggregator()
    for ref, pred in zip(references, predictions):
        aggregator.add_scores(scorer.score(ref, pred))
    return aggregator.aggregate()


def _format_score(value) -> float:
    return float(value.mid.fmeasure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="JSON file with prediction objects.")
    parser.add_argument("--prediction-key", default="hyp", help="Key containing the generated hypothesis text.")
    parser.add_argument("--reference-key", default="ref", help="Key containing the reference text.")
    parser.add_argument("--output", default=None, type=Path, help="Optional JSON file for metrics.")
    parser.add_argument("--no-stemmer", action="store_true", help="Disable Porter stemming.")
    args = parser.parse_args()

    try:
        raw = json.loads(args.predictions.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("prediction JSON must contain a list of objects")
        predictions: List[str] = []
        references: List[str] = []
        for index, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"row {index}: prediction entry is not an object")
            if args.prediction_key not in item or args.reference_key not in item:
                raise ValueError(f"row {index}: missing keys {args.prediction_key!r}/{args.reference_key!r}")
            predictions.append(str(item[args.prediction_key]))
            references.append(str(item[args.reference_key]))
        results = compute_rouge(predictions, references, use_stemmer=not args.no_stemmer)
        payload = {
            name: _format_score(score)
            for name, score in results.items()
        }
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
