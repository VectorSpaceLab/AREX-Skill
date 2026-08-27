#!/usr/bin/env python3
"""No-network, preflight-only contract checker for MobileSAMv2 inference.

This helper intentionally does not import torch, OpenCV, Matplotlib, the
ObjectAwareModel detector, or MobileSAMv2. It validates the local inputs that a
separate CUDA inference runner would need and never performs inference or
writes outputs.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


SOURCE_ENCODERS = (
    "tiny_vit",
    "sam_vit_h",
    "mobile_sam",
    "efficientvit_l2",
    "efficientvit_l1",
    "efficientvit_l0",
)
OPERATIONAL_ENCODERS = {
    "tiny_vit": "mobile_sam.pt",
    "sam_vit_h": "sam_vit_h.pt",
    "efficientvit_l2": "l2.pt",
}
CHECKPOINT_EXTENSIONS = {".pt", ".pth"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


class PreflightError(ValueError):
    """A user-correctable preflight failure."""


def parse_bool(value: str) -> bool:
    """Parse a predictable boolean instead of source ``type=bool`` semantics."""
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(
        f"expected true/false, yes/no, or 1/0; received {value!r}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate explicit local MobileSAMv2 object-aware inference inputs. "
            "This helper is always preflight-only: no model import, download, "
            "inference, or output write is performed."
        )
    )
    # Keep the source flag spellings and source defaults where they are safe to
    # expose. Required paths are an intentional adaptation documented in the
    # bundled CLI reference.
    parser.add_argument(
        "--ObjectAwareModel_path",
        required=True,
        help="local ObjectAwareModel detector checkpoint (source default: ./PromptGuidedDecoder/ObjectAwareModel.pt)",
    )
    parser.add_argument(
        "--Prompt_guided_Mask_Decoder_path",
        required=True,
        help="local prompt-guided decoder checkpoint (source default: ./PromptGuidedDecoder/Prompt_guided_Mask_Decoder.pt)",
    )
    parser.add_argument(
        "--encoder_path",
        required=True,
        help="local image-encoder checkpoint (source default: ./; explicit path required here)",
    )
    parser.add_argument(
        "--img_path",
        required=True,
        help="local image directory (source default: ./test_images/)",
    )
    parser.add_argument("--imgsz", type=int, default=1024, help="detector image size (default: 1024)")
    parser.add_argument("--iou", type=float, default=0.9, help="detector IoU threshold (default: 0.9)")
    parser.add_argument("--conf", type=float, default=0.4, help="detector confidence threshold (default: 0.4)")
    parser.add_argument(
        "--retina",
        type=parse_bool,
        default=True,
        metavar="BOOL",
        help="detector retina_masks value; adapted strict boolean (source default: True)",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="explicit local output directory (source default: ./; no files are written)",
    )
    parser.add_argument(
        "--encoder_type",
        required=True,
        choices=SOURCE_ENCODERS,
        help="source parser encoder name; only three mappings are operational",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="explicitly request the safe preflight pass (the helper always does this)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="alias for --preflight; no model import, inference, download, or write",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="allow existing output filenames in the report; never writes them",
    )
    return parser


def _local_path(raw: str, label: str) -> Path:
    value = raw.strip()
    if not value:
        raise PreflightError(f"{label} must not be empty")
    lowered = value.lower()
    if "://" in value or lowered.startswith(("http:", "https:", "ftp:", "file:")):
        raise PreflightError(f"{label} must be a local path, not a URL: {raw!r}")
    return Path(value).expanduser()


def _check_checkpoint(raw: str, label: str) -> Path:
    path = _local_path(raw, label)
    if path.suffix.lower() not in CHECKPOINT_EXTENSIONS:
        allowed = ", ".join(sorted(CHECKPOINT_EXTENSIONS))
        raise PreflightError(f"{label} must end in {allowed}: {path}")
    if not path.is_file():
        raise PreflightError(f"{label} does not exist as a local file: {path}")
    if not os.access(path, os.R_OK):
        raise PreflightError(f"{label} is not readable: {path}")
    try:
        if path.stat().st_size == 0:
            raise PreflightError(f"{label} is empty: {path}")
    except OSError as exc:
        raise PreflightError(f"cannot inspect {label}: {path}: {exc}") from exc
    return path


def _check_image_directory(raw: str) -> Tuple[Path, List[Path]]:
    directory = _local_path(raw, "--img_path")
    if not directory.is_dir():
        raise PreflightError(f"--img_path must be an existing local directory: {directory}")
    images = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        extensions = ", ".join(sorted(IMAGE_EXTENSIONS))
        raise PreflightError(
            f"--img_path contains no supported image files ({extensions}): {directory}"
        )
    unreadable = [path for path in images if not os.access(path, os.R_OK)]
    if unreadable:
        raise PreflightError(f"image file is not readable: {unreadable[0]}")
    return directory, images


def _check_output_directory(raw: str, input_dir: Path, images: Sequence[Path], allow_overwrite: bool) -> Tuple[Path, List[Path]]:
    output = _local_path(raw, "--output_dir")
    # Resolve without requiring the path to exist. This catches the dangerous
    # same-directory case while allowing a user to preflight a directory they
    # will create separately.
    input_resolved = input_dir.resolve()
    output_resolved = output.resolve()
    if (
        output_resolved == input_resolved
        or input_resolved in output_resolved.parents
        or output_resolved in input_resolved.parents
    ):
        raise PreflightError(
            "--output_dir must be a disjoint directory from --img_path "
            "to avoid input/output collisions"
        )

    if output.exists():
        if not output.is_dir():
            raise PreflightError(f"--output_dir exists but is not a directory: {output}")
        if not os.access(output, os.W_OK | os.X_OK):
            raise PreflightError(f"--output_dir is not writable: {output}")
    else:
        parent = output.parent
        if not parent.is_dir():
            raise PreflightError(
                f"--output_dir does not exist and its parent is missing: {output}"
            )
        if not os.access(parent, os.W_OK | os.X_OK):
            raise PreflightError(
                f"--output_dir does not exist and its parent is not writable: {parent}"
            )

    collisions = [output / image.name for image in images if (output / image.name).exists()]
    if collisions and not allow_overwrite:
        raise PreflightError(
            "output file already exists (use a new directory or --allow-overwrite): "
            + str(collisions[0])
        )
    return output, collisions


def _check_number(value: float, label: str, low: float, high: float) -> None:
    if not math.isfinite(value) or not low <= value <= high:
        raise PreflightError(f"{label} must be finite and in [{low}, {high}], received {value!r}")


def validate(args: argparse.Namespace) -> Tuple[Path, Path, List[Path], List[Path]]:
    errors: List[str] = []

    if args.encoder_type not in OPERATIONAL_ENCODERS:
        errors.append(
            f"--encoder_type {args.encoder_type!r} is parser-accepted but has no standalone mapping; "
            f"choose one of {', '.join(OPERATIONAL_ENCODERS)}"
        )

    for raw, label in (
        (args.ObjectAwareModel_path, "--ObjectAwareModel_path"),
        (args.Prompt_guided_Mask_Decoder_path, "--Prompt_guided_Mask_Decoder_path"),
        (args.encoder_path, "--encoder_path"),
    ):
        try:
            _check_checkpoint(raw, label)
        except PreflightError as exc:
            errors.append(str(exc))

    try:
        _check_number(args.imgsz, "--imgsz", 1, float("inf"))
    except PreflightError as exc:
        errors.append(str(exc))
    for value, label in ((args.iou, "--iou"), (args.conf, "--conf")):
        try:
            _check_number(value, label, 0.0, 1.0)
        except PreflightError as exc:
            errors.append(str(exc))

    input_dir: Optional[Path] = None
    images: List[Path] = []
    try:
        input_dir, images = _check_image_directory(args.img_path)
    except PreflightError as exc:
        errors.append(str(exc))

    output_dir: Optional[Path] = None
    collisions: List[Path] = []
    if input_dir is not None:
        try:
            output_dir, collisions = _check_output_directory(
                args.output_dir, input_dir, images, args.allow_overwrite
            )
        except PreflightError as exc:
            errors.append(str(exc))
    else:
        # Still reject obvious URL/empty output values so invalid input is
        # diagnosed in one pass, without touching the filesystem.
        try:
            output_dir = _local_path(args.output_dir, "--output_dir")
        except PreflightError as exc:
            errors.append(str(exc))

    if errors:
        raise PreflightError("\n".join(f"- {error}" for error in errors))
    assert input_dir is not None and output_dir is not None
    return input_dir, output_dir, images, collisions


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        input_dir, output_dir, images, collisions = validate(args)
    except PreflightError as exc:
        print("MobileSAMv2 preflight: FAILED", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2

    print("MobileSAMv2 preflight: PASS")
    print(f"  encoder: {args.encoder_type} ({OPERATIONAL_ENCODERS[args.encoder_type]})")
    print(f"  images: {len(images)} discovered under {input_dir}")
    print(f"  output: {output_dir}")
    print(f"  thresholds: imgsz={args.imgsz}, iou={args.iou}, conf={args.conf}, retina={args.retina}")
    if collisions:
        print(f"  existing outputs allowed: {len(collisions)}")
    print("  network: disabled; model import: skipped; inference: skipped; writes: skipped")
    print("This helper validates inputs only; actual inference requires a separately maintained CUDA runner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
