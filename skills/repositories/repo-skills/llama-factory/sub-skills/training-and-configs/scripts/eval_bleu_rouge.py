# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Dependency-free approximate BLEU/ROUGE evaluator for prediction files.

Input must be JSONL or JSON containing records with `predict` and `label`
fields. This script is intentionally self-contained and does not import
LlamaFactory, datasets, nltk, jieba, or rouge_chinese. Scores are approximate
word/character n-gram overlap metrics for quick local checks, not a replacement
for the optional dependency-backed upstream evaluator.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and isinstance(data.get("data"), list):
            records = data["data"]
        else:
            raise ValueError("JSON input must be a list of records or an object with a data list.")
    for index, record in enumerate(records):
        if not isinstance(record, dict) or "predict" not in record or "label" not in record:
            raise ValueError(f"Record {index} must contain predict and label fields.")
    return records


def tokenize(text: str, mode: str) -> list[str]:
    text = str(text).strip()
    if mode == "char":
        return [char for char in text if not char.isspace()]
    return TOKEN_RE.findall(text.lower())


def ngrams(tokens: list[str], n: int) -> collections.Counter[tuple[str, ...]]:
    return collections.Counter(tuple(tokens[index : index + n]) for index in range(max(len(tokens) - n + 1, 0)))


def overlap_count(left: collections.Counter[tuple[str, ...]], right: collections.Counter[tuple[str, ...]]) -> int:
    return sum((left & right).values())


def rouge_n(prediction: list[str], reference: list[str], n: int) -> float:
    reference_ngrams = ngrams(reference, n)
    if not reference_ngrams:
        return 0.0
    return overlap_count(ngrams(prediction, n), reference_ngrams) / sum(reference_ngrams.values())


def lcs_length(left: list[str], right: list[str]) -> int:
    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    for token in left:
        current = [0]
        for index, other in enumerate(right, start=1):
            if token == other:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def rouge_l(prediction: list[str], reference: list[str]) -> float:
    if not reference:
        return 0.0
    return lcs_length(prediction, reference) / len(reference)


def bleu(prediction: list[str], reference: list[str], max_order: int = 4) -> float:
    if not prediction or not reference:
        return 0.0
    precisions: list[float] = []
    for n in range(1, max_order + 1):
        pred_ngrams = ngrams(prediction, n)
        total = sum(pred_ngrams.values())
        if total == 0:
            precisions.append(1.0 / (len(prediction) + 2.0))
            continue
        matches = overlap_count(pred_ngrams, ngrams(reference, n))
        precisions.append((matches + 1.0) / (total + 2.0))
    brevity = 1.0 if len(prediction) > len(reference) else math.exp(1 - len(reference) / max(len(prediction), 1))
    return brevity * math.exp(sum(math.log(score) for score in precisions) / max_order)


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def evaluate(records: list[dict[str, Any]], mode: str) -> dict[str, float]:
    scores: dict[str, list[float]] = {"bleu-4": [], "rouge-1": [], "rouge-2": [], "rouge-l": []}
    for record in records:
        prediction = tokenize(str(record["predict"]), mode)
        reference = tokenize(str(record["label"]), mode)
        scores["bleu-4"].append(bleu(prediction, reference) * 100)
        scores["rouge-1"].append(rouge_n(prediction, reference, 1) * 100)
        scores["rouge-2"].append(rouge_n(prediction, reference, 2) * 100)
        scores["rouge-l"].append(rouge_l(prediction, reference) * 100)
    return {name: round(mean(values), 4) for name, values in sorted(scores.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename", type=Path, help="JSON/JSONL file with predict and label fields.")
    parser.add_argument("--tokenizer", choices=["word", "char"], default="word", help="Tokenization mode for overlap metrics.")
    parser.add_argument("--output", type=Path, default=Path("predictions_score.json"), help="Where to write aggregate JSON scores.")
    parser.add_argument("--no-write", action="store_true", help="Print scores without writing the output JSON file.")
    args = parser.parse_args(argv)

    records = load_records(args.filename)
    result = evaluate(records, args.tokenizer)
    for name, score in result.items():
        print(f"{name}: {score:.4f}")
    if not args.no_write:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Score file saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
