#!/usr/bin/env python3
"""Validate easy12306 inference assets without requiring the source checkout.

Safe default checks:
- OpenCV can read the captcha image.
- Legacy text crop and 8 tile geometry match easy12306 expectations.
- The shared 80-row label vocabulary is present.
- The expected text and image model files exist.

Pass --load-models only when the user explicitly wants Keras/TensorFlow to load
.h5 artifacts. This can be slower and may expose legacy Keras compatibility
issues, so it is intentionally opt-in.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np

try:  # Keep --help and label/model-only diagnostics usable without OpenCV.
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - host-dependent
    cv2 = None  # type: ignore
    _CV2_IMPORT_ERROR = exc
else:
    _CV2_IMPORT_ERROR = None

TEXT_ROWS = (3, 22)
TEXT_COLS = (120, 177)
TEXT_SHAPE = (19, 57)
SECOND_PROMPT_OFFSETS = (27, 47, 60)
TILE_LENGTH = 67
TILE_INTERVAL = 5
TILE_STEP = TILE_LENGTH + TILE_INTERVAL
TILE_ROW_START = 40
TILE_COL_START = 5
TILE_SHAPE = (67, 67, 3)
EXPECTED_TILE_COUNT = 8
EXPECTED_LABEL_ROWS = 80
BGR_MEAN = np.array([103.939, 116.779, 123.68], dtype=np.float32)


def _require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError(f"OpenCV is required for image checks: {_CV2_IMPORT_ERROR}")


def read_color_image(path: Path) -> np.ndarray:
    _require_cv2()
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)  # type: ignore[union-attr]
    if img is None:
        raise ValueError(f"could not read captcha image: {path}")
    return img


def text_crop(img: np.ndarray, offset: int = 0) -> np.ndarray:
    return img[TEXT_ROWS[0] : TEXT_ROWS[1], TEXT_COLS[0] + offset : TEXT_COLS[1] + offset]


def text_tensor(img: np.ndarray, offset: int = 0) -> np.ndarray:
    _require_cv2()
    crop = text_crop(img, offset)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)  # type: ignore[union-attr]
    gray = gray / 255.0
    h, w = gray.shape
    gray = gray.reshape((1, h, w, 1))
    return gray


def iter_tiles(img: np.ndarray) -> Iterable[tuple[int, int, np.ndarray]]:
    for row in range(TILE_ROW_START, img.shape[0] - TILE_LENGTH, TILE_STEP):
        for col in range(TILE_COL_START, img.shape[1] - TILE_LENGTH, TILE_STEP):
            yield row, col, img[row : row + TILE_LENGTH, col : col + TILE_LENGTH]


def preprocess_tiles(tiles: list[np.ndarray]) -> np.ndarray:
    arr = np.asarray(tiles).astype("float32")
    arr -= BGR_MEAN
    return arr


def read_labels(path: Path) -> list[str]:
    if not path.exists():
        raise ValueError(f"labels file does not exist: {path}")
    rows = path.read_text(encoding="utf-8-sig").splitlines()
    if len(rows) != EXPECTED_LABEL_ROWS:
        raise ValueError(f"labels file must contain {EXPECTED_LABEL_ROWS} rows, got {len(rows)}")
    empty = [idx for idx, value in enumerate(rows) if value == ""]
    if empty:
        raise ValueError(f"labels file contains empty rows at indexes {empty[:10]}")
    return rows


def validate_model_path(path: Path, role: str) -> None:
    if not path.exists():
        raise ValueError(f"{role} model file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"{role} model path is not a file: {path}")
    print(f"[{role}-model] exists: {path} ({path.stat().st_size} bytes)")


def load_model(path: Path, role: str):
    try:
        from keras import models  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "failed to import Keras. For the legacy easy12306 scripts, prefer "
            f"Python 3.11 with TensorFlow/Keras 2.15-compatible packages. Import error: {exc}"
        ) from exc
    try:
        model = models.load_model(path, compile=False)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"failed to load {role} model {path}: {exc}") from exc
    output_shape = getattr(model, "output_shape", None)
    print(f"[{role}-model] loaded: input_shape={getattr(model, 'input_shape', None)} output_shape={output_shape}")
    if isinstance(output_shape, tuple) and output_shape and output_shape[-1] != EXPECTED_LABEL_ROWS:
        raise RuntimeError(f"{role} model output last dimension should be {EXPECTED_LABEL_ROWS}, got {output_shape}")
    return model


def validate_image_geometry(path: Path) -> tuple[np.ndarray, list[np.ndarray]]:
    img = read_color_image(path)
    print(f"[captcha-image] shape={img.shape} dtype={img.dtype}")
    failures: list[str] = []

    first_crop = text_crop(img, 0)
    print(f"[text-crop] offset=0 shape={first_crop.shape[:2]} expected={TEXT_SHAPE}")
    if first_crop.shape[:2] != TEXT_SHAPE:
        failures.append(f"first text crop shape {first_crop.shape[:2]} != {TEXT_SHAPE}")
    for offset in SECOND_PROMPT_OFFSETS:
        crop = text_crop(img, offset)
        print(f"[text-crop] offset={offset} shape={crop.shape[:2]} expected={TEXT_SHAPE}")
        if crop.shape[:2] != TEXT_SHAPE:
            failures.append(f"second text crop offset {offset} shape {crop.shape[:2]} != {TEXT_SHAPE}")

    tiles = list(iter_tiles(img))
    print(f"[tiles] count={len(tiles)} expected={EXPECTED_TILE_COUNT}")
    if len(tiles) != EXPECTED_TILE_COUNT:
        failures.append(f"tile count {len(tiles)} != {EXPECTED_TILE_COUNT}")
    tile_arrays: list[np.ndarray] = []
    for idx, (row, col, tile) in enumerate(tiles):
        print(f"[tiles] tile[{idx}] row={row} col={col} shape={tile.shape}")
        if tile.shape != TILE_SHAPE:
            failures.append(f"tile[{idx}] shape {tile.shape} != {TILE_SHAPE}")
        tile_arrays.append(tile)

    if failures:
        raise ValueError("; ".join(failures))
    tensor = text_tensor(img, 0)
    print(f"[text-tensor] shape={tensor.shape} min={float(tensor.min()):.6g} max={float(tensor.max()):.6g}")
    pre = preprocess_tiles(tile_arrays)
    print(f"[tile-tensor] shape={pre.shape} dtype={pre.dtype} bgr_mean_subtracted={BGR_MEAN.tolist()}")
    return img, tile_arrays


def synthetic_captcha() -> np.ndarray:
    yy = np.arange(190, dtype=np.uint16)[:, None]
    xx = np.arange(293, dtype=np.uint16)[None, :]
    base = ((yy * 7 + xx * 5) % 256).astype(np.uint8)
    img = np.stack([base, np.roll(base, 1, axis=1), np.roll(base, 2, axis=0)], axis=-1)
    img[3:22, 120:177, :] = 240
    img[3:22, 147:204, :] = 250
    img[3:22, 167:224, :] = 245
    for row in (40, 112):
        for col in (5, 77, 149, 221):
            img[row : row + TILE_LENGTH, col : col + TILE_LENGTH, :] ^= 0x33
    return img


def run_self_test() -> None:
    _require_cv2()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        image_path = tmp / "captcha.png"
        labels_path = tmp / "texts.txt"
        text_model = tmp / "model.h5"
        image_model = tmp / "12306.image.model.h5"
        if not cv2.imwrite(str(image_path), synthetic_captcha()):  # type: ignore[union-attr]
            raise RuntimeError("failed to write synthetic captcha image")
        labels_path.write_text("\n".join(f"label_{i:02d}" for i in range(EXPECTED_LABEL_ROWS)) + "\n", encoding="utf-8")
        text_model.write_bytes(b"placeholder")
        image_model.write_bytes(b"placeholder")
        read_labels(labels_path)
        validate_model_path(text_model, "text")
        validate_model_path(image_model, "image")
        validate_image_geometry(image_path)
    print("self-test: PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate easy12306 inference images, labels, and model artifact paths.")
    parser.add_argument("--captcha-image", type=Path, help="Full captcha image to check against easy12306 crop/tile geometry.")
    parser.add_argument("--text-model", type=Path, help="Path to the text prompt model, usually model.h5.")
    parser.add_argument("--image-model", type=Path, help="Path to the image tile model, usually 12306.image.model.h5.")
    parser.add_argument("--labels-file", type=Path, help="Path to the 80-row labels file, usually texts.txt.")
    parser.add_argument("--load-models", action="store_true", help="Load both .h5 models with Keras/TensorFlow after path checks.")
    parser.add_argument("--self-test", action="store_true", help="Run a synthetic geometry/labels/path self-test and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.self_test or args.captcha_image or args.text_model or args.image_model or args.labels_file):
        parser.error("provide --self-test or one or more asset paths to validate")

    try:
        if args.self_test:
            run_self_test()
        if args.labels_file:
            labels = read_labels(args.labels_file)
            print(f"[labels] rows={len(labels)} first={labels[0]!r} last={labels[-1]!r}")
        if args.captcha_image:
            validate_image_geometry(args.captcha_image)
        if args.text_model:
            validate_model_path(args.text_model, "text")
        if args.image_model:
            validate_model_path(args.image_model, "image")
        if args.load_models:
            if not args.text_model or not args.image_model:
                raise ValueError("--load-models requires both --text-model and --image-model")
            load_model(args.text_model, "text")
            load_model(args.image_model, "image")
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
