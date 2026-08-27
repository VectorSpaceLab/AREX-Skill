#!/usr/bin/env python3
"""Safe smoke checks for Presidio Structured DataFrame and JSON workflows.

The script uses tiny in-memory fixtures and a no-download AnalyzerEngine built
from local PatternRecognizer instances. It demonstrates automatic DataFrame
analysis, a manual mapping override, and manual dot-path mapping for nested
JSON arrays.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from typing import Any, Dict, Iterable, Tuple

DEFAULT_LANGUAGE = "en"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run self-contained Presidio Structured smoke checks for Pandas "
            "DataFrames and JSON-like data. No source checkout or model download "
            "is required."
        )
    )
    parser.add_argument(
        "--case",
        choices=("both", "dataframe", "json"),
        default="both",
        help="Which smoke case to run (default: both).",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Analyzer language code for the no-op recognizers (default: en).",
    )
    parser.add_argument(
        "--selection-strategy",
        choices=("most_common", "highest_confidence", "mixed"),
        default="most_common",
        help="PandasAnalysisBuilder entity-selection strategy for the DataFrame case.",
    )
    parser.add_argument(
        "--mixed-strategy-threshold",
        type=float,
        default=0.5,
        help="Threshold used only when --selection-strategy=mixed.",
    )
    return parser


def build_no_download_analyzer(language: str):
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NoOpNlpEngine

    nlp_engine = NoOpNlpEngine(models=[{"lang_code": language, "model_name": "no_op"}])
    nlp_engine.load()

    recognizers = [
        PatternRecognizer(
            supported_entity="PERSON",
            name="sample_person_names",
            supported_language=language,
            patterns=[
                Pattern(
                    name="sample full names",
                    regex=r"\b(?:Alice Doe|Bob Smith|Carol Jones)\b",
                    score=0.9,
                )
            ],
        ),
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            name="sample_email_addresses",
            supported_language=language,
            patterns=[
                Pattern(
                    name="example.com email",
                    regex=r"\b[A-Za-z0-9._%+-]+@example\.com\b",
                    score=0.95,
                )
            ],
        ),
        PatternRecognizer(
            supported_entity="PROJECT_CODE",
            name="sample_project_codes",
            supported_language=language,
            patterns=[
                Pattern(
                    name="project code",
                    regex=r"\bPRJ-\d{4}\b",
                    score=0.85,
                )
            ],
        ),
    ]
    registry = RecognizerRegistry(recognizers=recognizers, supported_languages=[language])
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=[language],
    )


def build_operators() -> Dict[str, Any]:
    from presidio_anonymizer.entities import OperatorConfig

    return {
        "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        "EMPLOYEE_LOGIN": OperatorConfig("replace", {"new_value": "<LOGIN>"}),
        "PROJECT_CODE": OperatorConfig("replace", {"new_value": "<PROJECT_CODE>"}),
        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
    }


def run_dataframe_case(args: argparse.Namespace, analyzer, operators) -> Dict[str, Any]:
    import pandas as pd
    from presidio_structured import PandasAnalysisBuilder, StructuredAnalysis, StructuredEngine

    df = pd.DataFrame(
        {
            "full_name": ["Alice Doe", "Bob Smith"],
            # The analyzer sees emails, but this workflow wants login-specific treatment.
            "employee_login": ["alice@example.com", "bob@example.com"],
            "support_ticket": ["PRJ-1001", "PRJ-1002"],
            "department": ["research", "operations"],
        }
    )

    auto_analysis = PandasAnalysisBuilder(analyzer=analyzer).generate_analysis(
        df,
        language=args.language,
        selection_strategy=args.selection_strategy,
        mixed_strategy_threshold=args.mixed_strategy_threshold,
    )
    manual_mapping = dict(auto_analysis.entity_mapping)
    manual_mapping["employee_login"] = "EMPLOYEE_LOGIN"
    manual_analysis = StructuredAnalysis(entity_mapping=manual_mapping)

    result_df = StructuredEngine().anonymize(df.copy(deep=True), manual_analysis, operators)

    assert result_df["full_name"].tolist() == ["<PERSON>", "<PERSON>"]
    assert result_df["employee_login"].tolist() == ["<LOGIN>", "<LOGIN>"]
    assert result_df["support_ticket"].tolist() == ["<PROJECT_CODE>", "<PROJECT_CODE>"]
    assert result_df["department"].tolist() == ["research", "operations"]

    return {
        "auto_mapping": dict(sorted(auto_analysis.entity_mapping.items())),
        "manual_mapping": dict(sorted(manual_analysis.entity_mapping.items())),
        "records": result_df.to_dict(orient="records"),
    }


def run_json_case(args: argparse.Namespace, operators) -> Dict[str, Any]:
    from presidio_structured import JsonDataProcessor, StructuredAnalysis, StructuredEngine

    payload = {
        "users": [
            {"name": "Alice Doe", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
        "metadata": {"owner": "Carol Jones", "ticket": "PRJ-1003"},
        "public_note": "release after review",
    }
    manual_analysis = StructuredAnalysis(
        entity_mapping={
            "users.name": "PERSON",
            "users.email": "EMAIL_ADDRESS",
            "metadata.owner": "PERSON",
            "metadata.ticket": "PROJECT_CODE",
        }
    )

    result = StructuredEngine(data_processor=JsonDataProcessor()).anonymize(
        deepcopy(payload), manual_analysis, operators
    )

    assert [user["name"] for user in result["users"]] == ["<PERSON>", "<PERSON>"]
    assert [user["email"] for user in result["users"]] == ["<EMAIL>", "<EMAIL>"]
    assert result["metadata"] == {"owner": "<PERSON>", "ticket": "<PROJECT_CODE>"}
    assert result["public_note"] == payload["public_note"]

    return {
        "manual_mapping": dict(sorted(manual_analysis.entity_mapping.items())),
        "payload": result,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        analyzer = build_no_download_analyzer(args.language)
        operators = build_operators()
        report: Dict[str, Any] = {"status": "passed", "case": args.case}
        if args.case in {"both", "dataframe"}:
            report["dataframe"] = run_dataframe_case(args, analyzer, operators)
        if args.case in {"both", "json"}:
            report["json"] = run_json_case(args, operators)
    except Exception as exc:  # pragma: no cover - smoke script boundary
        print(f"Structured smoke failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
