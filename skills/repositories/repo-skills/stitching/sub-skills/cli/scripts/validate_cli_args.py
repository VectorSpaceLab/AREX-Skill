#!/usr/bin/env python3
"""Validate stitching CLI arguments without running a panorama stitch.

This helper parses the public `stitch` arguments, expands image and mask glob
patterns, and checks that the feature-mask count matches the image count.

Example:
  python scripts/validate_cli_args.py -- stitch img*.jpg --feature_masks mask1.png mask2.png
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional local checkout to prepend to sys.path before importing.",
    )
    parser.add_argument(
        "cli_argv",
        nargs=argparse.REMAINDER,
        help="Command tokens after an optional -- sentinel, e.g. `-- stitch img*.jpg ...`.",
    )
    return parser.parse_args()


def maybe_prepend_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    sys.path.insert(0, str(repo_root.resolve()))


def normalize_cli_argv(cli_argv: list[str]) -> list[str]:
    if cli_argv[:1] == ["--"]:
        cli_argv = cli_argv[1:]
    if cli_argv[:1] == ["stitch"]:
        cli_argv = cli_argv[1:]
    return cli_argv


def expand_paths(patterns: list[str]) -> list[str]:
    expanded: list[str] = []
    for pattern in patterns:
        matches = [path for path in glob.glob(pattern) if not os.path.isdir(path)]
        if matches:
            expanded.extend(matches)
        else:
            expanded.append(pattern)
    return expanded


def main() -> int:
    args = parse_args()
    maybe_prepend_repo_root(args.repo_root)

    try:
        from stitching.cli.stitch import create_parser
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1

    cli_argv = normalize_cli_argv(args.cli_argv)
    if not cli_argv:
        print(json.dumps({"ok": False, "error": "No CLI arguments provided after optional -- stitch"}, indent=2))
        return 1

    parser = create_parser()
    parsed = parser.parse_args(cli_argv)
    images = expand_paths(parsed.images)
    feature_masks = expand_paths(parsed.feature_masks)

    errors: list[str] = []
    missing_images = [path for path in images if not os.path.exists(path)]
    missing_masks = [path for path in feature_masks if not os.path.exists(path)]
    if missing_images:
        errors.append(f"Missing image files: {missing_images}")
    if missing_masks:
        errors.append(f"Missing mask files: {missing_masks}")
    if feature_masks and len(feature_masks) != len(images):
        errors.append(
            f"Feature-mask count {len(feature_masks)} does not match image count {len(images)}"
        )

    report = {
        "ok": not errors,
        "parsed": {
            "images": parsed.images,
            "feature_masks": parsed.feature_masks,
            "output": parsed.output,
            "affine": parsed.affine,
            "verbose": parsed.verbose,
            "crop": parsed.crop,
        },
        "resolved": {
            "images": images,
            "feature_masks": feature_masks,
        },
        "errors": errors,
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
