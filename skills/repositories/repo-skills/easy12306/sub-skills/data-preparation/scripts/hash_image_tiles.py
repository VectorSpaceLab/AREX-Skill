#!/usr/bin/env python3
"""Compute easy12306-compatible packed perceptual hashes.

The script adapts the safe hash functions from the legacy project. It does not
implement wavelet hash because the source version referenced pywt without an
import or dependency contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import numpy as np

try:  # Keep --help available even if image dependencies are missing.
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - depends on host environment
    cv2 = None  # type: ignore
    _CV2_IMPORT_ERROR = exc
else:
    _CV2_IMPORT_ERROR = None

try:
    import scipy.fftpack  # type: ignore
except Exception as exc:  # pragma: no cover - depends on host environment
    scipy = None  # type: ignore
    _SCIPY_IMPORT_ERROR = exc
else:
    _SCIPY_IMPORT_ERROR = None

TILE_LENGTH = 67
TILE_INTERVAL = 5
TILE_STEP = TILE_LENGTH + TILE_INTERVAL
TILE_ROW_START = 40
TILE_COL_START = 5
EXPECTED_TILE_COUNT = 8
HASH_BYTES = 8

HashFn = Callable[[np.ndarray], np.ndarray]


def _require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError(f"OpenCV is required for image hashing: {_CV2_IMPORT_ERROR}")


def _require_scipy() -> None:
    if _SCIPY_IMPORT_ERROR is not None:
        raise RuntimeError(f"SciPy is required for DCT-based hashes: {_SCIPY_IMPORT_ERROR}")


def _gray(img: np.ndarray) -> np.ndarray:
    _require_cv2()
    if img.ndim == 2:
        return img
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # type: ignore[union-attr]
    raise ValueError(f"unsupported image rank: {img.ndim}")


def avhash(im: np.ndarray) -> np.ndarray:
    _require_cv2()
    im = cv2.resize(_gray(im), (8, 8), interpolation=cv2.INTER_CUBIC)  # type: ignore[union-attr]
    avg = im.mean()
    return np.packbits(im > avg)


def phash(im: np.ndarray) -> np.ndarray:
    _require_cv2()
    _require_scipy()
    im = cv2.resize(_gray(im), (32, 32), interpolation=cv2.INTER_CUBIC)  # type: ignore[union-attr]
    im = scipy.fftpack.dct(scipy.fftpack.dct(im, axis=0), axis=1)  # type: ignore[union-attr]
    block = im[:8, :8]
    med = np.median(block)
    return np.packbits(block > med)


def phash_simple(im: np.ndarray) -> np.ndarray:
    _require_cv2()
    _require_scipy()
    im = cv2.resize(_gray(im), (32, 32), interpolation=cv2.INTER_CUBIC)  # type: ignore[union-attr]
    im = scipy.fftpack.dct(im)  # type: ignore[union-attr]
    block = im[:8, 1:9]
    avg = block.mean()
    return np.packbits(block > avg)


def dhash(im: np.ndarray) -> np.ndarray:
    _require_cv2()
    im = cv2.resize(_gray(im), (9, 8), interpolation=cv2.INTER_CUBIC)  # type: ignore[union-attr]
    return np.packbits(im[:, 1:] > im[:, :-1])


def dhash_vertical(im: np.ndarray) -> np.ndarray:
    _require_cv2()
    im = cv2.resize(_gray(im), (8, 9), interpolation=cv2.INTER_CUBIC)  # type: ignore[union-attr]
    return np.packbits(im[1:, :] > im[:-1, :])


HASHERS: dict[str, HashFn] = {
    "avhash": avhash,
    "phash": phash,
    "phash-simple": phash_simple,
    "dhash": dhash,
    "dhash-vertical": dhash_vertical,
}


def iter_tiles(img: np.ndarray):
    for row in range(TILE_ROW_START, img.shape[0] - TILE_LENGTH, TILE_STEP):
        for col in range(TILE_COL_START, img.shape[1] - TILE_LENGTH, TILE_STEP):
            yield row, col, img[row : row + TILE_LENGTH, col : col + TILE_LENGTH]


def read_image(path: Path) -> np.ndarray:
    _require_cv2()
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)  # type: ignore[union-attr]
    if img is None:
        raise ValueError(f"could not read image: {path}")
    return _gray(img)


def packed_hex(vec: np.ndarray) -> str:
    arr = np.asarray(vec, dtype=np.uint8).reshape(-1)
    if arr.size != HASH_BYTES:
        raise ValueError(f"hash length {arr.size} bytes != {HASH_BYTES}")
    return arr.tobytes().hex()


def selected_items(img: np.ndarray, mode: str):
    tiles = list(iter_tiles(img))
    valid_tiles = len(tiles) == EXPECTED_TILE_COUNT and all(tile.shape == (TILE_LENGTH, TILE_LENGTH) for _, _, tile in tiles)
    if mode == "whole" or (mode == "auto" and not valid_tiles):
        return [("whole", None, None, img)]
    if mode in {"tiles", "auto"}:
        if not valid_tiles:
            raise ValueError(f"tile mode expected {EXPECTED_TILE_COUNT} tiles of {TILE_LENGTH}x{TILE_LENGTH}, got {len(tiles)}")
        return [(f"tile_{idx}", row, col, tile) for idx, (row, col, tile) in enumerate(tiles)]
    raise ValueError(f"unknown mode: {mode}")


def synthetic_captcha() -> np.ndarray:
    yy = np.arange(190, dtype=np.uint16)[:, None]
    xx = np.arange(293, dtype=np.uint16)[None, :]
    img = ((yy * 7 + xx * 11) % 256).astype(np.uint8)
    for row in (40, 112):
        for col in (5, 77, 149, 221):
            img[row : row + TILE_LENGTH, col : col + TILE_LENGTH] ^= 0x33
    return img


def run_self_test() -> None:
    img = synthetic_captcha()
    for method, fn in HASHERS.items():
        whole = fn(img)
        if np.asarray(whole).reshape(-1).size != HASH_BYTES:
            raise AssertionError(f"{method} whole hash length mismatch")
        items = selected_items(img, "tiles")
        if len(items) != EXPECTED_TILE_COUNT:
            raise AssertionError(f"{method} tile count mismatch")
        for name, _row, _col, tile in items:
            digest = fn(tile)
            if np.asarray(digest).reshape(-1).size != HASH_BYTES:
                raise AssertionError(f"{method} {name} hash length mismatch")
    print("self-test: PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute packed easy12306 hash hex strings for a whole image or its eight captcha tiles.",
        epilog="whash is intentionally excluded because the source version referenced pywt without importing it.",
    )
    parser.add_argument("--image", type=Path, help="Image to hash. Canonical full captcha images produce eight tile hashes in auto mode.")
    parser.add_argument("--method", choices=sorted(HASHERS), default="phash", help="Hash method to compute; default: phash.")
    parser.add_argument("--mode", choices=("auto", "whole", "tiles"), default="auto", help="auto hashes eight tiles when geometry matches, otherwise the whole image.")
    parser.add_argument("--self-test", action="store_true", help="Verify all methods produce stable 8-byte vectors on synthetic inputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.self_test or args.image):
        parser.error("provide --self-test or --image")
    try:
        if args.self_test:
            run_self_test()
        if args.image:
            img = read_image(args.image)
            fn = HASHERS[args.method]
            for name, row, col, item in selected_items(img, args.mode):
                digest = packed_hex(fn(item))
                if row is None:
                    print(f"{name}\tmethod={args.method}\thex={digest}")
                else:
                    print(f"{name}\trow={row}\tcol={col}\tmethod={args.method}\thex={digest}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
