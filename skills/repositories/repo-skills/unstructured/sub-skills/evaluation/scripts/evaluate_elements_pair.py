#!/usr/bin/env python3
"""Compare one predicted Unstructured element JSON file with one gold element JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import difflib
import re
from collections import Counter

try:
    from unstructured.metrics.element_type import (
        calculate_element_type_percent_match,
        get_element_type_frequency,
    )
except ImportError:
    calculate_element_type_percent_match = None
    get_element_type_frequency = None

try:
    from unstructured.metrics.text_extraction import calculate_accuracy, calculate_percent_missing_text
except ImportError:
    calculate_accuracy = None
    calculate_percent_missing_text = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one predicted Unstructured element JSON file with one gold element JSON file. "
            "The script intentionally avoids unstructured.metrics.evaluate so text, element, and "
            "table checks do not import torch-backed object detection metrics."
        )
    )
    parser.add_argument("--prediction", required=True, type=Path, help="Predicted element JSON file")
    parser.add_argument("--gold", required=True, type=Path, help="Gold element JSON file")
    parser.add_argument(
        "--table-source",
        choices=("auto", "html", "cells", "skip"),
        default="auto",
        help="Read predicted table data from text_as_html, table_as_cells, choose automatically, or skip",
    )
    parser.add_argument(
        "--table-cutoff",
        type=float,
        default=0.8,
        help="Similarity cutoff for table element-level alignment",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Print machine-readable JSON instead of a compact text report",
    )
    return parser.parse_args()


def load_elements(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: malformed JSON: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"{path}: cannot read file: {exc}") from exc

    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a JSON array of element objects")
    if not all(isinstance(item, dict) for item in data):
        raise SystemExit(f"{path}: expected every array item to be an element object")
    return data


def elements_text(elements: Iterable[dict[str, Any]]) -> str:
    return "\n\n".join(str(element.get("text") or "") for element in elements).strip()


def ensure_metadata(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for element in elements:
        item = dict(element)
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            item["metadata"] = {}
        normalized.append(item)
    return normalized


def fallback_accuracy(output: str, source: str) -> float:
    if not source:
        return 1.0 if not output else 0.0
    return max(0.0, min(1.0, difflib.SequenceMatcher(None, output, source).ratio()))


def fallback_percent_missing(output: str, source: str) -> float:
    output_words = Counter(re.findall(r"\b\w+\b", output.lower()))
    source_words = Counter(re.findall(r"\b\w+\b", source.lower()))
    total = sum(source_words.values())
    if total == 0:
        return 0.0
    missing = sum(max(count - output_words.get(word, 0), 0) for word, count in source_words.items())
    return min(1.0, round(missing / total, 3))


def element_type_metrics(prediction: list[dict[str, Any]], gold: list[dict[str, Any]]) -> dict[str, Any]:
    if get_element_type_frequency and calculate_element_type_percent_match:
        prediction_json = json.dumps(ensure_metadata(prediction), ensure_ascii=False)
        gold_json = json.dumps(ensure_metadata(gold), ensure_ascii=False)
        prediction_frequency = get_element_type_frequency(prediction_json)
        gold_frequency = get_element_type_frequency(gold_json)
        accuracy = calculate_element_type_percent_match(prediction_frequency, gold_frequency)
    else:
        prediction_frequency = fallback_element_frequency(prediction)
        gold_frequency = fallback_element_frequency(gold)
        accuracy = fallback_element_accuracy(prediction_frequency, gold_frequency)
    return {
        "element_type_accuracy": round(accuracy, 3),
        "prediction_frequency": stringify_frequency(prediction_frequency),
        "gold_frequency": stringify_frequency(gold_frequency),
    }


def fallback_element_frequency(elements: list[dict[str, Any]]) -> dict[tuple[str, int | None], int]:
    frequency: dict[tuple[str, int | None], int] = {}
    for element in elements:
        metadata = element.get("metadata") if isinstance(element.get("metadata"), dict) else {}
        key = (str(element.get("type")), metadata.get("category_depth"))
        frequency[key] = frequency.get(key, 0) + 1
    return frequency


def fallback_element_accuracy(
    prediction_frequency: dict[tuple[str, int | None], int],
    gold_frequency: dict[tuple[str, int | None], int],
) -> float:
    total = sum(gold_frequency.values())
    if not total:
        return 0.0
    matches = sum(min(prediction_frequency.get(key, 0), count) for key, count in gold_frequency.items())
    return min(1.0, max(0.0, matches / total))


def stringify_frequency(frequency: dict[tuple[str, int | None], int]) -> dict[str, int]:
    return {f"{element_type}|depth={depth}": count for (element_type, depth), count in frequency.items()}


def has_html_tables(elements: Iterable[dict[str, Any]]) -> bool:
    for element in elements:
        metadata = element.get("metadata") or {}
        if element.get("type") == "Table" and isinstance(metadata, dict):
            text_as_html = metadata.get("text_as_html")
            if isinstance(text_as_html, str) and "<table" in text_as_html.lower():
                return True
    return False


def has_cell_tables(elements: Iterable[dict[str, Any]]) -> bool:
    for element in elements:
        metadata = element.get("metadata") or {}
        if element.get("type") == "Table" and isinstance(metadata, dict):
            if isinstance(metadata.get("table_as_cells"), list):
                return True
    return False


def has_gold_tables(elements: Iterable[dict[str, Any]]) -> bool:
    return any(element.get("type") == "Table" for element in elements)


def choose_table_source(prediction: list[dict[str, Any]], requested: str) -> str | None:
    if requested == "skip":
        return None
    if requested in {"html", "cells"}:
        return requested
    if has_cell_tables(prediction):
        return "cells"
    if has_html_tables(prediction):
        return "html"
    return None


def table_metrics(
    prediction: list[dict[str, Any]], gold: list[dict[str, Any]], source_type: str, cutoff: float
) -> dict[str, Any]:
    try:
        from unstructured.metrics.table.table_eval import TableEvalProcessor
    except ImportError as exc:
        raise RuntimeError(
            "table metrics require the package's table metric dependencies, including numpy"
        ) from exc

    processor = TableEvalProcessor(
        prediction=prediction,
        ground_truth=gold,
        cutoff=cutoff,
        source_type=source_type,
    )
    report = processor.process_file()
    return asdict(report) | {"composite_structure_acc": report.composite_structure_acc}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    prediction = load_elements(args.prediction)
    gold = load_elements(args.gold)
    prediction_text = elements_text(prediction)
    gold_text = elements_text(gold)

    report: dict[str, Any] = {
        "prediction_file": str(args.prediction),
        "gold_file": str(args.gold),
        "prediction_element_count": len(prediction),
        "gold_element_count": len(gold),
        "text_accuracy": round(
            calculate_accuracy(prediction_text, gold_text)
            if calculate_accuracy
            else fallback_accuracy(prediction_text, gold_text),
            3,
        ),
        "text_percent_missing": round(
            calculate_percent_missing_text(prediction_text, gold_text)
            if calculate_percent_missing_text
            else fallback_percent_missing(prediction_text, gold_text),
            3,
        ),
    }
    report.update(element_type_metrics(prediction, gold))

    source_type = choose_table_source(prediction, args.table_source)
    if source_type and has_gold_tables(gold):
        try:
            report["table_source"] = source_type
            report["table_metrics"] = table_metrics(prediction, gold, source_type, args.table_cutoff)
        except Exception as exc:  # table conversion can fail on malformed HTML/cells
            report["table_error"] = f"{type(exc).__name__}: {exc}"
    else:
        report["table_source"] = source_type or "not available"
        report["table_metrics"] = None
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Prediction: {report['prediction_file']}")
    print(f"Gold:       {report['gold_file']}")
    print(
        "Elements:   "
        f"prediction={report['prediction_element_count']} gold={report['gold_element_count']}"
    )
    print(f"Text:       accuracy={report['text_accuracy']} missing={report['text_percent_missing']}")
    print(f"Types:      accuracy={report['element_type_accuracy']}")
    print("Predicted type frequency:")
    for key, count in sorted(report["prediction_frequency"].items()):
        print(f"  - {key}: {count}")
    print("Gold type frequency:")
    for key, count in sorted(report["gold_frequency"].items()):
        print(f"  - {key}: {count}")
    if report.get("table_error"):
        print(f"Table:      error={report['table_error']}")
    elif report.get("table_metrics"):
        print(f"Table:      source={report['table_source']}")
        for key, value in report["table_metrics"].items():
            print(f"  - {key}: {value}")
    else:
        print(f"Table:      skipped ({report['table_source']})")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
