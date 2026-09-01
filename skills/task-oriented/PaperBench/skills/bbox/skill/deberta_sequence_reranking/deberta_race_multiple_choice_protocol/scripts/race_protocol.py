#!/usr/bin/env python3
"""RACE-style candidate formatting and accuracy helpers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LABELS = ["A", "B", "C", "D"]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip())


def simple_tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+|[^\w\s]", normalize_text(text).lower())


def build_candidates(
    article: str,
    question: str,
    options: list[str],
    answer: str,
    max_seq_len: int = 128,
) -> dict:
    if len(options) != 4:
        raise ValueError("RACE-style items require exactly four options")
    if answer not in LABELS:
        raise ValueError("answer must be one of A, B, C, D")
    article_tokens = simple_tokenize(article)
    question_tokens = simple_tokenize(question)
    candidates = []
    for label, option in zip(LABELS, options):
        option_tokens = simple_tokenize(option)
        tokens = ["[CLS]"] + article_tokens + ["[SEP]"] + question_tokens + option_tokens + ["[SEP]"]
        if len(tokens) > max_seq_len:
            keep_article = max(0, max_seq_len - (len(question_tokens) + len(option_tokens) + 3))
            tokens = ["[CLS]"] + article_tokens[:keep_article] + ["[SEP]"] + question_tokens + option_tokens + ["[SEP]"]
        candidate_text = " ".join(tokens)
        candidates.append(
            {
                "label": label,
                "article": normalize_text(article),
                "question": normalize_text(question),
                "option": normalize_text(option),
                "tokens": tokens,
                "candidate_text": candidate_text,
                "absolute_position": len(["[CLS]"] + article_tokens + ["[SEP]"] + question_tokens),
                "is_gold": label == answer,
            }
        )
    return {
        "article": normalize_text(article),
        "question": normalize_text(question),
        "options": dict(zip(LABELS, [normalize_text(option) for option in options])),
        "answer": answer,
        "max_seq_len": max_seq_len,
        "candidates": candidates,
    }


def predict_from_logits(logits: dict[str, float]) -> str:
    if not logits:
        return ""
    return max(logits.items(), key=lambda item: item[1])[0]


def accuracy(predicted: str, answer: str) -> float:
    return 1.0 if predicted == answer else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-json", required=True)
    parser.add_argument("--max-seq-len", type=int, default=128)
    args = parser.parse_args()
    item = json.loads(Path(args.item_json).read_text(encoding="utf-8"))
    result = build_candidates(
        item["article"],
        item["question"],
        item["options"],
        item["answer"],
        args.max_seq_len,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
