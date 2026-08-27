#!/usr/bin/env python3
"""Read-only summary of a BindCraft output directory.

This helper intentionally uses only the Python standard library.  It does not
import BindCraft, PyRosetta, CUDA libraries, or mutate the supplied directory.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


EXPECTED_DIRS = (
    "Accepted",
    "Accepted/Ranked",
    "Accepted/Animation",
    "Accepted/Plots",
    "Accepted/Pickle",
    "Trajectory",
    "Trajectory/Relaxed",
    "Trajectory/Plots",
    "Trajectory/Clashing",
    "Trajectory/LowConfidence",
    "Trajectory/Animation",
    "Trajectory/Pickle",
    "MPNN",
    "MPNN/Binder",
    "MPNN/Sequences",
    "MPNN/Relaxed",
    "Rejected",
)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only counts and Average_i_pTM top rows for a BindCraft "
            "output directory. No files are created, changed, or deleted."
        )
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="BindCraft design_path containing CSV files and output folders",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="number of rows to show per CSV containing Average_i_pTM (default: 5)",
    )
    return parser.parse_args(argv)


def nonempty_rows(path: Path) -> Tuple[int, Optional[List[str]], List[Dict[str, str]]]:
    """Return data-row count, header, and rows without writing to *path*."""
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        for row in reader:
            values = []
            for value in row.values():
                if isinstance(value, list):
                    values.append(" ".join(str(item) for item in value))
                else:
                    values.append(str(value or ""))
            if any(value.strip() for value in values):
                rows.append(row)
    return len(rows), header, rows


def numeric(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value.strip())
    except (AttributeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def file_counts(path: Path) -> Tuple[int, int]:
    total = 0
    pdbs = 0
    if not path.is_dir():
        return total, pdbs
    for item in path.rglob("*"):
        if item.is_file():
            total += 1
            if item.suffix.lower() == ".pdb":
                pdbs += 1
    return total, pdbs


def design_label(row: Dict[str, str]) -> str:
    value = row.get("Design") or row.get("Rank") or "<unnamed>"
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return str(value).strip() or "<unnamed>"


def print_top_rows(csv_path: Path, rows: List[Dict[str, str]], limit: int) -> None:
    scored = []
    for row_number, row in enumerate(rows, start=2):
        score = numeric(row.get("Average_i_pTM"))
        if score is not None:
            scored.append((score, row_number, row))
    if not scored:
        print(f"  {csv_path.name}: Average_i_pTM present but no numeric values")
        return

    scored.sort(key=lambda item: (-item[0], item[1]))
    print(f"  {csv_path.name} (top {min(limit, len(scored))}):")
    for score, row_number, row in scored[:limit]:
        rank = row.get("Rank") or ""
        if isinstance(rank, list):
            rank = " ".join(str(item) for item in rank)
        rank = str(rank).strip()
        rank_text = f", Rank={rank}" if rank else ""
        print(
            f"    row {row_number}: Design={design_label(row)}, "
            f"Average_i_pTM={score:g}{rank_text}"
        )


def summarize(output_dir: Path, top: int) -> int:
    root = output_dir.expanduser()
    if not root.exists():
        print(f"error: output directory does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: output path is not a directory: {root}", file=sys.stderr)
        return 2

    print(f"BindCraft output: {root.resolve()}")
    print("Directory counts (recursive files, PDB files):")
    for relative in EXPECTED_DIRS:
        directory = root / relative
        total, pdbs = file_counts(directory)
        status = "missing" if not directory.is_dir() else "present"
        print(f"  {relative}: {status}, files={total}, pdb={pdbs}")

    csv_paths = sorted(path for path in root.glob("*.csv") if path.is_file())
    print("CSV counts:")
    if not csv_paths:
        print("  none found")
    else:
        for csv_path in csv_paths:
            try:
                count, header, rows = nonempty_rows(csv_path)
            except (OSError, UnicodeError, csv.Error) as exc:
                print(f"  {csv_path.name}: unreadable ({exc})")
                continue
            columns = len(header or [])
            print(f"  {csv_path.name}: rows={count}, columns={columns}")

    print("Average_i_pTM top rows:")
    found_metric = False
    for csv_path in csv_paths:
        try:
            _, header, rows = nonempty_rows(csv_path)
        except (OSError, UnicodeError, csv.Error):
            continue
        if header and "Average_i_pTM" in header:
            found_metric = True
            print_top_rows(csv_path, rows, top)
    if not found_metric:
        print("  no CSV with an Average_i_pTM column found")
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.top < 1:
        print("error: --top must be at least 1", file=sys.stderr)
        return 2
    return summarize(args.output_dir, args.top)


if __name__ == "__main__":
    raise SystemExit(main())
