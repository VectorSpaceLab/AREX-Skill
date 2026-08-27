#!/usr/bin/env python3
"""Mirror Semantra's browser query parsing and weight normalization.

The web UI parses plus/minus or numeric prefixes, then rescales positive query
terms/preferences to about 0.618 and negative terms/preferences to about 0.382.
This standalone helper does not import Semantra or start a server.

Examples:
  python parse_semantra_query.py "economic growth - unchecked capitalism + war"
  python parse_semantra_query.py "dog +1.2 cat" --positive-preferences 1 --json
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

POSITIVE_RATIO = 0.61803398875
NEGATIVE_RATIO = 1 - POSITIVE_RATIO
QUERY_RE = re.compile(r"([\+\-]?\d*\.?\d*\s*)?([^\+\-]+)")


def js_like_parse_float(text: str | None) -> float | None:
    if text is None:
        return None
    stripped = text.strip()
    if stripped in {"", "+", "-", ".", "+.", "-."}:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def parse_query(query: str) -> list[dict[str, Any]]:
    parsed = []
    for match in QUERY_RE.finditer(query):
        prefix, term = match.groups()
        term = term.strip()
        if not term:
            continue
        parsed_float = js_like_parse_float(prefix)
        if parsed_float is not None and parsed_float != 0:
            weight = parsed_float
        elif prefix and "-" in prefix:
            weight = -1.0
        else:
            weight = 1.0
        parsed.append({"query": term, "raw_weight": weight, "weight": weight})
    return parsed


def normalize(parsed: list[dict[str, Any]], positive_preferences: int, negative_preferences: int) -> dict[str, Any]:
    total_positive = sum(1 for item in parsed if item["weight"] > 0) + positive_preferences
    total_negative = sum(1 for item in parsed if item["weight"] < 0) + negative_preferences
    normalized = []
    for item in parsed:
        new_item = dict(item)
        if item["weight"] > 0 and total_positive:
            new_item["weight"] = item["weight"] * POSITIVE_RATIO / total_positive
        elif item["weight"] < 0 and total_negative:
            new_item["weight"] = item["weight"] * NEGATIVE_RATIO / total_negative
        normalized.append(new_item)
    return {
        "queries": normalized,
        "positive_preferences": positive_preferences,
        "negative_preferences": negative_preferences,
        "total_positive_count": total_positive,
        "total_negative_count": total_negative,
        "positive_ratio": POSITIVE_RATIO,
        "negative_ratio": NEGATIVE_RATIO,
        "note": "Semantra counts terms/preferences when splitting ratios; explicit numeric weights are multiplied by the per-item share rather than normalized by total absolute weight.",
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Positive item count: {report['total_positive_count']}")
    print(f"Negative item count: {report['total_negative_count']}")
    print("Queries:")
    for item in report["queries"]:
        print(
            f"  - {item['query']!r}: raw_weight={item['raw_weight']} normalized_weight={item['weight']:.12g}"
        )
    if report["positive_preferences"] or report["negative_preferences"]:
        print(
            "Preference counts are included in normalization but their individual search-result embeddings are not shown by this parser."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Raw query string as typed in Semantra's search bar.")
    parser.add_argument("--positive-preferences", type=int, default=0, help="Count of positively tagged results.")
    parser.add_argument("--negative-preferences", type=int, default=0, help="Count of negatively tagged results.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    if args.positive_preferences < 0 or args.negative_preferences < 0:
        parser.error("preference counts must be non-negative")
    report = normalize(parse_query(args.query), args.positive_preferences, args.negative_preferences)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
