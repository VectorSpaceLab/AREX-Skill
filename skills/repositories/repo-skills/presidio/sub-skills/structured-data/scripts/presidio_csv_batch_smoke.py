#!/usr/bin/env python3
"""Safe CSV batch analyzer/anonymizer smoke for Presidio.

If --csv is omitted, this script creates a tiny temporary CSV fixture. The
analysis uses a no-download AnalyzerEngine with local PatternRecognizer rules,
then anonymizes the column dictionary with BatchAnonymizerEngine.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_LANGUAGE = "en"
DEFAULT_SKIP_COLUMNS = ["id"]

FIXTURE_ROWS = [
    {
        "id": "1",
        "name": "Alice Doe",
        "email": "alice@example.com",
        "comments": "Call 212-555-0101 about PRJ-1001.",
    },
    {
        "id": "2",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "comments": "Escalate PRJ-1002 to Bob Smith.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a self-contained Presidio CSV batch smoke. Provide --csv to "
            "anonymize a small CSV, or omit it to use a generated tiny fixture."
        )
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional input CSV path. If omitted, a tiny fixture is generated.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional path where anonymized rows should be written.",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Analyzer language code for the no-op recognizers (default: en).",
    )
    parser.add_argument(
        "--skip-columns",
        nargs="*",
        default=DEFAULT_SKIP_COLUMNS,
        help="CSV columns to preserve without analysis (default: id).",
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
            name="fixture_names",
            supported_language=language,
            patterns=[
                Pattern(
                    name="fixture full names",
                    regex=r"\b(?:Alice Doe|Bob Smith)\b",
                    score=0.9,
                )
            ],
        ),
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            name="fixture_emails",
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
            supported_entity="PHONE_NUMBER",
            name="fixture_phone_numbers",
            supported_language=language,
            patterns=[
                Pattern(
                    name="north america sample phone",
                    regex=r"\b\d{3}-\d{3}-\d{4}\b",
                    score=0.85,
                )
            ],
        ),
        PatternRecognizer(
            supported_entity="PROJECT_CODE",
            name="fixture_project_codes",
            supported_language=language,
            patterns=[
                Pattern(name="project code", regex=r"\bPRJ-\d{4}\b", score=0.85)
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
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
        "PROJECT_CODE": OperatorConfig("replace", {"new_value": "<PROJECT_CODE>"}),
        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
    }


def write_fixture_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIXTURE_ROWS[0]))
        writer.writeheader()
        writer.writerows(FIXTURE_ROWS)


def read_csv_as_columns(path: Path) -> Tuple[List[str], Dict[str, List[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("CSV must contain a header row")
        columns: Dict[str, List[str]] = {field: [] for field in fieldnames}
        for row in reader:
            for field in fieldnames:
                columns[field].append(row.get(field, ""))
    if not any(columns.values()):
        raise ValueError("CSV must contain at least one data row")
    return fieldnames, columns


def columns_to_rows(fieldnames: List[str], columns: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    row_count = max((len(values) for values in columns.values()), default=0)
    rows: List[Dict[str, Any]] = []
    for idx in range(row_count):
        rows.append(
            {
                field: columns.get(field, [""] * row_count)[idx]
                if idx < len(columns.get(field, []))
                else ""
                for field in fieldnames
            }
        )
    return rows


def anonymize_columns(
    columns: Dict[str, List[str]],
    language: str,
    skip_columns: List[str],
) -> Dict[str, List[str]]:
    from presidio_analyzer import BatchAnalyzerEngine
    from presidio_anonymizer import BatchAnonymizerEngine

    analyzer = BatchAnalyzerEngine(analyzer_engine=build_no_download_analyzer(language))
    analyzer_results = list(
        analyzer.analyze_dict(
            columns,
            language=language,
            keys_to_skip=skip_columns,
            batch_size=1,
            n_process=1,
        )
    )
    return BatchAnonymizerEngine().anonymize_dict(
        analyzer_results,
        operators=build_operators(),
    )


def write_output_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> Dict[str, Any]:
    using_fixture = args.csv is None
    with tempfile.TemporaryDirectory(prefix="presidio-csv-smoke-") as tmp_dir:
        input_path = args.csv
        if input_path is None:
            input_path = Path(tmp_dir) / "fixture.csv"
            write_fixture_csv(input_path)

        fieldnames, columns = read_csv_as_columns(input_path)
        anonymized_columns = anonymize_columns(columns, args.language, args.skip_columns)
        anonymized_rows = columns_to_rows(fieldnames, anonymized_columns)

        if using_fixture:
            assert [row["id"] for row in anonymized_rows] == ["1", "2"]
            assert [row["name"] for row in anonymized_rows] == ["<PERSON>", "<PERSON>"]
            assert [row["email"] for row in anonymized_rows] == ["<EMAIL>", "<EMAIL>"]
            assert "<PHONE>" in anonymized_rows[0]["comments"]
            assert "<PROJECT_CODE>" in anonymized_rows[1]["comments"]

        if args.output_csv is not None:
            write_output_csv(args.output_csv, fieldnames, anonymized_rows)

    return {
        "status": "passed",
        "fixture": using_fixture,
        "fieldnames": fieldnames,
        "skip_columns": args.skip_columns,
        "rows": anonymized_rows,
        "wrote_output_csv": args.output_csv is not None,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = run(args)
    except Exception as exc:  # pragma: no cover - smoke script boundary
        print(f"CSV batch smoke failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
