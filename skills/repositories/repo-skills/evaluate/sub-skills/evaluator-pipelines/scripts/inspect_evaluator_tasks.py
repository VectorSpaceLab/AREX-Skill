#!/usr/bin/env python3
"""Print evaluate.evaluator supported tasks without loading models or datasets."""

from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module


FALLBACK_REGISTRY = [
    ("text-classification", "TextClassificationEvaluator", "accuracy"),
    ("image-classification", "ImageClassificationEvaluator", "accuracy"),
    ("question-answering", "QuestionAnsweringEvaluator", "squad"),
    ("token-classification", "TokenClassificationEvaluator", "seqeval"),
    ("text-generation", "TextGenerationEvaluator", "word_count"),
    ("text2text-generation", "Text2TextGenerationEvaluator", "bleu"),
    ("summarization", "SummarizationEvaluator", "rouge"),
    ("translation", "TranslationEvaluator", "bleu"),
    ("automatic-speech-recognition", "AutomaticSpeechRecognitionEvaluator", "wer"),
    ("audio-classification", "AudioClassificationEvaluator", "accuracy"),
]


def fallback_registry() -> list[dict[str, str | None]]:
    return [
        {"task": task, "evaluator_class": evaluator_class, "default_metric": default_metric}
        for task, evaluator_class, default_metric in FALLBACK_REGISTRY
    ]


def build_registry(allow_fallback: bool = True) -> tuple[list[dict[str, str | None]], str | None]:
    try:
        evaluator_module = import_module("evaluate.evaluator")
    except Exception as error:  # noqa: BLE001 - deterministic fallback for minimal environments
        if not allow_fallback:
            raise
        return fallback_registry(), f"using bundled fallback because evaluate.evaluator import failed: {error}"

    tasks = evaluator_module.get_supported_tasks()
    registry = evaluator_module.SUPPORTED_EVALUATOR_TASKS
    rows = []
    for task in tasks:
        metadata = registry[task]
        implementation = metadata.get("implementation")
        rows.append(
            {
                "task": task,
                "evaluator_class": getattr(implementation, "__name__", str(implementation)),
                "default_metric": metadata.get("default_metric_name"),
            }
        )
    return rows, None


def print_table(rows: list[dict[str, str | None]]) -> None:
    headers = ["task", "evaluator_class", "default_metric"]
    widths = {
        header: max(len(header), *(len(str(row[header] or "")) for row in rows))
        for header in headers
    }
    print("  ".join(header.ljust(widths[header]) for header in headers))
    print("  ".join("-" * widths[header] for header in headers))
    for row in rows:
        print("  ".join(str(row[header] or "").ljust(widths[header]) for header in headers))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print registry as JSON")
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="fail instead of using bundled registry metadata when evaluate cannot be imported",
    )
    args = parser.parse_args()

    try:
        rows, warning = build_registry(allow_fallback=not args.no_fallback)
    except Exception as error:  # noqa: BLE001 - command-line diagnostic helper
        print(f"Unable to inspect evaluate.evaluator registry: {error}", file=sys.stderr)
        return 1

    if warning:
        print(f"Warning: {warning}", file=sys.stderr)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
