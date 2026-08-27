#!/usr/bin/env python3
"""Validate a LimiX benchmark-style local dataset root.

This script is intentionally lightweight: it reads CSV metadata/rows, reports
layout and target issues, and never imports LimiX, loads a checkpoint, downloads
remote data, or runs model inference.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


MISSING_STRINGS = {"", "nan", "NaN", "NAN", "na", "NA", "null", "NULL", "None", "none"}


class ValidationError(Exception):
    """Raised for CSV-level validation errors that should mark one dataset invalid."""


class CsvTable:
    def __init__(self, path: Path, header: List[str], rows: List[List[str]]):
        self.path = path
        self.header = header
        self.rows = rows

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return len(self.header)

    @property
    def feature_names(self) -> List[str]:
        return self.header[:-1]

    @property
    def target_name(self) -> str:
        return self.header[-1]

    def column_values(self, index: int) -> List[str]:
        return [row[index] for row in self.rows]

    def target_values(self) -> List[str]:
        return self.column_values(self.n_cols - 1)


def is_float_text(value: str) -> bool:
    if value in MISSING_STRINGS:
        return False
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed)


def parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite numeric value {value!r}")
    return parsed


def read_csv_table(path: Path) -> CsvTable:
    if not path.exists():
        raise ValidationError(f"missing required CSV: {path.name}")
    if not path.is_file():
        raise ValidationError(f"expected a file, got non-file path: {path.name}")

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            all_rows = list(reader)
    except UnicodeDecodeError as exc:
        raise ValidationError(f"could not decode {path.name} as UTF-8/UTF-8-SIG CSV: {exc}") from exc
    except csv.Error as exc:
        raise ValidationError(f"could not parse {path.name} as CSV: {exc}") from exc

    if not all_rows:
        raise ValidationError(f"{path.name} is empty; expected a header row and data rows")

    header = [cell.strip() for cell in all_rows[0]]
    if len(header) < 2:
        raise ValidationError(f"{path.name} has {len(header)} column(s); need at least one feature plus target")
    if any(name == "" for name in header):
        raise ValidationError(f"{path.name} has blank header names; use explicit feature and target names")
    if len(set(header)) != len(header):
        raise ValidationError(f"{path.name} has duplicate header names; make feature/target names unique")

    data_rows: List[List[str]] = []
    for line_no, row in enumerate(all_rows[1:], start=2):
        # Preserve empty cells but ignore fully blank trailing lines.
        if not row or all(cell == "" for cell in row):
            continue
        if len(row) != len(header):
            raise ValidationError(
                f"{path.name} line {line_no} has {len(row)} field(s), expected {len(header)}"
            )
        data_rows.append(row)

    if not data_rows:
        raise ValidationError(f"{path.name} has no non-empty data rows")

    return CsvTable(path=path, header=header, rows=data_rows)


def infer_task_from_targets(values: Sequence[str]) -> str:
    numeric_values: List[float] = []
    all_numeric = True
    for value in values:
        if not is_float_text(value):
            all_numeric = False
            break
        numeric_values.append(float(value))

    if not all_numeric:
        return "classification"

    unique_values = set(values)
    all_integer_like = all(float(v).is_integer() for v in numeric_values)
    if len(unique_values) <= 10 and all_integer_like:
        return "classification"
    return "regression"


def format_counter(counter: Counter, max_items: int = 12) -> str:
    items = counter.most_common(max_items)
    text = ", ".join(f"{key!r}:{count}" for key, count in items)
    if len(counter) > max_items:
        text += f", ... (+{len(counter) - max_items} more)"
    return text


def numeric_summary(values: Sequence[float]) -> Dict[str, float]:
    count = len(values)
    mean = sum(values) / count
    variance = sum((v - mean) ** 2 for v in values) / count
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean,
        "std": math.sqrt(variance),
    }


def nonnumeric_feature_columns(table: CsvTable) -> List[Tuple[int, str]]:
    result: List[Tuple[int, str]] = []
    for idx, name in enumerate(table.feature_names):
        values = table.column_values(idx)
        non_missing = [value for value in values if value not in MISSING_STRINGS]
        if non_missing and any(not is_float_text(value) for value in non_missing):
            result.append((idx, name))
    return result


def warn_unseen_test_categories(train: CsvTable, test: Optional[CsvTable]) -> List[str]:
    if test is None:
        return []
    warnings: List[str] = []
    for idx, name in nonnumeric_feature_columns(train):
        train_values = set(value for value in train.column_values(idx) if value not in MISSING_STRINGS)
        test_values = set(value for value in test.column_values(idx) if value not in MISSING_STRINGS)
        unseen = sorted(test_values - train_values)
        if unseen:
            shown = ", ".join(repr(value) for value in unseen[:8])
            suffix = "" if len(unseen) <= 8 else f", ... (+{len(unseen) - 8} more)"
            warnings.append(
                f"feature {name!r} has unseen test categories ({shown}{suffix}); "
                "classification CLI may drop this feature column"
            )
    return warnings


def validate_dataset_folder(
    folder: Path,
    requested_task: str,
    max_train_rows: int,
) -> Tuple[List[str], List[str], List[str]]:
    """Validate one dataset folder.

    Returns (summary_lines, warnings, errors).
    """
    warnings: List[str] = []
    errors: List[str] = []
    summary: List[str] = []

    dataset_name = folder.name
    train_path = folder / f"{dataset_name}_train.csv"
    test_path = folder / f"{dataset_name}_test.csv"

    try:
        train = read_csv_table(train_path)
    except ValidationError as exc:
        return [f"dataset={dataset_name}"], warnings, [str(exc)]

    test: Optional[CsvTable] = None
    if test_path.exists():
        try:
            test = read_csv_table(test_path)
        except ValidationError as exc:
            errors.append(str(exc))
    else:
        warnings.append(
            "missing optional test CSV; classification CLI will split train 50/50, "
            "current regression CLI skips/raises for this dataset"
        )

    if test is not None:
        if train.feature_names != test.feature_names:
            errors.append(
                "train/test feature columns differ; expected same feature names in the same order "
                f"(train={train.feature_names!r}, test={test.feature_names!r})"
            )
        if train.target_name != test.target_name:
            warnings.append(
                f"target header differs between train ({train.target_name!r}) and test ({test.target_name!r}); "
                "CLIs use the last column by position"
            )

    selected_task = requested_task
    if requested_task == "auto":
        selected_task = infer_task_from_targets(train.target_values())

    if train.n_rows >= max_train_rows:
        errors.append(
            f"train rows {train.n_rows} >= max-train-rows {max_train_rows}; "
            "classification CLI skips at this threshold and large LimiX CLI runs are GPU-memory sensitive"
        )

    summary.append(
        f"dataset={dataset_name} task={selected_task} train_rows={train.n_rows} "
        f"test_rows={test.n_rows if test is not None else 'absent'} features={len(train.feature_names)} "
        f"target={train.target_name!r}"
    )

    nonnumeric_features = nonnumeric_feature_columns(train)
    if nonnumeric_features:
        names = ", ".join(name for _, name in nonnumeric_features[:12])
        if len(nonnumeric_features) > 12:
            names += f", ... (+{len(nonnumeric_features) - 12} more)"
        warnings.append(f"nonnumeric feature column(s) detected: {names}")

    if selected_task == "classification":
        target_values = train.target_values()
        if any(value in MISSING_STRINGS for value in target_values):
            errors.append("classification target contains missing/blank values")
        class_counts = Counter(target_values)
        n_classes = len(class_counts)
        summary.append(f"classes={n_classes} counts={format_counter(class_counts)}")
        if n_classes < 2:
            errors.append(f"classification requires at least 2 classes; found {n_classes}")
        if n_classes > 10:
            errors.append(f"classification CLI supports at most 10 classes; found {n_classes}")
        warnings.extend(warn_unseen_test_categories(train, test))

    elif selected_task == "regression":
        if test is None:
            errors.append("regression CLI needs a test CSV for scoring; add <dataset>_test.csv")
        numeric_targets: List[float] = []
        bad_targets: List[str] = []
        for value in train.target_values():
            try:
                numeric_targets.append(parse_float(value))
            except (TypeError, ValueError):
                bad_targets.append(value)
        if bad_targets:
            shown = ", ".join(repr(value) for value in bad_targets[:8])
            suffix = "" if len(bad_targets) <= 8 else f", ... (+{len(bad_targets) - 8} more)"
            errors.append(f"regression train target has nonnumeric values: {shown}{suffix}")
        else:
            stats = numeric_summary(numeric_targets)
            summary.append(
                "target_stats="
                f"min={stats['min']:.6g}, max={stats['max']:.6g}, "
                f"mean={stats['mean']:.6g}, std={stats['std']:.6g}"
            )
            if stats["std"] == 0:
                errors.append("regression train target has zero variance; CLI normalization divides by target std")

            if test is not None:
                bad_test_targets: List[str] = []
                for value in test.target_values():
                    try:
                        parse_float(value)
                    except (TypeError, ValueError):
                        bad_test_targets.append(value)
                if bad_test_targets:
                    shown = ", ".join(repr(value) for value in bad_test_targets[:8])
                    suffix = "" if len(bad_test_targets) <= 8 else f", ... (+{len(bad_test_targets) - 8} more)"
                    errors.append(f"regression test target has nonnumeric values: {shown}{suffix}")
    else:
        errors.append(f"unsupported task {selected_task!r}")

    return summary, warnings, errors


def make_fixture(root: Path, task: str) -> None:
    root.mkdir(parents=True, exist_ok=True)

    def write_rows(path: Path, rows: Iterable[Sequence[object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

    if task in {"classification", "auto"}:
        name = "toy_cls"
        write_rows(
            root / name / f"{name}_train.csv",
            [
                ["feat_num", "feat_cat", "target"],
                [0.0, "a", "no"],
                [1.0, "b", "yes"],
                [2.0, "a", "no"],
                [3.0, "b", "yes"],
            ],
        )
        write_rows(
            root / name / f"{name}_test.csv",
            [
                ["feat_num", "feat_cat", "target"],
                [0.5, "a", "no"],
                [2.5, "b", "yes"],
            ],
        )

    if task in {"regression", "auto"}:
        name = "toy_reg"
        write_rows(
            root / name / f"{name}_train.csv",
            [
                ["feat_num", "feat_cat", "target"],
                [0.0, "low", 1.2],
                [1.0, "low", 1.8],
                [2.0, "high", 2.9],
                [3.0, "high", 3.7],
            ],
        )
        write_rows(
            root / name / f"{name}_test.csv",
            [
                ["feat_num", "feat_cat", "target"],
                [1.5, "low", 2.1],
                [3.5, "high", 4.0],
            ],
        )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a LimiX benchmark-style dataset root. The root must contain "
            "dataset folders named like <dataset>/<dataset>_train.csv and optional "
            "<dataset>/<dataset>_test.csv."
        )
    )
    parser.add_argument(
        "dataset_root",
        nargs="?",
        help="Path to the dataset root to validate. Optional when --make-fixture is used.",
    )
    parser.add_argument(
        "--task",
        choices=["classification", "regression", "auto"],
        default="auto",
        help="Task contract to validate. 'auto' infers per dataset from the train target. Default: auto.",
    )
    parser.add_argument(
        "--max-train-rows",
        type=int,
        default=50000,
        help="Maximum allowed training rows before reporting a LimiX benchmark skip risk. Default: 50000.",
    )
    parser.add_argument(
        "--make-fixture",
        metavar="DIR",
        help="Create a tiny safe fixture dataset root at DIR before validation. No model inference is run.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    dataset_root_arg = args.dataset_root
    if args.make_fixture:
        fixture_root = Path(args.make_fixture)
        make_fixture(fixture_root, args.task)
        print(f"Created tiny {args.task} fixture under: {fixture_root}")
        if dataset_root_arg is None:
            dataset_root_arg = str(fixture_root)

    if dataset_root_arg is None:
        print("ERROR: dataset_root is required unless --make-fixture supplies it", file=sys.stderr)
        return 2

    root = Path(dataset_root_arg)
    if not root.exists():
        print(f"ERROR: dataset root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"ERROR: dataset root is not a directory: {root}", file=sys.stderr)
        return 2
    if args.max_train_rows <= 0:
        print("ERROR: --max-train-rows must be positive", file=sys.stderr)
        return 2

    child_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    ignored_files = sorted(path.name for path in root.iterdir() if path.is_file())
    if ignored_files:
        shown = ", ".join(ignored_files[:8])
        suffix = "" if len(ignored_files) <= 8 else f", ... (+{len(ignored_files) - 8} more)"
        print(f"WARNING: root-level files are ignored by benchmark CLIs: {shown}{suffix}")

    if not child_dirs:
        print(f"ERROR: no dataset folders found under {root}", file=sys.stderr)
        return 1

    total_errors = 0
    total_warnings = 0
    for folder in child_dirs:
        summary, warnings, errors = validate_dataset_folder(
            folder=folder,
            requested_task=args.task,
            max_train_rows=args.max_train_rows,
        )
        status = "OK" if not errors else "FAIL"
        print(f"\n[{status}] {folder.name}")
        for line in summary:
            print(f"  {line}")
        for warning in warnings:
            total_warnings += 1
            print(f"  WARNING: {warning}")
        for error in errors:
            total_errors += 1
            print(f"  ERROR: {error}")

    print(
        f"\nValidated {len(child_dirs)} dataset folder(s) under {root}: "
        f"warnings={total_warnings}, errors={total_errors}"
    )
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
