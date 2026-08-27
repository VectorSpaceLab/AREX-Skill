#!/usr/bin/env python3
"""Lightweight dataset-layout checker for the LTSF-Linear skill.

This helper validates the common forecasting CSV layout and a small amount of
Pyraformer directory structure. It is intentionally conservative and does not
try to inspect the full benchmark data contents.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def find_repo_root(anchor: Path) -> Path:
    candidates = [anchor, *anchor.parents]
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "run_longExp.py").is_file() and (candidate / "Pyraformer" / "long_range_main.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root. Pass --repo-root when running from outside the checkout."
    )


def resolve_path(base: Path, raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def check_csv(csv_path: Path, *, date_column: str, target: str | None, features: str, require_date: bool) -> None:
    if not csv_path.is_file():
        raise SystemExit(f"CSV file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[csv] {csv_path}")
    print(f"  rows: {len(df)}")
    print(f"  columns: {list(df.columns)[:12]}")
    if require_date and date_column not in df.columns:
        raise SystemExit(f"missing required date column {date_column!r} in {csv_path}")
    if features in {"S", "MS"}:
        if not target:
            raise SystemExit(f"features={features} requires --target")
        if target not in df.columns:
            raise SystemExit(f"missing target column {target!r} in {csv_path}")
    if target and target not in df.columns:
        print(f"  note: target {target!r} not present; this is only acceptable when the selected route does not use it")


def check_pyraformer_layout(repo_root: Path, data_root: Path | None, raw_file: Path | None) -> None:
    pyraformer_dir = repo_root / "Pyraformer"
    required = [
        pyraformer_dir / "long_range_main.py",
        pyraformer_dir / "single_step_main.py",
        pyraformer_dir / "data_loader.py",
        pyraformer_dir / "pyraformer",
    ]
    for path in required:
        if not path.exists():
            raise SystemExit(f"missing Pyraformer path: {path}")
    print(f"[pyraformer] source layout ok under {pyraformer_dir}")
    data_dir = pyraformer_dir / "data"
    if data_dir.exists():
        print(f"  data dir: {data_dir}")
    else:
        print(f"  note: optional data dir not present yet: {data_dir}")
    if data_root is not None:
        print(f"  data root: {data_root}")
    if raw_file is not None:
        if not raw_file.is_file():
            raise SystemExit(f"missing Pyraformer data file: {raw_file}")
        print(f"  raw file: {raw_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the repo's common dataset and directory layouts.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root containing the checkout.")
    parser.add_argument("--kind", choices=("root", "pyraformer", "all"), default="root", help="Which layout family to check.")
    parser.add_argument("--data-root", default="dataset", help="Directory that contains the forecasting CSVs.")
    parser.add_argument("--data-path", help="CSV file name under --data-root.")
    parser.add_argument("--date-column", default="date", help="Expected date column name.")
    parser.add_argument("--target", default=None, help="Optional target column to verify.")
    parser.add_argument("--features", choices=("M", "S", "MS"), default="M", help="Forecasting feature mode.")
    parser.add_argument("--no-require-date", action="store_true", help="Skip the date-column check for the CSV path.")
    parser.add_argument("--pyraformer-data-file", default=None, help="Optional raw Pyraformer data file to check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(Path(__file__).resolve())
    data_root = resolve_path(repo_root, args.data_root)
    data_path = resolve_path(data_root, args.data_path) if args.data_path else None
    pyraformer_raw = resolve_path(repo_root, args.pyraformer_data_file) if args.pyraformer_data_file else None

    if args.kind in {"root", "all"}:
        if data_path is None:
            raise SystemExit("--data-path is required for the root layout check")
        check_csv(data_path, date_column=args.date_column, target=args.target, features=args.features, require_date=not args.no_require_date)

    if args.kind in {"pyraformer", "all"}:
        check_pyraformer_layout(repo_root, data_root if data_root.exists() else None, pyraformer_raw)

    print("layout check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
