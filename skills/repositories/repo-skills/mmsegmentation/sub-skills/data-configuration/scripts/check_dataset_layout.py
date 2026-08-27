#!/usr/bin/env python3
"""Check MMSegmentation-style image and segmentation-map pairing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check dataset directory existence, suffix counts, and image/mask pairing.')
    parser.add_argument('--data-root', default='.', help='Dataset root used by the config.')
    parser.add_argument('--img-path', required=True, help='Image directory relative to data-root, or absolute path.')
    parser.add_argument('--seg-map-path', default=None, help='Mask directory relative to data-root, or absolute path.')
    parser.add_argument('--ann-file', default=None, help='Optional split file relative to data-root, or absolute path.')
    parser.add_argument('--img-suffix', default='.jpg', help='Full image suffix, including extension.')
    parser.add_argument('--seg-map-suffix', default='.png', help='Full segmentation-map suffix, including extension.')
    parser.add_argument('--recursive', action='store_true', help='Search image and mask directories recursively.')
    parser.add_argument('--sample-size', type=int, default=10, help='Number of expected pairs to print.')
    parser.add_argument('--reduce-zero-label', action='store_true', help='Print notes for configs that set reduce_zero_label=True.')
    parser.add_argument('--ignore-index', type=int, default=255, help='Configured ignore_index value.')
    return parser.parse_args()


def resolve(data_root: Path, path_text: Optional[str]) -> Optional[Path]:
    if path_text is None:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return data_root / path


def list_by_suffix(root: Path, suffix: str, recursive: bool) -> List[Path]:
    pattern = '**/*' if recursive else '*'
    return sorted(path for path in root.glob(pattern) if path.is_file() and str(path.name).endswith(suffix))


def strip_suffix(text: str, suffix: str) -> str:
    if suffix and text.endswith(suffix):
        return text[:-len(suffix)]
    return text


def read_split(ann_file: Path) -> List[str]:
    lines = []
    for line in ann_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def expected_from_split(stems: Iterable[str], img_suffix: str, seg_suffix: str) -> List[Tuple[Path, Path]]:
    return [(Path(stem + img_suffix), Path(stem + seg_suffix)) for stem in stems]


def expected_from_images(img_dir: Path, images: Iterable[Path], img_suffix: str, seg_suffix: str) -> List[Tuple[Path, Path]]:
    pairs = []
    for image in images:
        rel_image = image.relative_to(img_dir)
        rel_text = rel_image.as_posix()
        stem_text = strip_suffix(rel_text, img_suffix)
        pairs.append((Path(rel_text), Path(stem_text + seg_suffix)))
    return pairs


def print_note(args: argparse.Namespace) -> None:
    if args.reduce_zero_label:
        print('Label note: reduce_zero_label=True maps original label 0 to ignore_index, then shifts remaining labels down by one.')
    else:
        print('Label note: reduce_zero_label=False keeps class id 0 as a real class unless masks use ignore_index explicitly.')
    if args.ignore_index != 255:
        print(f'Label note: ignore_index={args.ignore_index}; confirm losses, evaluator, and masks all use this value.')
    else:
        print('Label note: ignore_index=255, the MMSegmentation default.')


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    img_dir = resolve(data_root, args.img_path)
    seg_dir = resolve(data_root, args.seg_map_path)
    ann_file = resolve(data_root, args.ann_file)

    print('Dataset layout check')
    print(f'data_root: {data_root}')
    print(f'img_path: {img_dir}')
    if seg_dir is not None:
        print(f'seg_map_path: {seg_dir}')
    if ann_file is not None:
        print(f'ann_file: {ann_file}')
    print(f'img_suffix: {args.img_suffix}')
    print(f'seg_map_suffix: {args.seg_map_suffix}')
    print(f'recursive: {args.recursive}')

    errors = []
    if img_dir is None or not img_dir.is_dir():
        errors.append(f'image directory missing: {img_dir}')
    if seg_dir is not None and not seg_dir.is_dir():
        errors.append(f'segmentation-map directory missing: {seg_dir}')
    if ann_file is not None and not ann_file.is_file():
        errors.append(f'annotation split file missing: {ann_file}')

    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        print_note(args)
        return 1

    images = list_by_suffix(img_dir, args.img_suffix, args.recursive)
    print(f'image files matching suffix: {len(images)}')
    if len(images) == 0:
        print('ERROR: no image files matched the configured suffix', file=sys.stderr)
        print_note(args)
        return 1

    if seg_dir is None:
        print('No seg_map_path supplied; this is only suitable for unlabeled test/inference layouts.')
        print('Sample images:')
        for image in images[:max(args.sample_size, 0)]:
            print(f'- {image.relative_to(img_dir).as_posix()}')
        print_note(args)
        return 0

    masks = list_by_suffix(seg_dir, args.seg_map_suffix, args.recursive)
    print(f'segmentation-map files matching suffix: {len(masks)}')

    if ann_file is not None:
        stems = read_split(ann_file)
        print(f'ann_file entries: {len(stems)}')
        expected_pairs = expected_from_split(stems, args.img_suffix, args.seg_map_suffix)
    else:
        expected_pairs = expected_from_images(img_dir, images, args.img_suffix, args.seg_map_suffix)

    missing_images = []
    missing_masks = []
    ok_pairs = []
    for rel_image, rel_mask in expected_pairs:
        image_path = img_dir / rel_image
        mask_path = seg_dir / rel_mask
        image_exists = image_path.is_file()
        mask_exists = mask_path.is_file()
        if image_exists and mask_exists:
            ok_pairs.append((rel_image, rel_mask))
        if not image_exists:
            missing_images.append(rel_image)
        if not mask_exists:
            missing_masks.append(rel_mask)

    print(f'expected pairs: {len(expected_pairs)}')
    print(f'paired files found: {len(ok_pairs)}')
    print(f'missing images: {len(missing_images)}')
    print(f'missing segmentation maps: {len(missing_masks)}')

    sample_size = max(args.sample_size, 0)
    if sample_size:
        print('Pairing sample:')
        for rel_image, rel_mask in expected_pairs[:sample_size]:
            status = 'OK' if (img_dir / rel_image).is_file() and (seg_dir / rel_mask).is_file() else 'MISSING'
            print(f'- {status}: {rel_image.as_posix()} -> {rel_mask.as_posix()}')

    extra_masks = set(mask.relative_to(seg_dir).as_posix() for mask in masks)
    expected_masks = set(rel_mask.as_posix() for _, rel_mask in expected_pairs)
    unused_masks = sorted(extra_masks - expected_masks)
    if unused_masks:
        print(f'unused segmentation maps with configured suffix: {len(unused_masks)}')
        for rel_mask in unused_masks[:sample_size]:
            print(f'- unused: {rel_mask}')

    print_note(args)

    if missing_images or missing_masks:
        print('ERROR: layout does not match configured pairing rules', file=sys.stderr)
        return 1
    print('OK: layout matches configured pairing rules')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
