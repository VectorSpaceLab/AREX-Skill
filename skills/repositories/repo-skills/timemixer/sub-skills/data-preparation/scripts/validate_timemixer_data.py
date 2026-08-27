#!/usr/bin/env python3
"""Validate TimeMixer dataset layouts without importing the source repository."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd
from pandas.tseries.frequencies import to_offset


class ValidationError(RuntimeError):
    """Raised when a dataset layout does not match the expected contract."""


def fail(message: str) -> None:
    raise ValidationError(message)


def resolve_path(root: Path, relative: Optional[str], *, required: bool = True) -> Optional[Path]:
    if relative is None:
        if required:
            fail("A required path argument is missing.")
        return None
    path = Path(relative)
    if not path.is_absolute():
        path = root / path
    if required and not path.exists():
        fail(f"Missing path: {path}")
    return path


def require_file(path: Path) -> None:
    if not path.is_file():
        fail(f"Expected file but found nothing at: {path}")


def require_dir(path: Path) -> None:
    if not path.is_dir():
        fail(f"Expected directory but found nothing at: {path}")


def numeric_series_mask(series: pd.Series) -> bool:
    converted = pd.to_numeric(series, errors="coerce")
    bad_mask = converted.isna() & series.notna()
    return not bool(bad_mask.any())


def numeric_frame_mask(frame: pd.DataFrame) -> bool:
    bad_columns: List[str] = []
    for column in frame.columns:
        if not numeric_series_mask(frame[column]):
            bad_columns.append(str(column))
    if bad_columns:
        fail("Non-numeric values found in columns: " + ", ".join(bad_columns))
    return True


def drop_optional_leading_column(frame: pd.DataFrame) -> pd.DataFrame:
    """Match loaders that intentionally discard the first CSV column."""
    if frame.shape[1] < 2:
        fail("CSV file needs at least two columns after dropping the leading column.")
    return frame.iloc[:, 1:]


def parse_rows_needed(seq_len: Optional[int], pred_len: Optional[int], *, anomaly: bool = False) -> Optional[int]:
    if seq_len is None and pred_len is None:
        return None
    seq = seq_len or 0
    pred = pred_len or 0
    return seq if anomaly else seq + pred


def check_window_rows(row_count: int, needed: Optional[int], *, context: str) -> None:
    if needed is None:
        return
    if row_count < needed:
        fail(f"{context} has only {row_count} rows but needs at least {needed} for one window.")


def check_forecast_split_rows(total_rows: int, seq_len: Optional[int], pred_len: Optional[int], *, context: str, train_ratio: float, test_ratio: float, train_requires_seq: bool, valid_requires_seq: bool, test_requires_seq: bool) -> None:
    if seq_len is None and pred_len is None:
        return

    seq = seq_len or 0
    pred = pred_len or 0
    train_rows = int(total_rows * train_ratio)
    test_rows = int(total_rows * test_ratio)
    valid_rows = total_rows - train_rows - test_rows

    if train_requires_seq:
        train_needed = seq + pred
    else:
        train_needed = pred
    if valid_requires_seq:
        valid_needed = seq + pred
    else:
        valid_needed = pred
    if test_requires_seq:
        test_needed = seq + pred
    else:
        test_needed = pred

    if train_rows < train_needed:
        fail(
            f"{context} train split is too short: {train_rows} rows available, need at least {train_needed}."
        )
    if valid_rows < valid_needed:
        fail(
            f"{context} validation split is too short: {valid_rows} rows available, need at least {valid_needed}."
        )
    if test_rows < test_needed:
        fail(
            f"{context} test split is too short: {test_rows} rows available, need at least {test_needed}."
        )


def validate_custom(args: argparse.Namespace, root: Path) -> None:
    path = resolve_path(root, args.data_path)
    require_file(path)
    frame = pd.read_csv(path)

    missing = [name for name in (args.date_column, args.target) if name not in frame.columns]
    if missing:
        fail("Custom CSV is missing required column(s): " + ", ".join(missing))

    dates = pd.to_datetime(frame[args.date_column], errors="coerce")
    bad_dates = dates.isna() & frame[args.date_column].notna()
    if bool(bad_dates.any()):
        fail(f"Custom CSV column '{args.date_column}' contains values that pandas cannot parse as dates.")

    non_date_cols = [column for column in frame.columns if column != args.date_column]
    numeric_frame_mask(frame[non_date_cols])

    if args.freq is not None:
        try:
            to_offset(args.freq)
        except Exception as exc:  # pragma: no cover - defensive
            fail(f"Invalid frequency '{args.freq}': {exc}")

    check_forecast_split_rows(
        len(frame),
        args.seq_len,
        args.pred_len,
        context=f"Custom CSV {path.name}",
        train_ratio=0.7,
        test_ratio=0.2,
        train_requires_seq=True,
        valid_requires_seq=False,
        test_requires_seq=False,
    )
    print(f"OK custom CSV: rows={len(frame)} cols={len(frame.columns)} path={path}")


def validate_pems(args: argparse.Namespace, root: Path) -> None:
    path = resolve_path(root, args.data_path)
    require_file(path)
    try:
        with np.load(path, allow_pickle=True) as npz:
            if args.npz_key not in npz.files:
                fail(f"PEMS archive {path.name} does not contain key '{args.npz_key}'. Found: {', '.join(npz.files)}")
            data = npz[args.npz_key]
    except ValidationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"Could not open PEMS archive {path}: {exc}")

    try:
        data = np.asarray(data, dtype=float)
    except Exception:
        fail(f"PEMS archive {path.name} must contain numeric values in key '{args.npz_key}'.")

    if data.ndim != 3:
        fail(f"PEMS data array must be 3D [time, nodes, channels]; found shape {data.shape}.")
    if data.shape[2] < 1:
        fail(f"PEMS data array has no channel axis: shape {data.shape}.")
    if args.expected_channels is not None and data.shape[1] != args.expected_channels:
        fail(f"PEMS node count mismatch: archive has {data.shape[1]} channels but expected {args.expected_channels}.")

    check_forecast_split_rows(
        data.shape[0],
        args.seq_len,
        args.pred_len,
        context=f"PEMS archive {path.name}",
        train_ratio=0.6,
        test_ratio=0.2,
        train_requires_seq=True,
        valid_requires_seq=True,
        test_requires_seq=True,
    )
    print(f"OK PEMS archive: shape={data.shape} key={args.npz_key} path={path}")


def validate_solar(args: argparse.Namespace, root: Path) -> None:
    path = resolve_path(root, args.data_path)
    require_file(path)

    rows: list[list[float]] = []
    column_count: Optional[int] = None
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                fail(f"Solar file {path.name} has a blank line at {line_no}.")
            parts = [part.strip() for part in line.split(",")]
            if column_count is None:
                column_count = len(parts)
            elif len(parts) != column_count:
                fail(
                    f"Solar file {path.name} has an inconsistent column count at line {line_no}: "
                    f"expected {column_count}, found {len(parts)}."
                )
            try:
                rows.append([float(part) for part in parts])
            except ValueError as exc:
                fail(f"Solar file {path.name} contains a nonnumeric token at line {line_no}: {exc}")

    if not rows:
        fail(f"Solar file {path.name} is empty.")

    matrix = np.asarray(rows, dtype=float)
    check_forecast_split_rows(
        matrix.shape[0],
        args.seq_len,
        args.pred_len,
        context=f"Solar file {path.name}",
        train_ratio=0.7,
        test_ratio=0.2,
        train_requires_seq=True,
        valid_requires_seq=False,
        test_requires_seq=False,
    )
    print(f"OK Solar file: rows={matrix.shape[0]} cols={matrix.shape[1]} path={path}")


def validate_m4(args: argparse.Namespace, root: Path) -> None:
    info_path = resolve_path(root, args.m4_info)
    train_path = resolve_path(root, args.m4_training)
    test_path = resolve_path(root, args.m4_test)
    require_file(info_path)
    require_file(train_path)
    require_file(test_path)

    frame = pd.read_csv(info_path)
    required_cols = ["M4id", "SP", "Frequency", "Horizon"]
    missing = [column for column in required_cols if column not in frame.columns]
    if missing:
        fail("M4 info file is missing required column(s): " + ", ".join(missing))

    if args.seasonal_patterns is not None and not (frame["SP"] == args.seasonal_patterns).any():
        fail(f"M4 info file does not contain seasonal pattern '{args.seasonal_patterns}'.")

    for archive_path in (train_path, test_path):
        try:
            with np.load(archive_path, allow_pickle=True) as npz:
                if len(npz.files) == 0:
                    fail(f"M4 archive {archive_path.name} is empty.")
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            fail(f"Could not open M4 archive {archive_path}: {exc}")

    print(f"OK M4 layout: info={info_path} train={train_path} test={test_path}")


def csv_body_is_numeric(frame: pd.DataFrame) -> bool:
    numeric_frame_mask(frame)
    return True


def csv_matrix_from_file(path: Path) -> pd.DataFrame:
    require_file(path)
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"Could not read CSV file {path}: {exc}")
    raise AssertionError("unreachable")


def npy_matrix_from_file(path: Path) -> np.ndarray:
    require_file(path)
    try:
        arr = np.load(path, allow_pickle=True)
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"Could not read NPY file {path}: {exc}")
    return np.asarray(arr)


def validate_csv_triplet_with_label_file(train_path: Path, test_path: Path, label_path: Path, *, seq_len: Optional[int]) -> None:
    train_frame = drop_optional_leading_column(csv_matrix_from_file(train_path))
    test_frame = drop_optional_leading_column(csv_matrix_from_file(test_path))
    label_frame = drop_optional_leading_column(csv_matrix_from_file(label_path))

    csv_body_is_numeric(train_frame)
    csv_body_is_numeric(test_frame)
    csv_body_is_numeric(label_frame)

    if test_frame.shape[0] != label_frame.shape[0]:
        fail(
            f"Anomaly CSV label rows do not match the test rows: test={test_frame.shape[0]}, labels={label_frame.shape[0]}."
        )

    if seq_len is not None:
        check_window_rows(train_frame.shape[0], seq_len, context=f"Anomaly train file {train_path.name}")
        check_window_rows(test_frame.shape[0], seq_len, context=f"Anomaly test file {test_path.name}")

    print(
        f"OK anomaly CSV triplet: train={train_frame.shape} test={test_frame.shape} labels={label_frame.shape}"
    )


def validate_csv_embedded_labels(train_path: Path, test_path: Path, *, seq_len: Optional[int]) -> None:
    train_frame = csv_matrix_from_file(train_path)
    test_frame = csv_matrix_from_file(test_path)

    if train_frame.shape[1] < 2:
        fail(f"Anomaly train file {train_path.name} needs at least two columns.")
    if test_frame.shape[1] < 2:
        fail(f"Anomaly test file {test_path.name} needs at least two columns.")

    train_features = train_frame.iloc[:, :-1]
    test_features = test_frame.iloc[:, :-1]
    test_labels = test_frame.iloc[:, -1:]

    csv_body_is_numeric(train_features)
    csv_body_is_numeric(test_features)
    csv_body_is_numeric(test_labels)

    if seq_len is not None:
        check_window_rows(train_features.shape[0], seq_len, context=f"Anomaly train file {train_path.name}")
        check_window_rows(test_features.shape[0], seq_len, context=f"Anomaly test file {test_path.name}")

    print(
        f"OK anomaly CSV embedded labels: train={train_features.shape} test={test_features.shape} labels={test_labels.shape}"
    )


def validate_npy_triplet(train_path: Path, test_path: Path, label_path: Path, *, seq_len: Optional[int]) -> None:
    train_arr = npy_matrix_from_file(train_path)
    test_arr = npy_matrix_from_file(test_path)
    label_arr = npy_matrix_from_file(label_path)

    try:
        train_arr = np.asarray(train_arr, dtype=float)
        test_arr = np.asarray(test_arr, dtype=float)
        label_arr = np.asarray(label_arr, dtype=float)
    except Exception:
        fail("Anomaly NPY triplet must contain numeric values.")

    if train_arr.ndim != 2:
        fail(f"Anomaly train array {train_path.name} must be 2D; found shape {train_arr.shape}.")
    if test_arr.ndim != 2:
        fail(f"Anomaly test array {test_path.name} must be 2D; found shape {test_arr.shape}.")
    if label_arr.ndim == 1:
        label_arr = label_arr.reshape(-1, 1)
    elif label_arr.ndim != 2:
        fail(f"Anomaly label array {label_path.name} must be 1D or 2D; found shape {label_arr.shape}.")

    if train_arr.shape[0] < 1 or test_arr.shape[0] < 1 or label_arr.shape[0] < 1:
        fail("Anomaly arrays must not be empty.")
    if test_arr.shape[0] != label_arr.shape[0]:
        fail(
            f"Anomaly label rows do not match the test rows: test={test_arr.shape[0]}, labels={label_arr.shape[0]}."
        )
    if seq_len is not None:
        check_window_rows(train_arr.shape[0], seq_len, context=f"Anomaly train array {train_path.name}")
        check_window_rows(test_arr.shape[0], seq_len, context=f"Anomaly test array {test_path.name}")

    print(f"OK anomaly NPY triplet: train={train_arr.shape} test={test_arr.shape} labels={label_arr.shape}")


def validate_anomaly(args: argparse.Namespace, root: Path) -> None:
    train_path = resolve_path(root, args.train_file)
    test_path = resolve_path(root, args.test_file)
    require_file(train_path)
    require_file(test_path)

    label_path = None
    if args.label_file is not None:
        label_path = resolve_path(root, args.label_file)
        require_file(label_path)

    suffixes = {train_path.suffix.lower(), test_path.suffix.lower()}
    if label_path is not None:
        suffixes.add(label_path.suffix.lower())

    if ".npy" in suffixes:
        if label_path is None:
            fail("NPY anomaly validation needs an explicit label file.")
        validate_npy_triplet(train_path, test_path, label_path, seq_len=args.seq_len)
        return

    if label_path is not None:
        validate_csv_triplet_with_label_file(train_path, test_path, label_path, seq_len=args.seq_len)
    else:
        validate_csv_embedded_labels(train_path, test_path, seq_len=args.seq_len)


def validate_uea_file(path: Path, *, strict: bool) -> None:
    require_file(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.rstrip() for line in text.splitlines()]
    lower = text.lower()
    required_tokens = ["@problemname", "@timestamps", "@univariate", "@classlabel", "@data"]
    missing = [token for token in required_tokens if token not in lower]
    if missing:
        fail(f"UEA file {path.name} is missing required header token(s): {', '.join(missing)}")

    data_line_index = next((idx for idx, line in enumerate(lines) if line.strip().lower() == "@data"), None)
    if data_line_index is None:
        fail(f"UEA file {path.name} does not contain an @data section.")
    if not any(line.strip() for line in lines[data_line_index + 1 :]):
        fail(f"UEA file {path.name} has an empty @data section.")

    if not strict:
        return

    try:
        from sktime.datasets import load_from_tsfile_to_dataframe
    except Exception:
        # Fall back to the header check above when sktime is not installed.
        return

    try:
        X, y = load_from_tsfile_to_dataframe(
            str(path), return_separate_X_and_y=True, replace_missing_vals_with="NaN"
        )
    except Exception as exc:
        fail(f"UEA file {path.name} is not a valid sktime .ts archive: {exc}")

    if len(X) == 0:
        fail(f"UEA file {path.name} parsed successfully but contained no samples.")
    if y is None or len(y) == 0:
        fail(f"UEA file {path.name} parsed successfully but contained no labels.")


def validate_uea(args: argparse.Namespace, root: Path) -> None:
    require_dir(root)
    files = sorted(path for path in root.glob("*.ts") if path.is_file())
    if not files:
        fail(f"No .ts files were found in {root}.")

    upper_names = [path.name.upper() for path in files]
    if not args.allow_single_uea_file:
        if not any("TRAIN" in name for name in upper_names):
            fail("UEA classification data should include a TRAIN .ts file.")
        if not any("TEST" in name for name in upper_names):
            fail("UEA classification data should include a TEST .ts file.")

    for path in files:
        validate_uea_file(path, strict=args.uea_strict)

    print(f"OK UEA layout: {len(files)} .ts file(s) validated in {root}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate TimeMixer dataset layouts without importing the source repository."
    )
    parser.add_argument(
        "--data-type",
        required=True,
        choices=["custom", "pems", "solar", "m4", "anomaly-csv", "uea"],
        help="Dataset family to validate.",
    )
    parser.add_argument("--root-path", required=True, help="Dataset root directory.")

    parser.add_argument("--data-path", help="File name relative to --root-path for custom, PEMS, Solar, or M4 layouts.")
    parser.add_argument("--target", default="OT", help="Target column name for custom CSVs.")
    parser.add_argument("--date-column", default="date", help="Date column name for custom CSVs.")
    parser.add_argument("--freq", default="h", help="Frequency string for custom CSV validation.")
    parser.add_argument("--expected-channels", type=int, help="Expected channel count for PEMS archives.")
    parser.add_argument("--npz-key", default="data", help="Array key inside a PEMS .npz archive.")
    parser.add_argument("--seq-len", type=int, help="Optional window-length check for forecasting/anomaly layouts.")
    parser.add_argument("--pred-len", type=int, help="Optional prediction-length check for forecasting layouts.")

    parser.add_argument("--train-file", default="train.csv", help="Anomaly train file name relative to --root-path.")
    parser.add_argument("--test-file", default="test.csv", help="Anomaly test file name relative to --root-path.")
    parser.add_argument(
        "--label-file",
        default=None,
        help="Optional anomaly label file name relative to --root-path. If omitted, the test file's last column is treated as labels.",
    )

    parser.add_argument("--m4-info", default="M4-info.csv", help="M4 info CSV name.")
    parser.add_argument("--m4-training", default="training.npz", help="M4 training archive name.")
    parser.add_argument("--m4-test", default="test.npz", help="M4 test archive name.")
    parser.add_argument(
        "--seasonal-patterns",
        help="Optional M4 seasonal pattern to require in the info file.",
    )

    parser.add_argument(
        "--allow-single-uea-file",
        action="store_true",
        help="Allow a single UEA .ts file instead of requiring TRAIN and TEST files.",
    )
    parser.add_argument(
        "--uea-strict",
        action="store_true",
        help="Try to parse UEA .ts files with sktime when available.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root_path)

    try:
        require_dir(root)
        if args.data_type == "custom":
            validate_custom(args, root)
        elif args.data_type == "pems":
            validate_pems(args, root)
        elif args.data_type == "solar":
            validate_solar(args, root)
        elif args.data_type == "m4":
            validate_m4(args, root)
        elif args.data_type == "anomaly-csv":
            validate_anomaly(args, root)
        elif args.data_type == "uea":
            validate_uea(args, root)
        else:  # pragma: no cover - choices guard this
            fail(f"Unsupported data type: {args.data_type}")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
