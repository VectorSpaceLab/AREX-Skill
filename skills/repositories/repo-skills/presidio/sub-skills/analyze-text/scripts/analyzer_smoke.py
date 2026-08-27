#!/usr/bin/env python3
"""Smoke-check the default Presidio Analyzer text path.

This script tries the default AnalyzerEngine configuration first. If the
expected default spaCy model is unavailable, it prints clear install guidance
and exits cleanly unless --strict is set.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List

from presidio_analyzer import AnalyzerEngine

DEFAULT_TEXT = "John Smith drivers license is AC432223"
DEFAULT_EXPECTED_ENTITIES = ["PERSON", "US_DRIVER_LICENSE"]
DEFAULT_LANGUAGE = "en"

MISSING_MODEL_HINTS = (
    "en_core_web_lg",
    "can't find model",
    "cannot find model",
    "no module named 'en_core_web_lg'",
    "spaCy",
    "download",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check the default Presidio Analyzer engine and confirm that the "
            "documented default model path can detect common text entities."
        )
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Sample text to analyze (default: a PERSON and US driver license example).",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Language code to analyze (default: en).",
    )
    parser.add_argument(
        "--expected-entities",
        nargs="+",
        default=DEFAULT_EXPECTED_ENTITIES,
        help=(
            "Entity types that must be present in the result. "
            "Defaults to PERSON and US_DRIVER_LICENSE."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Return a non-zero exit code when the default model is missing instead "
            "of printing guidance and exiting cleanly."
        ),
    )
    return parser


def _looks_like_missing_default_model(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(hint.lower() in message for hint in MISSING_MODEL_HINTS)


def _format_spans(text: str, results) -> List[str]:
    lines = []
    for result in results:
        span = text[result.start : result.end]
        lines.append(f"{result.entity_type}: {span!r} ({result.score:.3f})")
    return lines


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(
            text=args.text,
            language=args.language,
            entities=args.expected_entities,
        )
    except Exception as exc:  # pragma: no cover - smoke-script behavior
        if _looks_like_missing_default_model(exc):
            print(
                "Default AnalyzerEngine is unavailable because the default spaCy "
                "model was not found. Install the documented default model for the "
                "AnalyzerEngine path, or use a NoOpNlpEngine + custom recognizers "
                "for no-download workflows.",
                file=sys.stderr,
            )
            print(f"Original error: {exc}", file=sys.stderr)
            return 1 if args.strict else 0
        raise

    found_entities = {result.entity_type for result in results}
    missing = [entity for entity in args.expected_entities if entity not in found_entities]
    assert not missing, (
        f"Missing expected entities: {missing}. Got: {sorted(found_entities)}"
    )

    print("Default AnalyzerEngine smoke passed")
    for line in _format_spans(args.text, results):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
