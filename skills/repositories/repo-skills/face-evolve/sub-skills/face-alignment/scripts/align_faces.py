#!/usr/bin/env python3
"""Batch-align face.evoLVe identity folders with the MTCNN alignment path.

This bundled helper is adapted from face.evoLVe's alignment workflow but adds
explicit roots, deterministic traversal, safe output creation, and clear errors.
It requires --repo-root so it can use a local face.evoLVe checkout containing
applications/align/ and the MTCNN .npy weights. No downloads are attempted and
source inputs are never deleted.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Sequence, Tuple

import numpy as np
from PIL import Image

try:  # tqdm is useful but not essential for parser/help usability.
    from tqdm import tqdm
except Exception:  # pragma: no cover - fallback for minimal environments.
    def tqdm(iterable: Iterable, **_: object) -> Iterable:
        return iterable

LOGGER = logging.getLogger("face_evolve_align_faces")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Align source_root/<identity>/<image> with face.evoLVe MTCNN and "
            "write aligned .jpg crops under dest_root."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help=(
            "Local face.evoLVe checkout root containing applications/align/ "
            "and pnet.npy, rnet.npy, onet.npy."
        ),
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
        "--crop-size",
        "-crop_size",
        default=112,
        type=int,
        help="Square aligned crop edge in pixels; default: 112.",
    )
    parser.add_argument(
        "--min-face-size",
        default=20.0,
        type=float,
        help="MTCNN minimum face size in pixels; default: 20.0.",
    )
    parser.add_argument(
        "--thresholds",
        nargs=3,
        type=float,
        metavar=("P", "R", "O"),
        default=(0.6, 0.7, 0.8),
        help="PNet/RNet/ONet score thresholds; default: 0.6 0.7 0.8.",
    )
    parser.add_argument(
        "--nms-thresholds",
        nargs=3,
        type=float,
        metavar=("P", "R", "O"),
        default=(0.7, 0.7, 0.7),
        help="PNet/RNet/ONet NMS thresholds; default: 0.7 0.7 0.7.",
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


def validate_roots(repo_root: Path, source_root: Path, dest_root: Path) -> Tuple[Path, Path, Path, Path]:
    repo_root = resolve_path(repo_root)
    source_root = resolve_path(source_root)
    dest_root = resolve_path(dest_root)

    align_dir = repo_root / "applications" / "align"
    if not repo_root.is_dir():
        raise SystemExit(f"--repo-root is not a directory: {repo_root}")
    if not align_dir.is_dir():
        raise SystemExit(f"--repo-root does not contain applications/align/: {repo_root}")
    missing = [name for name in ("pnet.npy", "rnet.npy", "onet.npy") if not (align_dir / name).is_file()]
    if missing:
        raise SystemExit(
            "MTCNN weight files are missing under applications/align/: " + ", ".join(missing)
        )

    if not source_root.is_dir():
        raise SystemExit(f"--source-root is not a directory: {source_root}")
    if dest_root.exists() and not dest_root.is_dir():
        raise SystemExit(f"--dest-root exists but is not a directory: {dest_root}")
    if roots_overlap(source_root, dest_root):
        raise SystemExit(
            "--dest-root must be separate from --source-root; overlapping roots can "
            "cause recursive processing or overwrites."
        )
    return repo_root, source_root, dest_root, align_dir


@contextlib.contextmanager
def temporary_cwd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(str(previous))


def load_alignment_helpers(align_dir: Path):
    """Import legacy face.evoLVe alignment helpers from a validated checkout."""
    # Suppress known noisy compatibility warnings from the legacy PyTorch detector.
    warnings.filterwarnings("ignore", message="volatile was removed.*", category=UserWarning)
    warnings.filterwarnings("ignore", message="Implicit dimension choice for softmax.*", category=UserWarning)

    sys.path.insert(0, str(align_dir))
    try:
        from detector import detect_faces  # type: ignore
        from align_trans import get_reference_facial_points, warp_and_crop_face  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller checkout.
        raise SystemExit(
            "Failed to import face.evoLVe MTCNN helpers from applications/align/: "
            f"{exc}"
        ) from exc
    return detect_faces, get_reference_facial_points, warp_and_crop_face


def legacy_detect_faces(detect_faces, align_dir: Path, image: Image.Image, *, min_face_size: float,
                        thresholds: Sequence[float], nms_thresholds: Sequence[float]):
    """Run source detector with cwd fixed for .npy weights and normalize no-face errors."""
    try:
        with temporary_cwd(align_dir):
            return detect_faces(
                image,
                min_face_size=float(min_face_size),
                thresholds=list(thresholds),
                nms_thresholds=list(nms_thresholds),
            )
    except ValueError as exc:
        message = str(exc)
        if "at least one array" in message and "concatenate" in message:
            return [], []
        raise


def output_name_for(input_path: Path) -> str:
    return f"{input_path.stem}.jpg"


def align_one_image(
    source_path: Path,
    dest_path: Path,
    *,
    align_dir: Path,
    detect_faces,
    warp_and_crop_face,
    reference_points: np.ndarray,
    crop_size: int,
    min_face_size: float,
    thresholds: Sequence[float],
    nms_thresholds: Sequence[float],
) -> str:
    try:
        with Image.open(source_path) as opened:
            image = opened.convert("RGB")
    except Exception as exc:
        LOGGER.warning("Skipping unreadable image %s: %s", source_path, exc)
        return "read_error"

    try:
        _boxes, landmarks = legacy_detect_faces(
            detect_faces,
            align_dir,
            image,
            min_face_size=min_face_size,
            thresholds=thresholds,
            nms_thresholds=nms_thresholds,
        )
    except Exception as exc:
        LOGGER.warning("Skipping %s after detector error: %s", source_path, exc)
        return "detect_error"

    if len(landmarks) == 0:
        LOGGER.warning("Skipping %s: no landmarks detected", source_path)
        return "no_landmarks"
    if len(landmarks) > 1:
        LOGGER.info("%s produced %d faces; aligning the first returned landmark set", source_path, len(landmarks))

    first_landmarks = landmarks[0]
    facial5points = [[first_landmarks[j], first_landmarks[j + 5]] for j in range(5)]
    warped_face = warp_and_crop_face(
        np.asarray(image),
        facial5points,
        reference_points,
        crop_size=(crop_size, crop_size),
    )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(warped_face).save(dest_path)
    return "aligned"


def align_tree(args: argparse.Namespace) -> Counter:
    if args.crop_size <= 0:
        raise SystemExit("--crop-size must be a positive integer")
    if args.min_face_size <= 0:
        raise SystemExit("--min-face-size must be positive")

    _repo_root, source_root, dest_root, align_dir = validate_roots(
        args.repo_root, args.source_root, args.dest_root
    )
    identity_dirs = [p for p in visible_children(source_root) if p.is_dir()]
    if not identity_dirs:
        raise SystemExit(
            "No visible identity subdirectories were found under --source-root; "
            "expected source_root/<identity>/<image>."
        )

    detect_faces, get_reference_facial_points, warp_and_crop_face = load_alignment_helpers(align_dir)
    scale = float(args.crop_size) / 112.0
    reference_points = get_reference_facial_points(default_square=True) * scale

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
            status = align_one_image(
                image_path,
                output_path,
                align_dir=align_dir,
                detect_faces=detect_faces,
                warp_and_crop_face=warp_and_crop_face,
                reference_points=reference_points,
                crop_size=int(args.crop_size),
                min_face_size=float(args.min_face_size),
                thresholds=args.thresholds,
                nms_thresholds=args.nms_thresholds,
            )
            stats[status] += 1
            if status == "aligned":
                written_outputs.add(output_path)

    return stats


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args(argv)
    stats = align_tree(args)
    LOGGER.info("Alignment summary: %s", dict(sorted(stats.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
