#!/usr/bin/env python3
"""Inspect easy12306 text-classifier training and prediction assets.

The checker validates dataset keys/shapes, 80-label vocabulary files, and optional
model-file presence. It does not import Keras or load a model unless --load-model
is explicitly supplied.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence


class Report:
    def __init__(self) -> None:
        self.notes: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def note(self, message: str) -> None:
        self.notes.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def emit(self) -> None:
        for message in self.notes:
            print(f"[ok] {message}")
        for message in self.warnings:
            print(f"[warn] {message}")
        for message in self.errors:
            print(f"[error] {message}")
        print("RESULT: " + ("PASS" if self.ok else "FAIL"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate easy12306 text-model datasets, label vocabulary files, "
            "and optional model artifacts without running training."
        )
    )
    parser.add_argument("--texts-npz", type=Path, help="Base texts.npz with arrays 'texts' and 'labels'.")
    parser.add_argument(
        "--texts-v2-npz",
        type=Path,
        help="Optional texts.v2.npz statistical dataset with arrays 'texts' and 'labels'.",
    )
    parser.add_argument(
        "--labels-file",
        type=Path,
        help="80-row label vocabulary file; raw one-label-per-line or simple indexed Markdown table.",
    )
    parser.add_argument("--model", type=Path, help="Optional text model .h5 file; existence is checked.")
    parser.add_argument(
        "--load-model",
        action="store_true",
        help="Actually import Keras and load --model with compile=False. Omitted by default.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Create tiny temporary fixtures, validate them, and exit 0 on success.",
    )
    return parser


def import_numpy(report: Report):
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised only when numpy missing
        report.error(
            "NumPy is required for dataset validation. Install numpy in the active "
            f"environment before running this checker. Import error: {exc}"
        )
        return None
    return np


def is_integer_like(np, array) -> bool:
    if np.issubdtype(array.dtype, np.integer):
        return True
    if not np.issubdtype(array.dtype, np.number):
        return False
    if array.size == 0:
        return True
    finite = np.isfinite(array)
    if not bool(np.all(finite)):
        return False
    return bool(np.all(np.equal(array, np.floor(array))))


def describe_sparse_labels(np, labels, classes: int, dataset_name: str, report: Report) -> None:
    if labels.ndim != 1:
        report.error(f"{dataset_name}: sparse labels must be 1D, got shape {labels.shape}.")
        return
    if labels.size == 0:
        report.warn(f"{dataset_name}: labels array is empty; training will not be meaningful.")
        return
    if not is_integer_like(np, labels):
        report.error(f"{dataset_name}: sparse labels must be integer-like, got dtype {labels.dtype}.")
        return
    labels_i = labels.astype("int64", copy=False)
    lo = int(labels_i.min())
    hi = int(labels_i.max())
    if lo < 0 or hi >= classes:
        report.error(f"{dataset_name}: sparse label ids must be in [0, {classes - 1}], got range [{lo}, {hi}].")
    else:
        unique = int(len(np.unique(labels_i)))
        report.note(f"{dataset_name}: detected sparse label ids in [0, {classes - 1}] with {unique} observed classes.")


def describe_v2_labels(np, labels, classes: int, dataset_name: str, report: Report) -> None:
    if labels.ndim == 1:
        describe_sparse_labels(np, labels, classes, dataset_name, report)
        report.note(
            f"{dataset_name}: v2 labels are sparse ids; this is accepted for inspection, "
            "but convert to an 80-column one-hot/vote matrix before using the unmodified load_data_v2 merge."
        )
        return

    if labels.ndim != 2:
        report.error(f"{dataset_name}: v2 labels must be sparse 1D ids or a 2D one-hot/vote matrix, got shape {labels.shape}.")
        return
    if labels.shape[1] != classes:
        report.error(f"{dataset_name}: v2 label matrix must have {classes} columns, got {labels.shape[1]}.")
        return
    if not np.issubdtype(labels.dtype, np.number):
        report.error(f"{dataset_name}: v2 label matrix must be numeric, got dtype {labels.dtype}.")
        return
    if labels.size and not bool(np.all(np.isfinite(labels))):
        report.error(f"{dataset_name}: v2 label matrix contains NaN or infinite values.")
        return
    if labels.size and float(labels.min()) < 0.0:
        report.error(f"{dataset_name}: v2 vote/soft-target labels should be non-negative.")
        return

    if labels.size == 0:
        report.warn(f"{dataset_name}: v2 label matrix is empty.")
        return

    row_sums = labels.sum(axis=1)
    is_binary = bool(np.all((labels == 0) | (labels == 1)))
    is_one_hot = is_binary and bool(np.allclose(row_sums, 1.0))
    positive_rows = int(np.count_nonzero(row_sums > 0))
    if is_one_hot:
        report.note(f"{dataset_name}: detected one-hot v2 label matrix shaped {labels.shape}.")
    else:
        report.note(
            f"{dataset_name}: detected vote/soft-target v2 label matrix shaped {labels.shape}; "
            f"{positive_rows}/{labels.shape[0]} rows have positive total weight."
        )
        if positive_rows != labels.shape[0]:
            report.warn(f"{dataset_name}: some v2 label rows have no positive class weight.")


def validate_text_values(np, texts, dataset_name: str, report: Report) -> None:
    if not np.issubdtype(texts.dtype, np.number):
        report.error(f"{dataset_name}: texts must be numeric, got dtype {texts.dtype}.")
        return
    if texts.size == 0:
        report.warn(f"{dataset_name}: texts array is empty; training will not be meaningful.")
        return
    if not bool(np.all(np.isfinite(texts))):
        report.error(f"{dataset_name}: texts contains NaN or infinite values.")
        return
    try:
        min_value = float(texts.min())
        max_value = float(texts.max())
    except ValueError:
        return
    if min_value < 0 or max_value > 255:
        report.warn(
            f"{dataset_name}: text pixel range [{min_value:g}, {max_value:g}] is outside the usual [0, 255] range."
        )
    elif max_value <= 1.0:
        report.warn(
            f"{dataset_name}: text pixels appear already normalized to [0, 1]; the legacy loader divides by 255 again."
        )


def validate_npz(path: Path, dataset_name: str, classes: int, v2: bool, report: Report) -> None:
    np = import_numpy(report)
    if np is None:
        return
    if not path.exists():
        report.error(f"{dataset_name}: file does not exist: {path}")
        return
    if not path.is_file():
        report.error(f"{dataset_name}: path is not a file: {path}")
        return

    try:
        with np.load(path, allow_pickle=False) as data:
            keys = set(data.files)
            missing = {"texts", "labels"} - keys
            if missing:
                report.error(f"{dataset_name}: missing required array(s): {', '.join(sorted(missing))}.")
                return
            texts = data["texts"]
            labels = data["labels"]
    except Exception as exc:
        report.error(f"{dataset_name}: could not read npz file {path}: {exc}")
        return

    if texts.ndim < 3:
        report.error(f"{dataset_name}: texts must be at least 3D as (n, h, w), got shape {texts.shape}.")
        return
    n, h, w = int(texts.shape[0]), int(texts.shape[1]), int(texts.shape[2])
    if n <= 0 or h <= 0 or w <= 0:
        report.error(f"{dataset_name}: texts first three dimensions must be positive, got shape {texts.shape}.")
        return
    if texts.ndim != 3:
        report.warn(
            f"{dataset_name}: texts shape is {texts.shape}; the legacy load_data implementation expects exactly (n, h, w)."
        )
    if labels.ndim == 0 or int(labels.shape[0]) != n:
        report.error(f"{dataset_name}: labels first dimension must match texts n={n}, got shape {labels.shape}.")
        return

    validate_text_values(np, texts, dataset_name, report)
    report.note(f"{dataset_name}: texts shape {texts.shape}; labels shape {labels.shape}.")

    if v2:
        describe_v2_labels(np, labels, classes, dataset_name, report)
    else:
        if labels.ndim != 1:
            report.error(
                f"{dataset_name}: base texts.npz labels should be sparse 1D ids for sparse loss/to_categorical, got shape {labels.shape}."
            )
        else:
            describe_sparse_labels(np, labels, classes, dataset_name, report)


def parse_markdown_table_labels(lines: Sequence[str]) -> List[str]:
    labels: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        first = cells[0]
        if first.isdigit():
            labels.append(cells[1])
    return labels


def parse_raw_labels(lines: Sequence[str]) -> List[str]:
    labels: List[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            continue
        if stripped in {"---", "| --- | --- |", "|---|---|"}:
            continue
        labels.append(stripped)
    return labels


def validate_labels_file(path: Path, classes: int, report: Report) -> Optional[List[str]]:
    if not path.exists():
        report.error(f"labels file does not exist: {path}")
        return None
    if not path.is_file():
        report.error(f"labels path is not a file: {path}")
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        report.error(f"labels file must be UTF-8 text: {exc}")
        return None
    except Exception as exc:
        report.error(f"could not read labels file {path}: {exc}")
        return None

    table_labels = parse_markdown_table_labels(lines)
    labels = table_labels if table_labels else parse_raw_labels(lines)
    if len(labels) != classes:
        source = "indexed Markdown table" if table_labels else "non-empty non-comment rows"
        report.error(f"labels file must contain exactly {classes} labels from {source}, found {len(labels)}.")
        return labels
    if any(not label for label in labels):
        report.error("labels file contains an empty label row.")
    duplicate_count = len(labels) - len(set(labels))
    if duplicate_count:
        report.warn(f"labels file has {duplicate_count} duplicate label row(s); verify vocabulary order manually.")
    report.note(f"labels file: detected {classes} labels; first='{labels[0]}', last='{labels[-1]}'.")
    return labels


def validate_model(path: Path, load_model: bool, classes: int, report: Report) -> None:
    if not path.exists():
        report.error(f"model file does not exist: {path}")
        return
    if not path.is_file():
        report.error(f"model path is not a file: {path}")
        return
    size = path.stat().st_size
    report.note(f"model file exists: {path} ({size} bytes).")
    if not load_model:
        report.note("model load skipped; pass --load-model to import Keras and load the artifact with compile=False.")
        return

    try:
        from keras import models  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional environment
        report.error(
            "--load-model requested, but Keras could not be imported. Use a Python 3.11 "
            f"environment with Keras/TensorFlow 2.15-compatible APIs when checking legacy artifacts. Import error: {exc}"
        )
        return
    try:
        model = models.load_model(str(path), compile=False)
    except Exception as exc:  # pragma: no cover - depends on optional artifact
        report.error(f"Keras failed to load model with compile=False: {exc}")
        return
    output_shape = getattr(model, "output_shape", None)
    report.note(f"Keras loaded model with compile=False; output_shape={output_shape!r}.")
    last_dim = None
    if isinstance(output_shape, tuple) and output_shape:
        last_dim = output_shape[-1]
    elif isinstance(output_shape, list) and output_shape and isinstance(output_shape[0], tuple):
        last_dim = output_shape[0][-1]
    if last_dim is not None and last_dim != classes:
        report.warn(f"loaded model output last dimension is {last_dim}, expected {classes} for easy12306 text labels.")


def run_checks(
    texts_npz: Optional[Path],
    texts_v2_npz: Optional[Path],
    labels_file: Optional[Path],
    model: Optional[Path],
    load_model: bool,
    classes: int = 80,
) -> Report:
    report = Report()
    if texts_npz is not None:
        validate_npz(texts_npz, "texts.npz", classes, v2=False, report=report)
    if texts_v2_npz is not None:
        validate_npz(texts_v2_npz, "texts.v2.npz", classes, v2=True, report=report)
    if labels_file is not None:
        validate_labels_file(labels_file, classes, report)
    if model is not None:
        validate_model(model, load_model, classes, report)
    elif load_model:
        report.error("--load-model requires --model.")
    if all(value is None for value in (texts_npz, texts_v2_npz, labels_file, model)) and not load_model:
        report.note("no assets were provided; use --self-test or pass one or more asset paths to validate.")
    return report


def self_test() -> int:
    report = Report()
    np = import_numpy(report)
    if np is None:
        report.emit()
        return 1

    with tempfile.TemporaryDirectory(prefix="easy12306_text_assets_") as tmp_dir:
        tmp = Path(tmp_dir)
        texts = (np.arange(4 * 19 * 57, dtype=np.uint16) % 256).reshape(4, 19, 57).astype(np.uint8)
        labels = np.array([0, 1, 2, 79], dtype=np.int64)
        np.savez(tmp / "texts.npz", texts=texts, labels=labels)

        v2_labels = np.eye(80, dtype=np.float32)[[0, 1, 2, 3]]
        np.savez(tmp / "texts.v2.npz", texts=texts, labels=v2_labels)

        labels_text = "\n".join(f"label_{idx:02d}" for idx in range(80)) + "\n"
        (tmp / "labels.txt").write_text(labels_text, encoding="utf-8")
        (tmp / "model.h5").write_bytes(b"existence-only fixture; not a real Keras model\n")

        report = run_checks(
            texts_npz=tmp / "texts.npz",
            texts_v2_npz=tmp / "texts.v2.npz",
            labels_file=tmp / "labels.txt",
            model=tmp / "model.h5",
            load_model=False,
        )
    report.emit()
    return 0 if report.ok else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    report = run_checks(
        texts_npz=args.texts_npz,
        texts_v2_npz=args.texts_v2_npz,
        labels_file=args.labels_file,
        model=args.model,
        load_model=args.load_model,
    )
    report.emit()
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
