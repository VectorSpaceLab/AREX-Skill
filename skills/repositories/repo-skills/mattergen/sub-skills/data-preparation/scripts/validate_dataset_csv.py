#!/usr/bin/env python3
"""Deterministic, read-only preflight for MatterGen CSV dataset inputs.

This intentionally does not call csv-to-dataset, create cache directories, download
archives, or write converted data. It checks the contract consumed by the package
converter and parses CIF text so malformed rows can be found before preprocessing.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ("cif", "material_id")


@dataclass(frozen=True)
class Issue:
    severity: str
    file_name: str
    row: int | None
    message: str

    def render(self) -> str:
        location = self.file_name
        if self.row is not None:
            location += f":row {self.row}"
        return f"[{self.severity}] {location}: {self.message}"


def _supported_property_ids() -> tuple[set[str], str | None]:
    """Read the installed package registry without importing it for --help."""
    try:
        # Make a checkout-local editable package discoverable when this script is
        # run directly from a project root. This is deliberately cwd-relative;
        # it does not embed or infer any machine-specific checkout path.
        with redirect_stdout(io.StringIO()):
            try:
                from mattergen.common.utils.globals import PROPERTY_SOURCE_IDS
            except ModuleNotFoundError:
                cwd_package = Path.cwd() / "mattergen"
                if not cwd_package.is_dir():
                    raise
                sys.path.insert(0, str(Path.cwd()))
                from mattergen.common.utils.globals import PROPERTY_SOURCE_IDS

        return set(PROPERTY_SOURCE_IDS), None
    except Exception as exc:  # pragma: no cover - exercised in broken installs
        return set(), f"could not load MatterGen property registry: {type(exc).__name__}: {exc}"


def _blank(value: Any) -> bool:
    return value is None or not str(value).strip()


def _parse_cif(value: str) -> str | None:
    """Use the same primitive-structure parse contract as the package converter."""
    try:
        from pymatgen.io.cif import CifParser
    except Exception as exc:  # pragma: no cover - exercised in broken installs
        return f"pymatgen CIF parser is unavailable ({type(exc).__name__}: {exc})"

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            structures = CifParser.from_str(value).parse_structures(
                primitive=True, on_error="ignore"
            )
        if not structures:
            return "CIF parser returned no structures"
    except Exception as exc:
        return f"CIF parse failed ({type(exc).__name__}: {exc})"
    return None


def _parse_space_group(value: str) -> str | None:
    try:
        from pymatgen.symmetry.groups import SpaceGroup

        SpaceGroup(value).int_number
    except Exception as exc:
        return f"space_group value is not a recognized space-group symbol ({type(exc).__name__}: {exc})"
    return None


def _read_csv(path: Path) -> tuple[list[str] | None, list[dict[str, Any]], str | None]:
    """Read one CSV strictly while retaining row dictionaries for validation."""
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, restkey="__extra__", strict=True)
            headers = reader.fieldnames
            if headers is None:
                return None, rows, "file has no CSV header"
            for row in reader:
                # pandas.read_csv, which the real converter uses, ignores blank lines.
                values = [row.get(header) for header in headers]
                if all(_blank(value) for value in values) and not row.get("__extra__"):
                    continue
                rows.append(row)
            return headers, rows, None
    except (OSError, UnicodeError, csv.Error) as exc:
        return None, rows, f"could not read CSV ({type(exc).__name__}: {exc})"


def validate_folder(
    csv_folder: Path,
    requested_properties: list[str],
    limit_rows: int,
) -> tuple[list[Issue], int, int]:
    issues: list[Issue] = []
    total_rows = 0
    parsed_rows = 0

    def add(severity: str, file_name: str, row: int | None, message: str) -> None:
        issues.append(Issue(severity, file_name, row, message))

    if not csv_folder.exists():
        add("ERROR", str(csv_folder), None, "CSV folder does not exist")
        return issues, total_rows, parsed_rows
    if not csv_folder.is_dir():
        add("ERROR", str(csv_folder), None, "--csv-folder is not a directory")
        return issues, total_rows, parsed_rows

    csv_files = sorted(
        (path for path in csv_folder.iterdir() if path.is_file() and path.suffix == ".csv"),
        key=lambda path: path.name,
    )
    if not csv_files:
        add("ERROR", str(csv_folder), None, "folder contains no .csv files")
        return issues, total_rows, parsed_rows

    supported, registry_error = _supported_property_ids()
    if registry_error:
        add("ERROR", str(csv_folder), None, registry_error)

    records: list[tuple[Path, list[str], list[dict[str, Any]]]] = []
    for path in csv_files:
        if path.stat().st_size == 0:
            add("ERROR", path.name, None, "file is empty")
            continue
        headers, rows, read_error = _read_csv(path)
        if read_error:
            add("ERROR", path.name, None, read_error)
            continue
        assert headers is not None
        if len(headers) != len(set(headers)):
            add("ERROR", path.name, None, "header contains duplicate column names")
        empty_headers = [index for index, header in enumerate(headers) if _blank(header)]
        # The repository fixture and common pandas `to_csv(index=True)` output
        # have one unnamed leading index column. The package converter ignores
        # this unknown column, so permit that exact harmless form while still
        # rejecting ambiguous empty headers.
        if empty_headers and empty_headers != [0]:
            add("ERROR", path.name, None, "header contains an empty column name outside an optional leading index column")
        if "__extra__" in headers:
            add("ERROR", path.name, None, "header uses the validator's reserved extra-field name")
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            add("ERROR", path.name, None, f"missing required column(s): {', '.join(missing)}")
        if not rows:
            add("ERROR", path.name, None, "file has no non-blank data rows")
        records.append((path, headers, rows))
        total_rows += len(rows)

    if not records:
        return issues, total_rows, parsed_rows

    present_known = set().union(*(set(headers) & supported for _, headers, _ in records))
    expected_properties = set(requested_properties) if requested_properties else present_known
    for prop in requested_properties:
        if prop not in supported:
            add(
                "ERROR",
                str(csv_folder),
                None,
                f"selected property '{prop}' is not in MatterGen's property registry; the converter will not cache it until the package registry is extended",
            )

    for path, headers, rows in records:
        for prop in sorted(expected_properties):
            if prop not in headers:
                add(
                    "ERROR",
                    path.name,
                    None,
                    f"property column '{prop}' is missing; selected/recognized property columns must have the same schema across CSV splits",
                )
                continue
            values = [row.get(prop) for row in rows]
            missing_count = sum(_blank(value) for value in values)
            if missing_count == len(values) and values:
                add("ERROR", path.name, None, f"property column '{prop}' is entirely empty")
            elif missing_count:
                add(
                    "WARN",
                    path.name,
                    None,
                    f"property column '{prop}' has {missing_count}/{len(values)} blank value(s); filter_sparse_properties will drop rows missing selected properties",
                )

    for path, headers, rows in records:
        if any(column not in headers for column in REQUIRED_COLUMNS):
            # Keep the schema error above concise and avoid producing one error per row.
            continue
        rows_to_check = rows if limit_rows <= 0 else rows[:limit_rows]
        for row_number, row in enumerate(rows_to_check, start=2):
            extras = row.get("__extra__")
            if extras:
                add("ERROR", path.name, row_number, "row has more fields than the header")
            material_id = row.get("material_id")
            cif = row.get("cif")
            if _blank(material_id):
                add("ERROR", path.name, row_number, "material_id is empty")
            if _blank(cif):
                add("ERROR", path.name, row_number, "cif is empty")
                continue
            parse_error = _parse_cif(str(cif))
            if parse_error:
                add("ERROR", path.name, row_number, parse_error)
            else:
                parsed_rows += 1

            if "space_group" in expected_properties and not _blank(row.get("space_group")):
                space_group_error = _parse_space_group(str(row["space_group"]).strip())
                if space_group_error:
                    add("ERROR", path.name, row_number, space_group_error)

    if limit_rows > 0:
        add(
            "WARN",
            str(csv_folder),
            None,
            f"only the first {limit_rows} data row(s) per file were checked; rerun without --limit-rows for a complete preflight",
        )
    return issues, total_rows, parsed_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only preflight for CSV folders passed to MatterGen csv-to-dataset."
    )
    parser.add_argument(
        "--csv-folder",
        required=True,
        type=Path,
        help="Folder containing every split CSV that csv-to-dataset would process.",
    )
    parser.add_argument(
        "--property",
        dest="properties",
        action="append",
        default=[],
        metavar="NAME",
        help="Require and inspect a selected registered property column; repeat for multiple properties.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Maximum number of rendered issues (validation still runs); default: 50.",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=0,
        help="Check only this many rows per file for a quick probe; 0 checks every row.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be positive")
    if args.limit_rows < 0:
        parser.error("--limit-rows must be non-negative")

    issues, total_rows, parsed_rows = validate_folder(
        csv_folder=args.csv_folder,
        requested_properties=args.properties,
        limit_rows=args.limit_rows,
    )
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    print(f"MatterGen CSV preflight: {'PASS' if not errors else 'FAIL'}")
    print(f"CSV folder: {args.csv_folder}")
    print(f"Rows discovered: {total_rows}; CIF rows parsed: {parsed_rows}")
    for issue in issues[: args.max_errors]:
        print(issue.render())
    if len(issues) > args.max_errors:
        print(f"[INFO] {len(issues) - args.max_errors} additional issue(s) suppressed; fix the first issues and rerun")
    if not errors:
        print("No blocking CSV, schema, structure, or selected-property errors found.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
