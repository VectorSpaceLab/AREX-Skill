#!/usr/bin/env python3
"""Safely pre-resize large face.evoLVe identity-folder images before alignment.

Adapted from face.evoLVe's resize-before-align helper with explicit roots,
deterministic traversal, no hard-coded destination path, and no source deletion.
The script writes a separate identity-folder tree and normalizes outputs to .jpg.
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

try:  # tqdm is useful but not required for help/parser usability.
    from tqdm import tqdm
except Exception:  # pragma: no cover - fallback for minimal environments.
    def tqdm(iterable: Iterable, **_: object) -> Iterable:
        return iterable

LOGGER = logging.getLogger("face_evolve_resize_faces")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a resized identity-folder tree before face.evoLVe MTCNN "
            "alignment. Large images are resized and padded to a square."
        )
    )
    parser.add_argument(
        "--source-root",
        "-source_root",
        required=True,
        type=Path,
        help="Identity-folder input root: source_root/<identity>/<image>.",
    )
    parser.add_argument(
        "--dest-root",
        "-dest_root",
        required=True,
        type=Path,
        help="Separate output root to create with the same identity folders.",
    )
    parser.add_argument(
        "--min-side",
        default=512,
        type=int,
        help=(
            "Threshold and target square edge for oversized images. Images with "
            "larger side <= this value are copied through as .jpg; default: 512."
        ),
    )
    return parser.parse_args(argv)


def resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def roots_overlap(a: Path, b: Path) -> bool:
    return a == b or is_within(a, b) or is_within(b, a)


def visible_children(path: Path) -> list[Path]:
    return [p for p in sorted(path.iterdir(), key=lambda item: item.name) if not p.name.startswith(".")]


def validate_roots(source_root: Path, dest_root: Path) -> tuple[Path, Path]:
    source_root = resolve_path(source_root)
    dest_root = resolve_path(dest_root)
    if not source_root.is_dir():
        raise SystemExit(f"--source-root is not a directory: {source_root}")
    if dest_root.exists() and not dest_root.is_dir():
        raise SystemExit(f"--dest-root exists but is not a directory: {dest_root}")
    if roots_overlap(source_root, dest_root):
        raise SystemExit(
            "--dest-root must be separate from --source-root; overlapping roots can "
            "cause recursive processing or overwrites."
        )
    return source_root, dest_root


def output_name_for(input_path: Path) -> str:
    return f"{input_path.stem}.jpg"


def resize_if_large(image, min_side: int, cv2_module):
    height, width = image.shape[:2]
    if max(width, height) <= min_side:
        return image, False

    scale = max(width, height) / float(min_side)
    new_width = max(1, int(round(width / scale)))
    new_height = max(1, int(round(height / scale)))
    resized = cv2_module.resize(image, (new_width, new_height))

    pad_top = max(0, (min_side - new_height) // 2)
    pad_bottom = max(0, min_side - new_height - pad_top)
    pad_left = max(0, (min_side - new_width) // 2)
    pad_right = max(0, min_side - new_width - pad_left)
    padded = cv2_module.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2_module.BORDER_CONSTANT,
        value=[0, 0, 0],
    )
    return padded, True


def resize_one_image(source_path: Path, dest_path: Path, *, min_side: int, cv2_module) -> str:
    image = cv2_module.imread(str(source_path), cv2_module.IMREAD_COLOR)
    if image is None:
        LOGGER.warning("Skipping unreadable image %s", source_path)
        return "read_error"

    output, resized = resize_if_large(image, min_side, cv2_module)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2_module.imwrite(str(dest_path), output):
        LOGGER.warning("Failed to write %s", dest_path)
        return "write_error"
    return "resized" if resized else "copied_as_jpg"


def resize_tree(args: argparse.Namespace) -> Counter:
    if args.min_side <= 0:
        raise SystemExit("--min-side must be a positive integer")
    try:
        import cv2
    except Exception as exc:  # pragma: no cover - depends on runtime environment.
        raise SystemExit("OpenCV is required: install/import cv2 before resizing faces") from exc

    source_root, dest_root = validate_roots(args.source_root, args.dest_root)
    identity_dirs = [p for p in visible_children(source_root) if p.is_dir()]
    if not identity_dirs:
        raise SystemExit(
            "No visible identity subdirectories were found under --source-root; "
            "expected source_root/<identity>/<image>."
        )

    dest_root.mkdir(parents=True, exist_ok=True)
    stats: Counter = Counter()
    written_outputs: set[Path] = set()

    for identity_dir in tqdm(identity_dirs, desc="identities"):
        dest_identity = dest_root / identity_dir.name
        dest_identity.mkdir(parents=True, exist_ok=True)
        for image_path in visible_children(identity_dir):
            if not image_path.is_file():
                stats["skipped_non_file"] += 1
                continue
            output_path = dest_identity / output_name_for(image_path)
            if output_path in written_outputs:
                LOGGER.warning(
                    "Skipping %s: output name collision after .jpg normalization (%s)",
                    image_path,
                    output_path,
                )
                stats["output_collision"] += 1
                continue
            status = resize_one_image(
                image_path,
                output_path,
                min_side=int(args.min_side),
                cv2_module=cv2,
            )
            stats[status] += 1
            if status in {"resized", "copied_as_jpg"}:
                written_outputs.add(output_path)

    return stats


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args(argv)
    stats = resize_tree(args)
    LOGGER.info("Resize summary: %s", dict(sorted(stats.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
