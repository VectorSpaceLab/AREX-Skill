#!/usr/bin/env python3
"""Tile nested UAVid ``<sequence>/{Images,Labels}`` data safely.

Images and labels are paired by exact filename stem, not directory order.
Each pair is bottom/right padded to a tile boundary (image fill 0, label
boundary/ignore 255) and full tiles are emitted in deterministic sequence,
image, row, column order.  The generalized padding also handles non-square
source images and non-square ``--split-size-h/w`` values.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

COLORS = {
    (128, 0, 0): 0, (128, 64, 128): 1, (0, 128, 0): 2,
    (128, 128, 0): 3, (64, 0, 128): 4, (192, 0, 192): 5,
    (64, 64, 0): 6, (0, 0, 0): 7, (255, 255, 255): 255,
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True, help="Directory containing sequence subdirectories")
    p.add_argument("--output-img-dir", required=True)
    p.add_argument("--output-mask-dir", required=True)
    p.add_argument("--mode", choices=("train", "val", "test"), default="train")
    p.add_argument("--split-size-h", type=int, default=1024)
    p.add_argument("--split-size-w", type=int, default=1024)
    p.add_argument("--stride-h", type=int, default=1024)
    p.add_argument("--stride-w", type=int, default=1024)
    p.add_argument("--overwrite", action="store_true")
    return p


def label_array(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        values = set(np.unique(array).tolist())
        if not values.issubset(set(range(8)) | {255}):
            raise ValueError("indexed UAVid labels outside 0..7/255: {}".format(sorted(values)))
        return array.astype(np.uint8)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("UAVid labels must be RGB or single-channel PNGs")
    out = np.full(array.shape[:2], 254, dtype=np.uint8)
    for color, label in COLORS.items():
        out[np.all(array == color, axis=2)] = label
    if np.any(out == 254):
        unknown = np.unique(array[out == 254].reshape(-1, 3), axis=0)
        raise ValueError("unsupported UAVid label colors (first few): {}".format(unknown[:5].tolist()))
    return out


def atomic_save(array: np.ndarray, path: Path, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError("refusing to overwrite: {} (use --overwrite)".format(path))
    fd, tmp = tempfile.mkstemp(prefix=".geoseg-", suffix=".png", dir=str(path.parent))
    os.close(fd)
    temporary = Path(tmp)
    try:
        Image.fromarray(array).save(str(temporary), format="PNG")
        os.replace(str(temporary), str(path))
    finally:
        temporary.unlink(missing_ok=True)


def sequence_pairs(sequence: Path):
    image_dir, label_dir = sequence / "Images", sequence / "Labels"
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise ValueError("sequence {} must contain Images/ and Labels/".format(sequence.name))
    images = {p.stem: p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"}
    labels = {p.stem: p for p in label_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"}
    missing_labels = sorted(set(images) - set(labels))
    missing_images = sorted(set(labels) - set(images))
    if missing_labels or missing_images:
        raise ValueError("UAVid stem mismatch in {} (missing labels: {}; missing images: {})".format(
            sequence.name, missing_labels[:8], missing_images[:8]))
    return [(images[stem], labels[stem], stem) for stem in sorted(images)]


def pad_pair(image: np.ndarray, mask: np.ndarray, tile_h: int, tile_w: int):
    h, w = image.shape[:2]
    target_h = max(tile_h, int(np.ceil(h / tile_h)) * tile_h)
    target_w = max(tile_w, int(np.ceil(w / tile_w)) * tile_w)
    image_out = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    mask_out = np.full((target_h, target_w), 255, dtype=np.uint8)
    image_out[:h, :w] = image
    mask_out[:h, :w] = mask
    return image_out, mask_out


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    values = (args.split_size_h, args.split_size_w, args.stride_h, args.stride_w)
    if any(value <= 0 for value in values):
        raise SystemExit("tile sizes and strides must be positive")
    input_dir = Path(args.input_dir).expanduser()
    if not input_dir.is_dir():
        raise SystemExit("input directory does not exist: {}".format(input_dir))
    sequences = sorted(p for p in input_dir.iterdir() if p.is_dir())
    if not sequences:
        raise SystemExit("no sequence directories found in {}".format(input_dir))
    work = [(sequence, pair) for sequence in sequences for pair in sequence_pairs(sequence)]
    out_img, out_mask = Path(args.output_img_dir).expanduser(), Path(args.output_mask_dir).expanduser()
    count = 0
    for sequence, (image_path, mask_path, stem) in work:
        with Image.open(image_path) as image_file, Image.open(mask_path) as mask_file:
            image = np.asarray(image_file.convert("RGB"))
            mask = label_array(np.asarray(mask_file))
        if image.shape[:2] != mask.shape[:2]:
            raise ValueError("shape mismatch for {}/{}: image {}, mask {}".format(
                sequence.name, stem, image.shape, mask.shape))
        image, mask = pad_pair(image, mask, args.split_size_h, args.split_size_w)
        tile_index = 0
        for y in range(0, image.shape[0], args.stride_h):
            for x in range(0, image.shape[1], args.stride_w):
                image_tile = image[y:y + args.split_size_h, x:x + args.split_size_w]
                mask_tile = mask[y:y + args.split_size_h, x:x + args.split_size_w]
                if image_tile.shape[:2] != (args.split_size_h, args.split_size_w):
                    tile_index += 1
                    continue
                filename = "{}_{}_{}_{}.png".format(sequence.name, stem, args.mode, tile_index)
                atomic_save(image_tile, out_img / filename, args.overwrite)
                atomic_save(mask_tile, out_mask / filename, args.overwrite)
                tile_index += 1
                count += 1
    print("split {} UAVid pairs into {} patches under {}".format(len(work), count, out_img))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
