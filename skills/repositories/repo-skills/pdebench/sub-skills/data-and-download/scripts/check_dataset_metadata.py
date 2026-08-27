#!/usr/bin/env python3
"""Validate a local PDEBench metadata CSV without downloading anything."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

CANONICAL_PDES = (
    "advection",
    "burgers",
    "1d_cfd",
    "diff_sorp",
    "1d_reacdiff",
    "2d_cfd",
    "darcy",
    "2d_reacdiff",
    "ns_incom",
    "swe",
    "3d_cfd",
)
REQUIRED_COLUMNS = ("PDE", "Filename", "URL", "Path", "MD5")


def _read_rows(metadata: Path) -> list[dict[str, str]]:
    if not metadata.is_file():
        raise FileNotFoundError(f"metadata CSV does not exist: {metadata}")
    with metadata.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise ValueError(
                "metadata CSV is missing required columns: " + ", ".join(missing)
            )
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _normalise_names(names: list[str]) -> list[str]:
    return [name.strip().lower() for name in names if name.strip()]


def _validate_rows(rows: list[dict[str, str]]) -> list[str]:
    problems: list[str] = []
    for index, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row.get(column):
                problems.append(f"row {index} has an empty {column} field")
        pde = row.get("PDE", "").lower()
        if pde and pde not in CANONICAL_PDES:
            problems.append(f"row {index} has unknown PDE name {row['PDE']!r}")
    return problems


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local PDEBench dataset metadata. This helper only reads a "
            "CSV; it never downloads or uploads files."
        )
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("pdebench_data_urls.csv"),
        help="Local PDEBench CSV (default: ./pdebench_data_urls.csv)",
    )
    parser.add_argument(
        "--pde-name",
        action="append",
        default=[],
        help="Canonical PDE name to validate; repeat for multiple names",
    )
    parser.add_argument(
        "--list-pdes",
        action="store_true",
        help="Print canonical names and row counts from the local CSV",
    )
    parser.add_argument(
        "--show-files",
        action="store_true",
        help="Print matching filenames, relative paths, and MD5 values",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = _read_rows(args.metadata)
        problems = _validate_rows(rows)
        if problems:
            raise ValueError("; ".join(problems[:8]))

        selected = _normalise_names(args.pde_name)
        unknown = sorted(set(selected).difference(CANONICAL_PDES))
        if unknown:
            raise ValueError(
                "unknown PDE name(s): "
                + ", ".join(unknown)
                + ". Use --list-pdes for canonical names."
            )
        if args.show_files and not selected:
            raise ValueError("--show-files requires at least one --pde-name")

        counts = Counter(row["PDE"].lower() for row in rows)
        if args.list_pdes:
            for name in CANONICAL_PDES:
                print(f"{name}\t{counts.get(name, 0)} row(s)")

        if selected:
            matches = [row for row in rows if row["PDE"].lower() in selected]
            missing = sorted(set(selected).difference(row["PDE"].lower() for row in matches))
            if missing:
                raise ValueError(
                    "valid PDE name(s) have no rows in this CSV: " + ", ".join(missing)
                )
            print(f"VALID: {len(matches)} metadata row(s) for {', '.join(selected)}")
            if args.show_files:
                for row in matches:
                    print(
                        f"{row['PDE'].lower()}\t{row['Path']}{row['Filename']}\t"
                        f"md5={row['MD5']}"
                    )
        elif not args.list_pdes:
            build_parser().error("provide --pde-name or --list-pdes")
        return 0
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
