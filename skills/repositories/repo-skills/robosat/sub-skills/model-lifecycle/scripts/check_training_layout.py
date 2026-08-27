#!/usr/bin/env python3
"""Validate a RoboSat training dataset layout.

The script checks the expected training/validation slippy-map directories,
verifies matching tile ids between images and labels, and optionally warns
about batch-size / drop-last risk for tiny splits.
"""

import argparse
import sys
from pathlib import Path


def format_tile(tile):
    z, x, y = tile
    return "{}/{}/{}".format(z, x, y)


def preview_tiles(tiles, limit=5):
    rendered = [format_tile(tile) for tile in tiles[:limit]]
    if len(tiles) > limit:
        rendered.append("... (+{} more)".format(len(tiles) - limit))
    return ", ".join(rendered)


def collect_tiles(root):
    tiles = {}
    duplicates = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(root)
        if len(rel.parts) != 3:
            continue

        z, x, filename = rel.parts
        y = Path(filename).stem
        if not (z.isdigit() and x.isdigit() and y.isdigit()):
            continue

        tile = (int(z), int(x), int(y))
        if tile in tiles:
            duplicates.append((tile, tiles[tile], path))
        else:
            tiles[tile] = path

    return tiles, duplicates


def validate_split(root, split_name, batch_size=None, drop_last=False):
    errors = []
    warnings = []

    images_dir = root / split_name / "images"
    labels_dir = root / split_name / "labels"

    if not images_dir.is_dir():
        errors.append("{}: missing images directory {}".format(split_name, images_dir))
    if not labels_dir.is_dir():
        errors.append("{}: missing labels directory {}".format(split_name, labels_dir))

    if errors:
        return errors, warnings

    image_tiles, image_dupes = collect_tiles(images_dir)
    label_tiles, label_dupes = collect_tiles(labels_dir)

    if image_dupes:
        tile, first, second = image_dupes[0]
        errors.append(
            "{}: duplicate image tile {} in {} and {}".format(split_name, format_tile(tile), first, second)
        )
    if label_dupes:
        tile, first, second = label_dupes[0]
        errors.append(
            "{}: duplicate label tile {} in {} and {}".format(split_name, format_tile(tile), first, second)
        )

    if not image_tiles:
        errors.append("{}: no image tiles found under {}".format(split_name, images_dir))
    if not label_tiles:
        errors.append("{}: no label tiles found under {}".format(split_name, labels_dir))

    if errors:
        return errors, warnings

    image_ids = set(image_tiles)
    label_ids = set(label_tiles)
    missing_labels = sorted(image_ids - label_ids)
    missing_images = sorted(label_ids - image_ids)

    if missing_labels:
        errors.append(
            "{}: missing labels for {}".format(split_name, preview_tiles(missing_labels))
        )
    if missing_images:
        errors.append(
            "{}: missing images for {}".format(split_name, preview_tiles(missing_images))
        )

    if errors:
        return errors, warnings

    count = len(image_tiles)
    print("OK {}: {} image tiles, {} label tiles, {} matched tiles".format(split_name, count, len(label_tiles), count))

    if batch_size is not None and batch_size > 0 and drop_last:
        remainder = count % batch_size
        if count < batch_size:
            warnings.append(
                "{}: batch size {} is larger than the split size {}; drop_last would yield zero batches".format(
                    split_name, batch_size, count
                )
            )
        elif remainder:
            warnings.append(
                "{}: batch size {} with drop_last would drop {} tile(s) from the final batch".format(
                    split_name, batch_size, remainder
                )
            )

    return errors, warnings


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate a RoboSat training dataset layout before launching rs train."
    )
    parser.add_argument("dataset_root", help="dataset root containing training/ and validation/")
    parser.add_argument("--batch-size", type=int, default=None, help="optional batch size for drop-last risk checks")
    parser.add_argument(
        "--drop-last",
        action="store_true",
        help="check the same drop_last risk that RoboSat training uses",
    )
    parser.add_argument(
        "--strict-batch-risk",
        action="store_true",
        help="treat batch-size / drop-last warnings as errors",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.dataset_root)
    if not root.is_dir():
        parser.error("dataset_root must point to an existing directory")

    overall_errors = []
    overall_warnings = []

    for split_name in ("training", "validation"):
        errors, warnings = validate_split(root, split_name, batch_size=args.batch_size, drop_last=args.drop_last)
        overall_errors.extend(errors)
        overall_warnings.extend(warnings)

    for warning in overall_warnings:
        print("WARN: {}".format(warning), file=sys.stderr)

    for error in overall_errors:
        print("ERROR: {}".format(error), file=sys.stderr)

    if overall_errors:
        return 1

    if args.strict_batch_risk and overall_warnings:
        return 1

    if args.batch_size is not None and not args.drop_last:
        print("INFO: batch-size provided without --drop-last; batch-risk check skipped", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
