#!/usr/bin/env python3
"""Smoke-check NoOpNlpEngine plus custom pattern recognizers.

This script avoids model downloads by pairing NoOpNlpEngine with two local
PatternRecognizer instances: one deny-list recognizer and one regex recognizer.
It also demonstrates allow-list filtering on the final AnalyzerEngine output.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NoOpNlpEngine

DEFAULT_LANGUAGE = "en"
DEFAULT_TEXT = "Professor 90210"
DEFAULT_ALLOW_LIST = ["Professor"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Demonstrate a no-download Presidio Analyzer setup with NoOpNlpEngine, "
            "a deny-list recognizer, a regex recognizer, and allow-list filtering."
        )
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Sample text to analyze (default: one deny-list hit and one ZIP hit).",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Language code to analyze (default: en).",
    )
    parser.add_argument(
        "--allow-list",
        nargs="*",
        default=DEFAULT_ALLOW_LIST,
        help=(
            "Allow-list terms to remove from the final result. "
            "Defaults to ['Professor'] so the title result is filtered out."
        ),
    )
    return parser


def build_engine(language: str) -> AnalyzerEngine:
    no_op_engine = NoOpNlpEngine(models=[{"lang_code": language, "model_name": "no_op"}])
    no_op_engine.load()

    title_recognizer = PatternRecognizer(
        supported_entity="TITLE",
        name="TitlesRecognizer",
        supported_language=language,
        deny_list=["Professor", "Dr.", "Mr.", "Mrs.", "Ms."],
    )
    zip_recognizer = PatternRecognizer(
        supported_entity="ZIP",
        name="ZipRecognizer",
        supported_language=language,
        patterns=[Pattern(name="zip code", regex=r"\b\d{5}\b", score=0.5)],
    )

    registry = RecognizerRegistry(
        recognizers=[title_recognizer, zip_recognizer],
        supported_languages=[language],
    )
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=no_op_engine,
        supported_languages=[language],
    )


def _entity_spans(text: str, results) -> List[str]:
    return [f"{result.entity_type}: {text[result.start:result.end]!r}" for result in results]


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    engine = build_engine(args.language)

    base_results = engine.analyze(text=args.text, language=args.language)
    filtered_results = engine.analyze(
        text=args.text,
        language=args.language,
        allow_list=args.allow_list,
    )

    base_entities = sorted(result.entity_type for result in base_results)
    filtered_entities = sorted(result.entity_type for result in filtered_results)

    assert base_entities == ["TITLE", "ZIP"], (
        f"Expected one title and one ZIP hit without allow-list filtering, got {base_entities}"
    )
    assert filtered_entities == ["ZIP"], (
        f"Allow-list filtering should remove only the title hit, got {filtered_entities}"
    )

    print("NoOpNlpEngine custom-recognizer smoke passed")
    print("Base results:")
    for line in _entity_spans(args.text, base_results):
        print(line)
    print("Filtered results:")
    for line in _entity_spans(args.text, filtered_results):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
