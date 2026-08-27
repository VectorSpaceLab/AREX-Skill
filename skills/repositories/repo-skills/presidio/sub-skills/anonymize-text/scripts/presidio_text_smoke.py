#!/usr/bin/env python3
"""Safe analyzer+anonymizer smoke for Presidio text workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Tuple

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NoOpNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

DEFAULT_TEXT = "Employee code ACME-1234 should be anonymized."
DEFAULT_ENTITY = "PROJECT_CODE"
DEFAULT_PATTERN = r"\bACME-\d{4}\b"
DEFAULT_REPLACEMENT = "<PROJECT_CODE>"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a safe Presidio analyzer+anonymizer smoke using either the installed "
            "default NLP model or a no-op fallback with an ad hoc pattern recognizer."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "default-model", "no-op"),
        default="auto",
        help=(
            "Analyzer mode. 'auto' tries the installed default model and falls back "
            "to no-op if the default model is unavailable."
        ),
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code to use for the analyzer and recognizer.",
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Text to analyze and anonymize.",
    )
    parser.add_argument(
        "--entity-type",
        default=DEFAULT_ENTITY,
        help="Entity name used by the custom pattern recognizer.",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Regular expression used by the custom pattern recognizer.",
    )
    parser.add_argument(
        "--replacement",
        default=DEFAULT_REPLACEMENT,
        help="Replacement text used by the replace operator.",
    )
    return parser


def build_analyzer(language: str, mode: str) -> Tuple[AnalyzerEngine, str]:
    if mode in {"auto", "default-model"}:
        try:
            return AnalyzerEngine(supported_languages=[language]), "default-model"
        except Exception:
            if mode == "default-model":
                raise

    no_op_engine = NoOpNlpEngine(
        models=[{"lang_code": language, "model_name": "no_op"}]
    )
    return (
        AnalyzerEngine(nlp_engine=no_op_engine, supported_languages=[language]),
        "no-op",
    )


def analyze_text(args: argparse.Namespace):
    analyzer, analyzer_mode = build_analyzer(args.language, args.mode)
    recognizer = PatternRecognizer(
        supported_entity=args.entity_type,
        name=f"{args.entity_type.lower()}_pattern",
        supported_language=args.language,
        patterns=[Pattern(name="match", regex=args.pattern, score=0.9)],
    )
    results = analyzer.analyze(
        text=args.text,
        language=args.language,
        entities=[args.entity_type],
        ad_hoc_recognizers=[recognizer],
    )
    return analyzer_mode, results


def anonymize_text(args: argparse.Namespace, analyzer_results):
    engine = AnonymizerEngine()
    operators = {
        args.entity_type: OperatorConfig(
            "replace", {"new_value": args.replacement}
        )
    }
    return engine.anonymize(
        text=args.text,
        analyzer_results=analyzer_results,
        operators=operators,
    )


def result_to_dict(mode: str, analyzer_results, anonymized_result) -> dict:
    return {
        "analysis_mode": mode,
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
        analyzer_mode, analyzer_results = analyze_text(args)
        if not analyzer_results:
            parser.error(
                "The sample pattern did not match. Adjust --text or --pattern."
            )
        anonymized_result = anonymize_text(args, analyzer_results)
    except Exception as exc:
        print(f"Smoke failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            result_to_dict(analyzer_mode, analyzer_results, anonymized_result),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
