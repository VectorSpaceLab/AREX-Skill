#!/usr/bin/env python3
"""
Inspect easy12306 image-tile training assets without running training.

The helper validates captcha.npz / captcha.test.npz schemas, optional 80-row
label vocabularies, and optional image-model file existence. It only imports
Keras/TensorFlow when --load-model is explicitly supplied.

Example:
  python inspect_image_training_assets.py --captcha-npz captcha.npz \
    --captcha-test-npz captcha.test.npz --labels-file texts.txt \
    --model 12306.image.model.h5
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

EXPECTED_CLASSES = 80
BGR_MEAN = np.array([103.939, 116.779, 123.68], dtype=np.float32)


class ValidationError(Exception):
    """Raised when a supplied asset violates the expected contract."""


def _fmt_shape(array: np.ndarray) -> str:
    return "(" + ", ".join(str(dim) for dim in array.shape) + ")"


def _is_integer_like(values: np.ndarray) -> bool:
    if np.issubdtype(values.dtype, np.integer):
        return True
    if not np.issubdtype(values.dtype, np.number):
        return False
    return np.all(np.isfinite(values)) and np.all(np.equal(values, np.round(values)))


def _summary(values: np.ndarray) -> str:
    values = np.asarray(values, dtype=np.float64)
    return (
        f"min={values.min():.6g}, max={values.max():.6g}, "
        f"mean={values.mean():.6g}, std={values.std():.6g}"
    )


def _require_numeric(name: str, array: np.ndarray) -> None:
    if not np.issubdtype(array.dtype, np.number):
        raise ValidationError(f"{name} must be numeric, got dtype {array.dtype}")
    if not np.all(np.isfinite(array)):
        raise ValidationError(f"{name} contains NaN or infinite values")


def validate_images(split: str, images: np.ndarray) -> None:
    if images.ndim != 4:
        raise ValidationError(f"{split}.images must be rank 4 (N,H,W,3), got {_fmt_shape(images)}")
    if images.shape[0] <= 0:
        raise ValidationError(f"{split}.images must contain at least one image")
    if images.shape[-1] != 3:
        raise ValidationError(
            f"{split}.images final channel must be 3 for OpenCV BGR input, got {_fmt_shape(images)}"
        )
    _require_numeric(f"{split}.images", images)
    print(f"[{split}] images: shape={_fmt_shape(images)}, dtype={images.dtype}, final_channel=3")
    print(f"[{split}] preprocessing: float32 images minus BGR means {BGR_MEAN.tolist()}")


def validate_labels(split: str, labels: np.ndarray, image_count: int, *, compute_weights: bool) -> str:
    if labels.shape[0] != image_count:
        raise ValidationError(
            f"{split}.labels first dimension {labels.shape[0]} does not match images count {image_count}"
        )
    if labels.ndim == 1 or (labels.ndim == 2 and labels.shape[1] == 1):
        sparse = labels.reshape(-1)
        if not _is_integer_like(sparse):
            raise ValidationError(f"{split}.labels sparse ids must be integer-like")
        sparse = sparse.astype(np.int64)
        if sparse.min() < 0 or sparse.max() >= EXPECTED_CLASSES:
            raise ValidationError(
                f"{split}.labels sparse ids must be in [0,{EXPECTED_CLASSES - 1}], "
                f"got min={sparse.min()} max={sparse.max()}"
            )
        unique = np.unique(sparse)
        print(
            f"[{split}] labels: sparse ids, shape={_fmt_shape(labels)}, "
            f"unique_classes={len(unique)}, min={sparse.min()}, max={sparse.max()}"
        )
        if compute_weights:
            print(f"[{split}] sample weights: skipped for sparse labels")
        return "sparse"

    if labels.ndim == 2 and labels.shape[1] == EXPECTED_CLASSES:
        _require_numeric(f"{split}.labels", labels)
        if np.any(labels < 0):
            raise ValidationError(f"{split}.labels vote/probability matrix must be non-negative")
        row_sums = labels.sum(axis=1).astype(np.float64)
        if np.any(row_sums <= 0):
            bad = np.where(row_sums <= 0)[0][:10].tolist()
            raise ValidationError(
                f"{split}.labels vote/probability rows must have positive sums; first bad rows={bad}"
            )
        winners = labels.argmax(axis=1)
        print(
            f"[{split}] labels: 80-column vote/probability matrix, shape={_fmt_shape(labels)}, "
            f"winner_classes={len(np.unique(winners))}, row_sum_{_summary(row_sums)}"
        )
        if compute_weights:
            weights = labels.max(axis=1).astype(np.float64) / np.sqrt(row_sums)
            mean = weights.mean()
            if not math.isfinite(float(mean)) or mean == 0:
                raise ValidationError(f"{split}.sample_weight mean is invalid: {mean}")
            weights = weights / mean
            if not np.all(np.isfinite(weights)):
                raise ValidationError(f"{split}.sample_weight contains NaN or infinite values")
            print(f"[{split}] sample_weight formula: max(row) / sqrt(sum(row)), normalized by mean")
            print(f"[{split}] sample_weight summary: {_summary(weights)}")
        return "matrix80"

    raise ValidationError(
        f"{split}.labels must be sparse ids with length N or an (N,{EXPECTED_CLASSES}) matrix, "
        f"got shape={_fmt_shape(labels)}"
    )


def validate_npz(path: Path, split: str, *, compute_weights: bool) -> str:
    if not path.exists():
        raise ValidationError(f"{split} file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"{split} path is not a file: {path}")
    try:
        with np.load(path, allow_pickle=False) as data:
            keys = set(data.files)
            missing = {"images", "labels"} - keys
            if missing:
                raise ValidationError(f"{split} missing required arrays: {sorted(missing)}")
            images = np.asarray(data["images"])
            labels = np.asarray(data["labels"])
    except ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001 - report concise CLI validation failures
        raise ValidationError(f"failed to read {split} npz {path}: {exc}") from exc

    print(f"[{split}] file: {path}")
    validate_images(split, images)
    label_kind = validate_labels(split, labels, images.shape[0], compute_weights=compute_weights)
    return label_kind


def validate_labels_file(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"labels file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"labels path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"labels file must be UTF-8 text: {exc}") from exc
    rows = text.splitlines()
    if len(rows) != EXPECTED_CLASSES:
        raise ValidationError(f"labels file must contain {EXPECTED_CLASSES} rows, got {len(rows)}")
    empty = [idx for idx, value in enumerate(rows) if value == ""]
    print(f"[labels-file] rows={len(rows)}, first={rows[0]!r}, last={rows[-1]!r}")
    if empty:
        print(f"[labels-file] warning: empty label rows at indexes {empty[:10]}")


def validate_model_file(path: Path, *, load_model: bool) -> None:
    if not path.exists():
        raise ValidationError(f"model file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"model path is not a file: {path}")
    print(f"[model] exists: {path} ({path.stat().st_size} bytes)")
    if not load_model:
        print("[model] not loaded; pass --load-model to import Keras/TensorFlow and inspect it")
        return

    try:
        from keras import models  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"failed to import Keras while --load-model was set: {exc}") from exc

    try:
        model = models.load_model(path)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"failed to load model {path}: {exc}") from exc
    print(f"[model] loaded: input_shape={getattr(model, 'input_shape', None)}, output_shape={getattr(model, 'output_shape', None)}")
    output_shape = getattr(model, "output_shape", None)
    if isinstance(output_shape, tuple) and output_shape and output_shape[-1] != EXPECTED_CLASSES:
        raise ValidationError(f"model output last dimension should be {EXPECTED_CLASSES}, got {output_shape}")


def run_validation(args: argparse.Namespace) -> None:
    if args.captcha_npz is not None:
        validate_npz(Path(args.captcha_npz), "captcha", compute_weights=True)
    else:
        print("[captcha] skipped: --captcha-npz not supplied")

    if args.captcha_test_npz is not None:
        validate_npz(Path(args.captcha_test_npz), "captcha.test", compute_weights=False)
    else:
        print("[captcha.test] skipped: --captcha-test-npz not supplied")

    if args.labels_file is not None:
        validate_labels_file(Path(args.labels_file))
    else:
        print("[labels-file] skipped: --labels-file not supplied")

    if args.model is not None:
        validate_model_file(Path(args.model), load_model=args.load_model)
    else:
        print("[model] skipped: --model not supplied")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="easy12306-image-assets-") as tmp:
        root = Path(tmp)
        train_images = np.arange(4 * 5 * 6 * 3, dtype=np.uint8).reshape(4, 5, 6, 3)
        train_labels = np.zeros((4, EXPECTED_CLASSES), dtype=np.float32)
        train_labels[0, 0] = 10
        train_labels[0, 1] = 2
        train_labels[1, 7] = 3
        train_labels[2, 7] = 1
        train_labels[2, 9] = 4
        train_labels[3, 79] = 5
        test_images = np.zeros((3, 5, 6, 3), dtype=np.uint8)
        test_labels = np.array([0, 7, 79], dtype=np.int64)
        labels_text = "".join(f"label-{idx:02d}\n" for idx in range(EXPECTED_CLASSES))

        train_npz = root / "captcha.npz"
        test_npz = root / "captcha.test.npz"
        labels_file = root / "texts.txt"
        np.savez(train_npz, images=train_images, labels=train_labels)
        np.savez(test_npz, images=test_images, labels=test_labels)
        labels_file.write_text(labels_text, encoding="utf-8")

        ns = argparse.Namespace(
            captcha_npz=str(train_npz),
            captcha_test_npz=str(test_npz),
            labels_file=str(labels_file),
            model=None,
            load_model=False,
        )
        run_validation(ns)
    print("SELF_TEST_OK")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate easy12306 image classifier training assets without running training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--captcha-npz", help="Path to captcha.npz containing images and labels arrays.")
    parser.add_argument("--captcha-test-npz", help="Optional path to captcha.test.npz for manual validation data.")
    parser.add_argument("--labels-file", help="Optional 80-row labels vocabulary file, usually texts.txt.")
    parser.add_argument("--model", help="Optional path to 12306.image.model.h5 or equivalent image model file.")
    parser.add_argument(
        "--load-model",
        action="store_true",
        help="Actually import Keras/TensorFlow and load --model. Omitted by default for safe schema checks.",
    )
    parser.add_argument("--self-test", action="store_true", help="Create tiny temporary fixtures and validate them.")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            run_self_test()
        else:
            run_validation(args)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
