#!/usr/bin/env python3
"""Deterministically tile ISPRS Potsdam images and label masks.

The official layout uses ``<tile>_RGB.tif`` or ``<tile>_IRRG.tif`` and
``<tile>_label.tif`` (or ``_label_noBoundary.tif``).  This keeps GeoSeg's
flags and naming while validating pairs before writing.  Train mode emits
source, horizontal-flip, and vertical-flip variants; other modes emit one.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

COLORS = {
    (255, 255, 255): 0, (255, 0, 0): 1, (255, 255, 0): 2,
    (0, 255, 0): 3, (0, 255, 255): 4, (0, 0, 255): 5, (0, 0, 0): 6,
}
GT_PALETTE = np.asarray(
    [[255, 255, 255], [255, 0, 0], [255, 255, 0], [0, 255, 0],
     [0, 204, 255], [0, 0, 255], [0, 0, 0]], dtype=np.uint8
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--img-dir", required=True)
    p.add_argument("--mask-dir", required=True)
    p.add_argument("--output-img-dir", required=True)
    p.add_argument("--output-mask-dir", required=True)
    p.add_argument("--eroded", action="store_true", help="Use <tile>_label_noBoundary.tif")
    p.add_argument("--gt", action="store_true", help="Write RGB visualization masks")
    p.add_argument("--rgb-image", action="store_true", help="Use _RGB.tif instead of _IRRG.tif")
    p.add_argument("--mode", choices=("train", "val", "test"), default="train")
    p.add_argument("--val-scale", type=float, default=1.0, help="Scale validation/test pairs")
    p.add_argument("--split-size", type=int, default=1024)
    p.add_argument("--stride", type=int, default=1024)
    p.add_argument("--overwrite", action="store_true")
    return p


def labels_from_mask(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        values = set(np.unique(array).tolist())
        if not values.issubset(set(range(7))):
            raise ValueError("indexed Potsdam mask contains labels outside 0..6: {}".format(sorted(values)))
        return array.astype(np.uint8)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("Potsdam masks must be RGB or single-channel TIFFs")
    out = np.full(array.shape[:2], 255, dtype=np.uint8)
    for color, label in COLORS.items():
        out[np.all(array == color, axis=2)] = label
    if np.any(out == 255):
        unknown = np.unique(array[out == 255].reshape(-1, 3), axis=0)
        raise ValueError("unsupported Potsdam mask colors (first few): {}".format(unknown[:5].tolist()))
    return out


def labels_to_rgb(labels: np.ndarray) -> np.ndarray:
    rgb = np.zeros(labels.shape + (3,), dtype=np.uint8)
    for label, color in enumerate(GT_PALETTE):
        rgb[labels == label] = color
    return rgb


def atomic_save(array: np.ndarray, path: Path, fmt: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError("refusing to overwrite: {} (use --overwrite)".format(path))
    fd, tmp = tempfile.mkstemp(prefix=".geoseg-", suffix=path.suffix, dir=str(path.parent))
    os.close(fd)
    temporary = Path(tmp)
    try:
        Image.fromarray(array).save(str(temporary), format=fmt)
        os.replace(str(temporary), str(path))
    finally:
        temporary.unlink(missing_ok=True)


def resize_pair(image: np.ndarray, mask: np.ndarray, scale: float):
    if scale <= 0:
        raise ValueError("--val-scale must be positive")
    if scale == 1.0:
        return image, mask
    h, w = image.shape[:2]
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    resampling = getattr(Image, "Resampling", Image)
    return (np.asarray(Image.fromarray(image).resize(size, resampling.BICUBIC)),
            np.asarray(Image.fromarray(mask).resize(size, resampling.NEAREST)))


def padded(image: np.ndarray, mask: np.ndarray, patch: int):
    h, w = image.shape[:2]
    hp, wp = (patch - h % patch) % patch, (patch - w % patch) % patch
    if hp or wp:
        image = np.pad(image, ((0, hp), (0, wp), (0, 0)), constant_values=0)
        mask = np.pad(mask, ((0, hp), (0, wp)), constant_values=6)
    return image, mask


def pairs(img_dir: Path, mask_dir: Path, rgb: bool, eroded: bool):
    suffix = "_RGB.tif" if rgb else "_IRRG.tif"
    images = sorted(p for p in img_dir.iterdir() if p.is_file() and p.name.endswith(suffix))
    if not images:
        raise ValueError("no {} images found in {}".format(suffix, img_dir))
    result, missing = [], []
    mask_suffix = "_label_noBoundary.tif" if eroded else "_label.tif"
    for image in images:
        stem = image.name[:-len(suffix)]
        mask = mask_dir / (stem + mask_suffix)
        if not mask.is_file():
            missing.append(mask.name)
        else:
            result.append((image, mask, stem))
    if missing:
        raise ValueError("missing paired Potsdam masks: {}".format(", ".join(missing[:8])))
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.split_size <= 0 or args.stride <= 0:
        raise SystemExit("--split-size and --stride must be positive")
    img_dir, mask_dir = Path(args.img_dir).expanduser(), Path(args.mask_dir).expanduser()
    if not img_dir.is_dir() or not mask_dir.is_dir():
        raise SystemExit("--img-dir and --mask-dir must be existing directories")
    work = pairs(img_dir, mask_dir, args.rgb_image, args.eroded)
    out_img, out_mask = Path(args.output_img_dir).expanduser(), Path(args.output_mask_dir).expanduser()
    for image_path, mask_path, stem in work:
        with Image.open(image_path) as image_file, Image.open(mask_path) as mask_file:
            image = np.asarray(image_file.convert("RGB"))
            mask = labels_from_mask(np.asarray(mask_file))
        if image.shape[:2] != mask.shape[:2]:
            raise ValueError("shape mismatch for {}: image {}, mask {}".format(image_path.name, image.shape, mask.shape))
        image, mask = resize_pair(image, mask, args.val_scale if args.mode != "train" else 1.0)
        image, mask = padded(image, mask, args.split_size)
        variants, masks = [image], [mask]
        if args.mode == "train":
            variants += [image[:, ::-1].copy(), image[::-1, :].copy()]
            masks += [mask[:, ::-1].copy(), mask[::-1, :].copy()]
        if args.gt:
            atomic_save(labels_to_rgb(mask), out_mask / "origin" / (stem + ".tif"), "TIFF", args.overwrite)
        for variant_id, (variant, variant_mask) in enumerate(zip(variants, masks)):
            tile_index = 0
            for y in range(0, variant.shape[0], args.stride):
                for x in range(0, variant.shape[1], args.stride):
                    im = variant[y:y + args.split_size, x:x + args.split_size]
                    ma = variant_mask[y:y + args.split_size, x:x + args.split_size]
                    if im.shape[:2] != (args.split_size, args.split_size):
                        tile_index += 1
                        continue
                    tile_stem = "{}_{}_{}".format(stem, variant_id, tile_index)
                    atomic_save(im, out_img / (tile_stem + ".tif"), "TIFF", args.overwrite)
                    data = labels_to_rgb(ma) if args.gt else ma
                    atomic_save(data, out_mask / (tile_stem + (".tif" if args.gt else ".png")), "TIFF" if args.gt else "PNG", args.overwrite)
                    tile_index += 1
    print("split {} Potsdam image/mask pairs into {}".format(len(work), out_img))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
