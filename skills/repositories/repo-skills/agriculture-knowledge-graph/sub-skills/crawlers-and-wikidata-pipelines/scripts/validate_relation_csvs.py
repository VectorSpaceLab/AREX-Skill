#!/usr/bin/env python3
"""Validate Agriculture_KnowledgeGraph relation/weather CSV artifacts.

The checker is intentionally offline: it performs no network calls, no Neo4j
queries, and no imports from the original repository. It validates headers,
row widths, non-empty key fields, duplicate/suspicious rows, and the
wikidata_relation2.csv -> new_node.csv target relationship.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

FILE_SPECS = {
    "wikidata_relation": {
        "filename": "wikidata_relation.csv",
        "header": ["HudongItem1", "relation", "HudongItem2"],
        "required": ["HudongItem1", "relation", "HudongItem2"],
    },
    "wikidata_relation2": {
        "filename": "wikidata_relation2.csv",
        "header": ["HudongItem", "relation", "NewNode"],
        "required": ["HudongItem", "relation", "NewNode"],
    },
    "new_node": {
        "filename": "new_node.csv",
        "header": ["title", "lable"],
        "alternate_headers": [["title", "label"]],
        "required": ["title"],
    },
    "weather_plant": {
        "filename": "weather_plant.csv",
        "header": ["Weather", "relation", "Plant"],
        "required": ["Weather", "relation", "Plant"],
        "expected_relation": "适合种植",
    },
    "city_weather": {
        "filename": "city_weather.csv",
        "header": ["city", "relation", "weather"],
        "required": ["city", "relation", "weather"],
        "expected_relation": "气候",
    },
}

Issue = Tuple[str, str, Optional[int], str]


def add_issue(issues: List[Issue], severity: str, file_id: str, line: Optional[int], message: str) -> None:
    issues.append((severity, file_id, line, message))


def normalize_header(header: Sequence[str]) -> List[str]:
    return [cell.strip().lstrip("\ufeff") for cell in header]


def has_suspicious_delimiter(value: str) -> bool:
    return any(ch in value for ch in [",", '"', "\n", "\r"])


def row_tuple(row: Dict[str, str], columns: Sequence[str]) -> Tuple[str, ...]:
    return tuple((row.get(column) or "").strip() for column in columns)


def read_csv_file(
    file_id: str,
    path: Path,
    max_rows: int,
    issues: List[Issue],
) -> Tuple[List[str], List[Dict[str, str]]]:
    spec = FILE_SPECS[file_id]
    expected_header = list(spec["header"])
    alternate_headers = [list(item) for item in spec.get("alternate_headers", [])]

    rows: List[Dict[str, str]] = []
    if not path.exists():
        add_issue(issues, "ERROR", file_id, None, f"missing file: {path}")
        return expected_header, rows

    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        add_issue(issues, "ERROR", file_id, None, f"cannot open {path}: {exc}")
        return expected_header, rows

    with handle:
        reader = csv.reader(handle)
        try:
            raw_header = next(reader)
        except StopIteration:
            add_issue(issues, "ERROR", file_id, 1, "empty CSV file")
            return expected_header, rows

        header = normalize_header(raw_header)
        if header == expected_header:
            effective_header = expected_header
        elif header in alternate_headers:
            effective_header = header
            add_issue(
                issues,
                "WARN",
                file_id,
                1,
                f"header {header!r} uses an accepted alias; source-compatible header is {expected_header!r}",
            )
        else:
            add_issue(issues, "ERROR", file_id, 1, f"header {header!r} != expected {expected_header!r}")
            effective_header = header

        for line_number, raw_row in enumerate(reader, start=2):
            if max_rows and len(rows) >= max_rows:
                break
            if not raw_row or all(not cell.strip() for cell in raw_row):
                add_issue(issues, "WARN", file_id, line_number, "blank row ignored")
                continue
            if len(raw_row) != len(effective_header):
                add_issue(
                    issues,
                    "ERROR",
                    file_id,
                    line_number,
                    f"expected {len(effective_header)} columns, found {len(raw_row)} columns",
                )
                continue
            row = {column: value.strip() for column, value in zip(effective_header, raw_row)}
            rows.append(row)

    return effective_header, rows


def validate_rows(file_id: str, header: Sequence[str], rows: List[Dict[str, str]], issues: List[Issue]) -> None:
    spec = FILE_SPECS[file_id]
    required = list(spec["required"])
    relation_value = spec.get("expected_relation")
    duplicate_counter: Counter[Tuple[str, ...]] = Counter()

    for index, row in enumerate(rows, start=2):
        for column in required:
            if column not in row:
                add_issue(issues, "ERROR", file_id, index, f"required column {column!r} is absent")
                continue
            if not row[column]:
                add_issue(issues, "ERROR", file_id, index, f"required column {column!r} is empty")

        for column in header:
            value = row.get(column, "")
            if value and has_suspicious_delimiter(value):
                add_issue(
                    issues,
                    "WARN",
                    file_id,
                    index,
                    f"field {column!r} contains comma, quote, or newline; review before source-style LOAD CSV",
                )

        if relation_value is not None and row.get("relation") and row.get("relation") != relation_value:
            add_issue(
                issues,
                "WARN",
                file_id,
                index,
                f"relation value {row.get('relation')!r} differs from expected {relation_value!r}",
            )

        if file_id == "new_node":
            label_value = row.get("lable", row.get("label", ""))
            if label_value and label_value != "newNode":
                add_issue(issues, "ERROR", file_id, index, f"new node label should be 'newNode', found {label_value!r}")

        duplicate_counter[row_tuple(row, header)] += 1

    for row_values, count in duplicate_counter.items():
        if count > 1:
            add_issue(issues, "WARN", file_id, None, f"duplicate row appears {count} times: {row_values!r}")


def validate_cross_file(rows_by_file: Dict[str, List[Dict[str, str]]], issues: List[Issue]) -> None:
    new_node_titles = {row.get("title", "") for row in rows_by_file.get("new_node", []) if row.get("title")}
    if new_node_titles and rows_by_file.get("wikidata_relation2"):
        missing = []
        for index, row in enumerate(rows_by_file["wikidata_relation2"], start=2):
            target = row.get("NewNode", "")
            if target and target not in new_node_titles:
                missing.append((index, target))
                if len(missing) <= 20:
                    add_issue(
                        issues,
                        "ERROR",
                        "wikidata_relation2",
                        index,
                        f"NewNode target {target!r} is absent from new_node.csv",
                    )
        if len(missing) > 20:
            add_issue(
                issues,
                "ERROR",
                "wikidata_relation2",
                None,
                f"{len(missing) - 20} additional NewNode targets are absent from new_node.csv",
            )

    titles = [row.get("title", "") for row in rows_by_file.get("new_node", []) if row.get("title")]
    duplicate_titles = [title for title, count in Counter(titles).items() if count > 1]
    for title in duplicate_titles[:20]:
        add_issue(issues, "ERROR", "new_node", None, f"duplicate new_node title {title!r}")
    if len(duplicate_titles) > 20:
        add_issue(issues, "ERROR", "new_node", None, f"{len(duplicate_titles) - 20} additional duplicate new_node titles")


def resolve_paths(args: argparse.Namespace) -> Dict[str, Path]:
    root = Path(args.root)
    return {
        file_id: Path(getattr(args, file_id)) if getattr(args, file_id) else root / str(spec["filename"])
        for file_id, spec in FILE_SPECS.items()
    }


def run_validation(paths: Dict[str, Path], max_rows: int = 0) -> Dict[str, object]:
    issues: List[Issue] = []
    headers_by_file: Dict[str, List[str]] = {}
    rows_by_file: Dict[str, List[Dict[str, str]]] = {}

    for file_id in FILE_SPECS:
        header, rows = read_csv_file(file_id, paths[file_id], max_rows=max_rows, issues=issues)
        headers_by_file[file_id] = list(header)
        rows_by_file[file_id] = rows
        validate_rows(file_id, header, rows, issues)

    validate_cross_file(rows_by_file, issues)

    counts = {
        file_id: {
            "path": str(paths[file_id]),
            "rows_checked": len(rows_by_file.get(file_id, [])),
            "header": headers_by_file.get(file_id, []),
        }
        for file_id in FILE_SPECS
    }
    error_count = sum(1 for severity, _, _, _ in issues if severity == "ERROR")
    warning_count = sum(1 for severity, _, _, _ in issues if severity == "WARN")
    return {
        "counts": counts,
        "issues": [
            {"severity": severity, "file": file_id, "line": line, "message": message}
            for severity, file_id, line, message in issues
        ],
        "errors": error_count,
        "warnings": warning_count,
    }


def write_fixture(root: Path) -> None:
    fixtures = {
        "wikidata_relation.csv": [
            ["HudongItem1", "relation", "HudongItem2"],
            ["菊糖", "instance of", "化合物"],
            ["苹果", "subclass of", "水果"],
        ],
        "wikidata_relation2.csv": [
            ["HudongItem", "relation", "NewNode"],
            ["菊糖", "described by source", "示例新节点"],
            ["苹果", "country of origin", "示例产地"],
        ],
        "new_node.csv": [
            ["title", "lable"],
            ["示例新节点", "newNode"],
            ["示例产地", "newNode"],
        ],
        "weather_plant.csv": [
            ["Weather", "relation", "Plant"],
            ["亚热带季风气候", "适合种植", "水稻"],
        ],
        "city_weather.csv": [
            ["city", "relation", "weather"],
            ["上海市", "气候", "亚热带季风气候"],
        ],
    }
    for filename, rows in fixtures.items():
        with (root / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)


def print_text_report(result: Dict[str, object], fail_on_warning: bool) -> None:
    counts = result["counts"]  # type: ignore[index]
    assert isinstance(counts, dict)
    for file_id in FILE_SPECS:
        item = counts[file_id]
        assert isinstance(item, dict)
        print(f"{file_id}: {item['rows_checked']} row(s) checked at {item['path']}")

    issues = result["issues"]  # type: ignore[index]
    assert isinstance(issues, list)
    for issue in issues:
        assert isinstance(issue, dict)
        location = issue["file"]
        if issue.get("line") is not None:
            location = f"{location}:{issue['line']}"
        print(f"{issue['severity']}: {location}: {issue['message']}")

    errors = int(result["errors"])  # type: ignore[arg-type]
    warnings = int(result["warnings"])  # type: ignore[arg-type]
    status = "PASS" if errors == 0 and (not fail_on_warning or warnings == 0) else "FAIL"
    print(f"{status}: {errors} error(s), {warnings} warning(s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline schema/invariant checks for Agriculture_KnowledgeGraph relation and weather CSVs."
    )
    parser.add_argument("--root", default=".", help="Directory containing the five expected CSV files (default: current directory).")
    parser.add_argument("--wikidata-relation", dest="wikidata_relation", help="Path to wikidata_relation.csv.")
    parser.add_argument("--wikidata-relation2", dest="wikidata_relation2", help="Path to wikidata_relation2.csv.")
    parser.add_argument("--new-node", dest="new_node", help="Path to new_node.csv.")
    parser.add_argument("--weather-plant", dest="weather_plant", help="Path to weather_plant.csv.")
    parser.add_argument("--city-weather", dest="city_weather", help="Path to city_weather.csv.")
    parser.add_argument("--max-rows", type=int, default=0, help="Validate at most this many data rows per file; 0 means all rows.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return a non-zero exit code when warnings are present.")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON report.")
    parser.add_argument("--self-test", action="store_true", help="Create and validate tiny in-memory-style fixtures in a temporary directory.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_rows < 0:
        parser.error("--max-rows must be non-negative")

    if args.self_test:
        with tempfile.TemporaryDirectory(prefix="agri-kg-csv-fixture-") as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            paths = {file_id: root / str(spec["filename"]) for file_id, spec in FILE_SPECS.items()}
            result = run_validation(paths, max_rows=args.max_rows)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print_text_report(result, args.fail_on_warning)
            return 0 if int(result["errors"]) == 0 and (not args.fail_on_warning or int(result["warnings"]) == 0) else 1

    paths = resolve_paths(args)
    result = run_validation(paths, max_rows=args.max_rows)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(result, args.fail_on_warning)

    if int(result["errors"]) > 0:
        return 1
    if args.fail_on_warning and int(result["warnings"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
