#!/usr/bin/env python3
"""Inspect Khoj query filter parsing without starting the Khoj server."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from typing import Any



def load_filter_classes() -> tuple[type[Any], type[Any], type[Any]]:
    try:
        from khoj.search_filter.date_filter import DateFilter
        from khoj.search_filter.file_filter import FileFilter
        from khoj.search_filter.word_filter import WordFilter
    except ModuleNotFoundError as error:
        if error.name == "khoj":
            raise SystemExit(
                "The khoj package is not importable. Run this helper in an environment where Khoj is installed."
            ) from error
        raise
    return DateFilter, FileFilter, WordFilter


def parse_relative_base(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "--relative-base must be an ISO datetime such as 1984-04-01T21:21:21"
        ) from error


def normalize_datetime_range(parsed: tuple[datetime, datetime] | None) -> list[str] | None:
    if parsed is None:
        return None
    return [item.isoformat() for item in parsed]


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Khoj DateFilter, FileFilter, and WordFilter parsing for a query.")
    parser.add_argument("query", help="Khoj search query containing optional dt/file/word filters")
    parser.add_argument(
        "--relative-base",
        type=parse_relative_base,
        default=None,
        help="ISO datetime used when demonstrating relative date phrase parsing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a readable text report",
    )
    args = parser.parse_args()

    DateFilter, FileFilter, WordFilter = load_filter_classes()
    date_filter = DateFilter()
    file_filter = FileFilter()
    word_filter = WordFilter()

    date_terms = date_filter.get_filter_terms(args.query)
    file_terms = file_filter.get_filter_terms(args.query)
    word_terms = word_filter.get_filter_terms(args.query)

    defiltered_by_filter = {
        "date": date_filter.defilter(args.query),
        "word": word_filter.defilter(args.query),
        "file": file_filter.defilter(args.query),
    }

    combined_defiltered = args.query
    for filter_instance in (date_filter, word_filter, file_filter):
        combined_defiltered = filter_instance.defilter(combined_defiltered)

    date_phrase_ranges: dict[str, Any] = {}
    for comparator, phrase in re.findall(date_filter.date_regex, args.query):
        date_phrase_ranges[f"dt{comparator}{phrase!r}"] = normalize_datetime_range(
            date_filter.parse(phrase, relative_base=args.relative_base)
        )

    report = {
        "query": args.query,
        "filter_terms": {
            "date": date_terms,
            "file": file_terms,
            "word": word_terms,
        },
        "date_range_timestamps": date_filter.extract_date_range(args.query),
        "date_phrase_ranges": date_phrase_ranges,
        "defiltered_by_filter": defiltered_by_filter,
        "combined_defiltered": combined_defiltered,
        "notes": [
            "FileFilter.defilter removes include filters but may leave -file exclusions in the embedded text.",
            "WordFilter terms are limited to letters, digits, underscores, and hyphens.",
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"Query: {report['query']}")
    print("\nFilter terms:")
    for filter_name, terms in report["filter_terms"].items():
        print(f"  {filter_name}: {terms}")
    print(f"\nDate range timestamps: {report['date_range_timestamps']}")
    print("Date phrase ranges:")
    for term, parsed_range in date_phrase_ranges.items():
        print(f"  {term}: {parsed_range}")
    print("\nDefiltered by individual filter:")
    for filter_name, value in defiltered_by_filter.items():
        print(f"  {filter_name}: {value}")
    print(f"\nCombined defiltered query: {combined_defiltered}")
    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
