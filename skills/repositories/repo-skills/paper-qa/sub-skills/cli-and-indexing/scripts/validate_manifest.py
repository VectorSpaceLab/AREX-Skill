#!/usr/bin/env python3
"""Validate a PaperQA indexing manifest CSV without importing PaperQA.

The validator checks that `file_location` exists relative to a paper directory
and optionally treats missing DOI/title hints as errors. It uses only the Python
standard library so it can run in ordinary installed-package environments.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DOI_RE = re.compile(r"^10\.\S+/.+", re.IGNORECASE)
EXPECTED_COLUMNS = {"file_location", "doi", "title"}


@dataclass
class Issue:
    level: str
    row: int | None
    field: str | None
    message: str


@dataclass
class ManifestReport:
    manifest: str
    paper_directory: str
    row_count: int = 0
    columns: list[str] = field(default_factory=list)
    files_found: int = 0
    files_missing: int = 0
    duplicate_file_locations: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == "warning")


def _issue(report: ManifestReport, level: str, row: int | None, field_name: str | None, message: str) -> None:
    report.issues.append(Issue(level=level, row=row, field=field_name, message=message))


def _resolve_file_location(
    paper_directory: Path,
    raw_location: str,
    allow_absolute: bool,
) -> tuple[Path | None, str | None]:
    raw_location = raw_location.strip()
    if not raw_location:
        return None, "blank file_location"

    candidate = Path(raw_location).expanduser()
    if candidate.is_absolute():
        if not allow_absolute:
            return candidate, "absolute file_location is user-specific; prefer a relative path"
        return candidate, None

    resolved = (paper_directory / candidate).resolve()
    try:
        resolved.relative_to(paper_directory.resolve())
    except ValueError:
        return resolved, "file_location escapes paper_directory"
    return resolved, None


def validate_manifest(
    manifest: Path,
    paper_directory: Path,
    require_doi: bool = False,
    require_title: bool = False,
    allow_absolute: bool = False,
) -> ManifestReport:
    report = ManifestReport(manifest=str(manifest), paper_directory=str(paper_directory))

    if not manifest.exists():
        _issue(report, "error", None, None, "manifest file does not exist")
        return report
    if manifest.suffix.lower() != ".csv":
        _issue(report, "error", None, None, "manifest must have .csv suffix")
    if not paper_directory.exists():
        _issue(report, "error", None, None, "paper directory does not exist")
        return report
    if not paper_directory.is_dir():
        _issue(report, "error", None, None, "paper directory is not a directory")
        return report

    with manifest.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        report.columns = list(reader.fieldnames or [])
        if not report.columns:
            _issue(report, "error", None, None, "manifest has no header row")
            return report
        if "file_location" not in report.columns:
            _issue(report, "error", None, "file_location", "required column is missing")
            return report

        unknown_columns = sorted(set(report.columns) - EXPECTED_COLUMNS)
        if unknown_columns:
            _issue(
                report,
                "warning",
                None,
                None,
                "extra columns may be ignored by CLI indexing: " + ", ".join(unknown_columns),
            )

        seen: dict[str, int] = {}
        for csv_row_number, row in enumerate(reader, start=2):
            report.row_count += 1
            raw_location = (row.get("file_location") or "").strip()
            if raw_location in seen:
                report.duplicate_file_locations.append(raw_location)
                _issue(
                    report,
                    "error",
                    csv_row_number,
                    "file_location",
                    f"duplicate file_location also seen on row {seen[raw_location]}",
                )
            elif raw_location:
                seen[raw_location] = csv_row_number

            resolved, location_warning = _resolve_file_location(
                paper_directory=paper_directory,
                raw_location=raw_location,
                allow_absolute=allow_absolute,
            )
            if location_warning:
                level = "warning" if "absolute" in location_warning else "error"
                _issue(report, level, csv_row_number, "file_location", location_warning)
            if resolved is None:
                report.files_missing += 1
            elif not resolved.exists():
                report.files_missing += 1
                _issue(report, "error", csv_row_number, "file_location", "referenced file does not exist")
            elif not resolved.is_file():
                report.files_missing += 1
                _issue(report, "error", csv_row_number, "file_location", "referenced path is not a file")
            else:
                report.files_found += 1

            doi = (row.get("doi") or "").strip()
            title = (row.get("title") or "").strip()
            if doi and not DOI_RE.match(doi):
                _issue(report, "warning", csv_row_number, "doi", "DOI does not match a simple 10.x/... pattern")
            elif not doi and require_doi:
                _issue(report, "error", csv_row_number, "doi", "DOI is required but blank")
            elif not doi:
                _issue(report, "warning", csv_row_number, "doi", "DOI is blank; metadata inference may be less deterministic")

            if not title and require_title:
                _issue(report, "error", csv_row_number, "title", "title is required but blank")
            elif not title:
                _issue(report, "warning", csv_row_number, "title", "title is blank; metadata inference may be less deterministic")
            elif len(title) < 5:
                _issue(report, "warning", csv_row_number, "title", "title looks unusually short")

    if report.row_count == 0:
        _issue(report, "error", None, None, "manifest contains no data rows")
    return report


def _print_text(report: ManifestReport, max_issues: int) -> None:
    print("PaperQA manifest validation")
    print(f"manifest: {report.manifest}")
    print(f"paper_directory: {report.paper_directory}")
    print(f"columns: {', '.join(report.columns) if report.columns else '(none)'}")
    print(f"rows: {report.row_count}")
    print(f"files_found: {report.files_found}")
    print(f"files_missing: {report.files_missing}")
    print(f"errors: {report.error_count}")
    print(f"warnings: {report.warning_count}")
    if report.duplicate_file_locations:
        print("duplicate_file_locations: " + ", ".join(report.duplicate_file_locations))
    if report.issues:
        print("issues:")
        for issue in report.issues[:max_issues]:
            row = "" if issue.row is None else f"row {issue.row}: "
            field_name = "" if issue.field is None else f"{issue.field}: "
            print(f"  - {issue.level}: {row}{field_name}{issue.message}")
        remaining = len(report.issues) - max_issues
        if remaining > 0:
            print(f"  ... {remaining} more issue(s) omitted")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a PaperQA manifest CSV.")
    parser.add_argument("--paper-directory", required=True, type=Path, help="Directory containing files to index.")
    parser.add_argument("--manifest", required=True, type=Path, help="Manifest CSV path.")
    parser.add_argument("--require-doi", action="store_true", help="Treat blank DOI values as errors.")
    parser.add_argument("--require-title", action="store_true", help="Treat blank title values as errors.")
    parser.add_argument(
        "--allow-absolute",
        action="store_true",
        help="Allow absolute file_location values. Relative values are preferred for shareability.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--max-issues", type=int, default=50, help="Maximum issues to print in text mode.")
    args = parser.parse_args(argv)

    report = validate_manifest(
        manifest=args.manifest.expanduser(),
        paper_directory=args.paper_directory.expanduser(),
        require_doi=args.require_doi,
        require_title=args.require_title,
        allow_absolute=args.allow_absolute,
    )

    if args.json:
        payload: dict[str, Any] = asdict(report)
        payload["error_count"] = report.error_count
        payload["warning_count"] = report.warning_count
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(report, max_issues=max(0, args.max_issues))

    return 0 if report.error_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
