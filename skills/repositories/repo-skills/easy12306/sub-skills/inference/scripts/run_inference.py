#!/usr/bin/env python3
"""Run easy12306-compatible inference from user-supplied artifacts.

This is a self-contained adapter for the legacy flat-script behavior. It accepts
explicit paths instead of depending on hard-coded files in an original checkout.
Use check_inference_assets.py first when diagnosing paths, labels, or geometry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover
    cv2 = None  # type: ignore
    _CV2_IMPORT_ERROR = exc
else:
    _CV2_IMPORT_ERROR = None

EXPECTED_LABEL_ROWS = 80
BGR_MEAN = np.array([103.939, 116.779, 123.68], dtype=np.float32)
TILE_LENGTH = 67
TILE_STEP = 72


def _require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError(f"OpenCV is required: {_CV2_IMPORT_ERROR}")


def read_labels(path: Path) -> list[str]:
    rows = path.read_text(encoding="utf-8-sig").splitlines()
    if len(rows) != EXPECTED_LABEL_ROWS or any(row == "" for row in rows):
        raise ValueError(f"labels file must contain exactly {EXPECTED_LABEL_ROWS} non-empty rows: {path}")
    return rows


def load_keras_model(path: Path, role: str):
    if not path.exists():
        raise ValueError(f"{role} model file does not exist: {path}")
    try:
        from keras import models  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "failed to import Keras. For legacy easy12306 artifacts, prefer "
            f"TensorFlow/Keras 2.15-compatible packages. Import error: {exc}"
        ) from exc
    try:
        return models.load_model(path, compile=False)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"failed to load {role} model {path}: {exc}") from exc


def read_color_image(path: Path):
    _require_cv2()
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)  # type: ignore[union-attr]
    if img is None:
        raise ValueError(f"could not read image: {path}")
    return img


def crop_text_tensor(img: np.ndarray, offset: int = 0) -> np.ndarray:
    _require_cv2()
    crop = img[3:22, 120 + offset : 177 + offset]
    if crop.shape[:2] != (19, 57):
        raise ValueError(f"text crop offset={offset} has shape {crop.shape[:2]}, expected (19, 57)")
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)  # type: ignore[union-attr]
    gray = gray / 255.0
    h, w = gray.shape
    gray.shape = (1, h, w, 1)
    return gray


def iter_tiles(img: np.ndarray):
    for row in range(40, img.shape[0] - TILE_LENGTH, TILE_STEP):
        for col in range(5, img.shape[1] - TILE_LENGTH, TILE_STEP):
            yield row, col, img[row : row + TILE_LENGTH, col : col + TILE_LENGTH]


def preprocess_tiles(tiles: list[np.ndarray]) -> np.ndarray:
    arr = np.asarray(tiles).astype("float32")
    if arr.shape != (8, 67, 67, 3):
        raise ValueError(f"tile tensor shape must be (8,67,67,3), got {arr.shape}")
    arr -= BGR_MEAN
    return arr


def classify_text(model, tensor: np.ndarray, labels: list[str]) -> tuple[int, str, list[float]]:
    probs = np.asarray(model.predict(tensor, verbose=0))
    class_id = int(probs.argmax())
    if class_id < 0 or class_id >= len(labels):
        raise ValueError(f"text model predicted class {class_id}, outside labels range")
    return class_id, labels[class_id], probs.reshape(-1).astype(float).tolist()


def run_captcha(args: argparse.Namespace) -> dict:
    labels = read_labels(args.labels_file)
    img = read_color_image(args.captcha_image)
    text_model = load_keras_model(args.text_model, "text")
    image_model = load_keras_model(args.image_model, "image")

    first_id, first_label, first_probs = classify_text(text_model, crop_text_tensor(img, 0), labels)
    prompts = [{"offset": 0, "class_id": first_id, "label": first_label, "probabilities": first_probs if args.include_probabilities else None}]

    if len(first_label) == 1:
        offset = 27
    elif len(first_label) == 2:
        offset = 47
    else:
        offset = 60
    second_tensor = crop_text_tensor(img, offset)
    if float(second_tensor.mean()) < 0.95:
        second_id, second_label, second_probs = classify_text(text_model, second_tensor, labels)
        prompts.append({"offset": offset, "class_id": second_id, "label": second_label, "probabilities": second_probs if args.include_probabilities else None})

    tile_rows = list(iter_tiles(img))
    if len(tile_rows) != 8:
        raise ValueError(f"expected 8 tiles, got {len(tile_rows)}; run check_inference_assets.py for geometry diagnostics")
    tile_tensor = preprocess_tiles([tile for _row, _col, tile in tile_rows])
    probs = np.asarray(image_model.predict(tile_tensor, verbose=0))
    class_ids = probs.argmax(axis=1)
    tiles = []
    for pos, class_id_np in enumerate(class_ids):
        class_id = int(class_id_np)
        if class_id < 0 or class_id >= len(labels):
            raise ValueError(f"image model predicted class {class_id}, outside labels range")
        tiles.append({
            "row": pos // 4,
            "col": pos % 4,
            "class_id": class_id,
            "label": labels[class_id],
            "probability": float(probs[pos].max()) if args.include_probabilities else None,
        })
    return {"prompts": prompts, "tiles": tiles}


def run_tile(args: argparse.Namespace) -> dict:
    _require_cv2()
    labels = read_labels(args.labels_file)
    image_model = load_keras_model(args.image_model, "image")
    img = read_color_image(args.image)
    resized = cv2.resize(img, (67, 67))  # type: ignore[union-attr]
    tensor = resized.reshape(-1, 67, 67, 3).astype("float32")
    tensor -= BGR_MEAN
    probs = np.asarray(image_model.predict(tensor, verbose=0))
    class_id = int(probs.argmax(axis=1)[0])
    if class_id < 0 or class_id >= len(labels):
        raise ValueError(f"image model predicted class {class_id}, outside labels range")
    return {"class_id": class_id, "label": labels[class_id], "probability": float(probs.max())}


def emit_human(result: dict, mode: str) -> None:
    if mode == "captcha":
        for prompt in result["prompts"]:
            print(prompt["label"])
        for tile in result["tiles"]:
            print(tile["row"], tile["col"], tile["label"])
    else:
        print([result["probability"]])
        print([result["class_id"]])
        print(result["label"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run self-contained easy12306-compatible inference from explicit artifact paths.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of legacy text output.")
    parser.add_argument("--include-probabilities", action="store_true", help="Include probabilities in JSON output where available.")
    sub = parser.add_subparsers(dest="mode", required=True)

    captcha = sub.add_parser("captcha", help="Classify a full 12306 captcha image with text and image models.")
    captcha.add_argument("--captcha-image", type=Path, required=True)
    captcha.add_argument("--text-model", type=Path, required=True)
    captcha.add_argument("--image-model", type=Path, required=True)
    captcha.add_argument("--labels-file", type=Path, required=True)

    tile = sub.add_parser("tile", help="Classify one object image/tile with the image model.")
    tile.add_argument("--image", type=Path, required=True)
    tile.add_argument("--image-model", type=Path, required=True)
    tile.add_argument("--labels-file", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_captcha(args) if args.mode == "captcha" else run_tile(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_human(result, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
