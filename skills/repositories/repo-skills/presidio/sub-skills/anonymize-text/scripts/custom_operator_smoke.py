#!/usr/bin/env python3
"""Deterministic custom-lambda anonymizer smoke without faker."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Tuple

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

DEFAULT_TEXT = "Account ACME-1234 requires review."
DEFAULT_SUBSTRING = "ACME-1234"
DEFAULT_ENTITY = "PROJECT_CODE"
DEFAULT_PREFIX = "<<"
DEFAULT_SUFFIX = ">>"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic custom-lambda anonymizer smoke using a manual span "
            "and the built-in custom operator."
        )
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Source text containing the span to anonymize.",
    )
    parser.add_argument(
        "--substring",
        default=DEFAULT_SUBSTRING,
        help="Substring to locate inside the text and anonymize.",
    )
    parser.add_argument(
        "--entity-type",
        default=DEFAULT_ENTITY,
        help="Entity name used for the manual RecognizerResult span.",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help="Prefix added by the custom lambda.",
    )
    parser.add_argument(
        "--suffix",
        default=DEFAULT_SUFFIX,
        help="Suffix added by the custom lambda.",
    )
    return parser


def locate_span(text: str, substring: str) -> Tuple[int, int]:
    if not substring:
        raise ValueError("--substring must not be empty")
    start = text.find(substring)
    if start < 0:
        raise ValueError(f"Substring {substring!r} was not found in the text.")
    return start, start + len(substring)


def anonymize_with_custom_lambda(args: argparse.Namespace):
    start, end = locate_span(args.text, args.substring)
    analyzer_results = [RecognizerResult(args.entity_type, start, end, 0.99)]
    engine = AnonymizerEngine()
    operator = OperatorConfig(
        "custom",
        {"lambda": lambda value: f"{args.prefix}{value[::-1]}{args.suffix}"},
    )
    result = engine.anonymize(
        text=args.text,
        analyzer_results=analyzer_results,
        operators={args.entity_type: operator},
    )
    return analyzer_results, result


def result_to_dict(analyzer_results, anonymized_result) -> dict:
    return {
        "detected_entities": [
            {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
            }
            for result in analyzer_results
        ],
        "anonymized_text": anonymized_result.text,
        "items": [
            {
                "entity_type": item.entity_type,
                "start": item.start,
                "end": item.end,
                "operator": item.operator,
                "text": item.text,
            }
            for item in anonymized_result.items
        ],
    }


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        analyzer_results, anonymized_result = anonymize_with_custom_lambda(args)
    except Exception as exc:
        print(f"Smoke failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            result_to_dict(analyzer_results, anonymized_result),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
