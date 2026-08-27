#!/usr/bin/env python3
"""Validate RoboSat Slippy Map directories and optional tile CSV files."""

import argparse
import csv
from collections import Counter
from pathlib import Path
import sys

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None

try:
    import mercantile
except Exception:  # pragma: no cover - optional dependency
    mercantile = None


def format_tile(tile):
    """Render a tile as z/x/y for messages."""

    x, y, z = tile
    return "{}/{}/{}".format(z, x, y)


def short_samples(items, limit=5):
    """Return a compact comma-separated sample list."""

    values = sorted(items)
    samples = [format_tile(tile) for tile in values[:limit]]
    if len(values) > limit:
        samples.append("...")
    return ", ".join(samples)


def load_csv_tiles(csv_path):
    """Read a tile CSV in x,y,z order."""

    tiles = set()
    issues = []

    try:
        fp = csv_path.open(newline="")
    except OSError as exc:
        return tiles, ["{}: unable to read CSV ({})".format(csv_path, exc)]

    with fp:
        reader = csv.reader(fp)
        for line_no, row in enumerate(reader, 1):
            if not row or all(not cell.strip() for cell in row):
                continue

            if len(row) != 3:
                issues.append(
                    "{}:{}: expected 3 columns in x,y,z order, got {!r}".format(csv_path, line_no, row)
                )
                continue

            try:
                x, y, z = (int(value) for value in row)
            except ValueError:
                issues.append("{}:{}: non-integer tile row {!r}".format(csv_path, line_no, row))
                continue

            tiles.add((x, y, z))

    if not tiles:
        issues.append("{}: no valid tile rows found".format(csv_path))

    return tiles, issues


def collect_slippy_tiles(root):
    """Collect and validate the z/x/y.* tree."""

    issues = []
    tiles = {}
    zoom_counts = Counter()

    if not root.exists():
        return tiles, ["{}: root directory does not exist".format(root)], zoom_counts

    if not root.is_dir():
        return tiles, ["{}: expected a directory root".format(root)], zoom_counts

    for z_dir in sorted(root.iterdir(), key=lambda path: path.name):
        if not z_dir.is_dir():
            issues.append("{}: unexpected file at the root level".format(z_dir.name))
            continue

        if not z_dir.name.isdigit():
            issues.append("{}: zoom directory name must be numeric".format(z_dir))
            continue

        for x_dir in sorted(z_dir.iterdir(), key=lambda path: path.name):
            if not x_dir.is_dir():
                issues.append("{}: unexpected file inside zoom directory".format(x_dir))
                continue

            if not x_dir.name.isdigit():
                issues.append("{}: x directory name must be numeric".format(x_dir))
                continue

            for entry in sorted(x_dir.iterdir(), key=lambda path: path.name):
                if entry.is_dir():
                    issues.append("{}: unexpected nested directory inside a tile column".format(entry))
                    continue

                stem = entry.stem
                if not stem.isdigit():
                    issues.append("{}: tile filename stem must be numeric".format(entry))
                    continue

                tile = (int(x_dir.name), int(stem), int(z_dir.name))
                if tile in tiles:
                    issues.append(
                        "{}: duplicate tile {}; already seen at {}".format(entry, format_tile(tile), tiles[tile])
                    )
                    continue

                tiles[tile] = entry
                zoom_counts[tile[2]] += 1

    if not tiles:
        issues.append("{}: no tile files found under the Slippy Map root".format(root))

    return tiles, issues, zoom_counts


def verify_images(tiles):
    """Verify that files can be opened as images when Pillow is present."""

    issues = []

    if Image is None:
        issues.append("WARN: Pillow is unavailable; image payload checks were skipped")
        return issues

    for tile, path in sorted(tiles.items()):
        try:
            with Image.open(str(path)) as image:
                image.verify()
        except Exception as exc:
            issues.append("{}: unreadable image {} ({})".format(path, format_tile(tile), exc))

    return issues


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate RoboSat Slippy Map directories and optional tile CSV files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("root", help="root directory of a z/x/y.* Slippy Map tree")
    parser.add_argument("--tiles-csv", dest="tiles_csv", help="optional x,y,z CSV to compare against the tree")
    parser.add_argument(
        "--skip-image-check",
        action="store_true",
        help="skip optional Pillow-based image verification even if Pillow is available",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.root)
    all_issues = []

    tiles, issues, zoom_counts = collect_slippy_tiles(root)
    all_issues.extend(issues)

    if tiles and not args.skip_image_check:
        all_issues.extend(verify_images(tiles))
    elif Image is None and not args.skip_image_check:
        # The warning is already useful, but keep it separate from hard failures.
        pass

    if tiles:
        print("OK: {} tile files discovered".format(len(tiles)))
        for zoom in sorted(zoom_counts):
            print("OK: zoom {} -> {} tiles".format(zoom, zoom_counts[zoom]))

    if args.tiles_csv:
        csv_path = Path(args.tiles_csv)
        csv_tiles, csv_issues = load_csv_tiles(csv_path)
        all_issues.extend(csv_issues)

        csv_failed = bool(csv_issues)
        if not csv_failed:
            disk_tiles = set(tiles.keys())
            missing = csv_tiles - disk_tiles
            extra = disk_tiles - csv_tiles

            if missing:
                all_issues.append(
                    "{}: {} tiles listed in the CSV are missing on disk; examples: {}".format(
                        csv_path, len(missing), short_samples(missing)
                    )
                )

            if extra:
                all_issues.append(
                    "{}: {} tiles exist on disk but are missing from the CSV; examples: {}".format(
                        csv_path, len(extra), short_samples(extra)
                    )
                )

            if not missing and not extra and csv_tiles:
                print("OK: CSV tile list matches the on-disk tree")

    hard_failures = [issue for issue in all_issues if not issue.startswith("WARN:")]
    warnings = [issue for issue in all_issues if issue.startswith("WARN:")]

    for warning in warnings:
        print(warning, file=sys.stderr)

    for issue in hard_failures:
        print("ERROR: {}".format(issue), file=sys.stderr)

    if hard_failures:
        return 1

    if not tiles:
        print("ERROR: no tile files were discovered", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
