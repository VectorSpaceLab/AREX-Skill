#!/usr/bin/env python3
"""Validate easy12306 captcha preprocessing artifacts.

This script preserves the safe geometry and schema checks from the legacy
preprocessing workflow without downloading captchas or importing credentialed
OCR helpers.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np

try:  # Keep --help and label/npz-only checks usable when OpenCV is absent.
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - depends on host environment
    cv2 = None  # type: ignore
    _CV2_IMPORT_ERROR = exc
else:
    _CV2_IMPORT_ERROR = None

TEXT_ROWS = (3, 22)
TEXT_COLS = (120, 177)
TEXT_SHAPE = (19, 57)
TILE_LENGTH = 67
TILE_INTERVAL = 5
TILE_STEP = TILE_LENGTH + TILE_INTERVAL
TILE_ROW_START = 40
TILE_COL_START = 5
TILE_SHAPE = (67, 67)
EXPECTED_TILE_COUNT = 8
EXPECTED_LABEL_ROWS = 80


def _require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError(f"OpenCV is required for image checks: {_CV2_IMPORT_ERROR}")


def get_text(img: np.ndarray, offset: int = 0) -> np.ndarray:
    """Return the legacy prompt-text crop."""
    return img[TEXT_ROWS[0] : TEXT_ROWS[1], TEXT_COLS[0] + offset : TEXT_COLS[1] + offset]


def iter_tiles(img: np.ndarray) -> Iterable[tuple[int, int, np.ndarray]]:
    """Yield legacy row-major 67x67 tiles."""
    for row in range(TILE_ROW_START, img.shape[0] - TILE_LENGTH, TILE_STEP):
        for col in range(TILE_COL_START, img.shape[1] - TILE_LENGTH, TILE_STEP):
            yield row, col, img[row : row + TILE_LENGTH, col : col + TILE_LENGTH]


def read_grayscale_image(path: Path) -> np.ndarray:
    _require_cv2()
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)  # type: ignore[union-attr]
    if img is None:
        raise ValueError(f"could not read image: {path}")
    return img


def validate_image(path: Path) -> list[str]:
    failures: list[str] = []
    img = read_grayscale_image(path)
    print(f"image: {path}")
    print(f"  shape={img.shape} dtype={img.dtype}")

    crop = get_text(img)
    print(f"  text_crop_shape={crop.shape} expected={TEXT_SHAPE}")
    if crop.shape != TEXT_SHAPE:
        failures.append(f"text crop shape {crop.shape} != {TEXT_SHAPE}")

    tiles = list(iter_tiles(img))
    print(f"  tile_count={len(tiles)} expected={EXPECTED_TILE_COUNT}")
    if len(tiles) != EXPECTED_TILE_COUNT:
        failures.append(f"tile count {len(tiles)} != {EXPECTED_TILE_COUNT}")
    for idx, (row, col, tile) in enumerate(tiles):
        print(f"  tile[{idx}] row={row} col={col} shape={tile.shape}")
        if tile.shape != TILE_SHAPE:
            failures.append(f"tile[{idx}] shape {tile.shape} != {TILE_SHAPE}")
    return failures


def validate_labels_file(path: Path) -> list[str]:
    failures: list[str] = []
    rows = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    print(f"labels_file: {path}")
    print(f"  non_empty_rows={len(rows)} expected={EXPECTED_LABEL_ROWS}")
    if len(rows) != EXPECTED_LABEL_ROWS:
        failures.append(f"label row count {len(rows)} != {EXPECTED_LABEL_ROWS}")
    return failures


def validate_npz(path: Path) -> list[str]:
    failures: list[str] = []
    print(f"npz: {path}")
    try:
        data = np.load(path, allow_pickle=False)
    except ValueError:
        data = np.load(path, allow_pickle=True)
        failures.append("npz required pickle loading; prefer plain numeric arrays")
    with data:
        keys = set(data.files)
        print(f"  keys={sorted(keys)}")
        for key in ("texts", "images"):
            if key not in keys:
                failures.append(f"missing key: {key}")
        if "texts" not in keys or "images" not in keys:
            return failures
        texts = data["texts"]
        images = data["images"]
        print(f"  texts_shape={texts.shape} dtype={texts.dtype}")
        print(f"  images_shape={images.shape} dtype={images.dtype}")
        if texts.ndim != 3 or tuple(texts.shape[1:]) != TEXT_SHAPE:
            failures.append(f"texts shape {texts.shape} is not (N,{TEXT_SHAPE[0]},{TEXT_SHAPE[1]})")
        if images.ndim != 3 or tuple(images.shape[1:]) != (EXPECTED_TILE_COUNT, 8):
            failures.append(f"images shape {images.shape} is not (N,{EXPECTED_TILE_COUNT},8)")
        if texts.ndim >= 1 and images.ndim >= 1 and texts.shape[0] != images.shape[0]:
            failures.append(f"texts/images sample count mismatch: {texts.shape[0]} != {images.shape[0]}")
        if images.dtype != np.uint8:
            print("  warning=images should usually be uint8 packed hash bytes")
    return failures


def synthetic_captcha() -> np.ndarray:
    yy = np.arange(190, dtype=np.uint16)[:, None]
    xx = np.arange(293, dtype=np.uint16)[None, :]
    img = ((yy * 5 + xx * 3) % 256).astype(np.uint8)
    img[3:22, 120:177] = 230
    for row in (40, 112):
        for col in (5, 77, 149, 221):
            img[row : row + TILE_LENGTH, col : col + TILE_LENGTH] ^= 0x55
    return img


def run_self_test() -> list[str]:
    _require_cv2()
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        image_path = tmp / "synthetic_captcha.png"
        labels_path = tmp / "labels.txt"
        npz_path = tmp / "data.npz"

        img = synthetic_captcha()
        ok = cv2.imwrite(str(image_path), img)  # type: ignore[union-attr]
        if not ok:
            raise RuntimeError("failed to write synthetic image")
        labels_path.write_text("\n".join(f"label_{i:02d}" for i in range(EXPECTED_LABEL_ROWS)) + "\n", encoding="utf-8")
        texts = np.stack([get_text(img), get_text(img)], axis=0)
        images = np.arange(2 * EXPECTED_TILE_COUNT * 8, dtype=np.uint8).reshape(2, EXPECTED_TILE_COUNT, 8)
        np.savez(npz_path, texts=texts, images=images)

        failures.extend(validate_image(image_path))
        failures.extend(validate_labels_file(labels_path))
        failures.extend(validate_npz(npz_path))
    if not failures:
        print("self-test: PASS")
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate easy12306 captcha crop/tile geometry and data.npz schemas.",
    )
    parser.add_argument("--image", type=Path, help="Full captcha image to validate; expected canonical geometry is 190x293.")
    parser.add_argument("--labels-file", type=Path, help="Optional 80-row label vocabulary file to count.")
    parser.add_argument("--npz", type=Path, help="Optional data.npz with keys texts and images.")
    parser.add_argument("--self-test", action="store_true", help="Run synthetic image/labels/npz checks and exit 0 on success.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.self_test or args.image or args.labels_file or args.npz):
        parser.error("provide --self-test or at least one of --image, --labels-file, --npz")

    failures: list[str] = []
    try:
        if args.self_test:
            failures.extend(run_self_test())
        if args.image:
            failures.extend(validate_image(args.image))
        if args.labels_file:
            failures.extend(validate_labels_file(args.labels_file))
        if args.npz:
            failures.extend(validate_npz(args.npz))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
