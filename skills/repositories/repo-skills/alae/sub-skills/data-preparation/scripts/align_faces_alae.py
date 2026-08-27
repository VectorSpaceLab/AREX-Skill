#!/usr/bin/env python3
"""Safe ALAE face-alignment helper.

This script adapts the useful alignment logic from ALAE's face-alignment
workflow while requiring explicit input, output, and dlib predictor paths. It
has no network, training, or hard-coded checkout side effects. `--help` and
`--dry-run` avoid importing dlib.

Example:
    python scripts/align_faces_alae.py \
      --input-dir raw_faces \
      --output-dir dataset_samples/faces/realign1024x1024 \
      --predictor shape_predictor_68_face_landmarks.dat \
      --output-size 1024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Align raw face images into ALAE-compatible sample images using dlib landmarks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing raw input images.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where aligned PNG files will be written.")
    parser.add_argument(
        "--predictor",
        type=Path,
        default=None,
        help="Path to dlib shape_predictor_68_face_landmarks.dat; required unless --dry-run is used.",
    )
    parser.add_argument(
        "--output-size",
        type=int,
        choices=(128, 1024),
        default=1024,
        help="Aligned image size. 1024 uses FFHQ/CelebA-HQ crop coefficients; 128 uses the legacy CelebA crop.",
    )
    parser.add_argument(
        "--transform-size",
        type=int,
        default=None,
        help="Intermediate transform size. Defaults to 4096 for 1024 output and 512 for 128 output.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Optional cap on input images scanned, useful for a small fixture run.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Check paths and planned work without importing dlib or writing images.")
    parser.add_argument(
        "--disable-padding",
        action="store_true",
        help="Disable reflection padding around tight crops. Defaults match the original padded workflow.",
    )
    return parser


def list_images(input_dir: Path, max_images: int | None) -> list[Path]:
    images = sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if max_images is not None:
        images = images[:max_images]
    return images


def import_runtime_dependencies():
    missing: list[str] = []
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        np = None
        missing.append(f"numpy ({exc})")
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        Image = None
        missing.append(f"Pillow/PIL ({exc})")
    try:
        import scipy.ndimage as ndimage  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        ndimage = None
        missing.append(f"scipy.ndimage ({exc})")
    try:
        import dlib  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        dlib = None
        missing.append(f"dlib ({exc})")

    if missing:
        raise RuntimeError(
            "Missing optional face-alignment dependencies: "
            + "; ".join(missing)
            + ". Install them and pass a local dlib 68-landmark predictor file."
        )
    return np, Image, ndimage, dlib


def pil_resample(Image, name: str):
    if hasattr(Image, "Resampling"):
        return getattr(Image.Resampling, name)
    fallback = {"LANCZOS": "ANTIALIAS", "BILINEAR": "BILINEAR"}[name]
    return getattr(Image, fallback)


def pil_transform_quad(Image):
    if hasattr(Image, "Transform"):
        return Image.Transform.QUAD
    return Image.QUAD


def align_face_array(
    img_array,
    landmarks,
    *,
    output_size: int,
    transform_size: int,
    enable_padding: bool,
    deps,
):
    """Return one aligned PIL image from an RGB numpy image and 68 dlib landmarks."""
    np, Image, ndimage = deps

    lm = np.array(landmarks)
    lm_eye_left = lm[36:42]
    lm_eye_right = lm[42:48]
    lm_mouth_outer = lm[48:60]

    eye_left = np.mean(lm_eye_left, axis=0)
    eye_right = np.mean(lm_eye_right, axis=0)
    eye_avg = (eye_left + eye_right) * 0.5
    eye_to_eye = eye_right - eye_left
    mouth_left = lm_mouth_outer[0]
    mouth_right = lm_mouth_outer[6]
    mouth_avg = (mouth_left + mouth_right) * 0.5
    eye_to_mouth = mouth_avg - eye_avg

    x = eye_to_eye - np.flipud(eye_to_mouth) * [-1, 1]
    x /= np.hypot(*x)

    use_1024_coefficients = output_size == 1024
    if use_1024_coefficients:
        x *= max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)
    else:
        x *= (np.hypot(*eye_to_eye) * 1.6410 + np.hypot(*eye_to_mouth) * 1.560) / 2.0

    y = np.flipud(x) * [-1, 1]
    if use_1024_coefficients:
        c = eye_avg + eye_to_mouth * 0.1
    else:
        c = eye_avg + eye_to_mouth * 0.317
    quad = np.stack([c - x - y, c - x + y, c + x + y, c + x - y])
    qsize = np.hypot(*x) * 2

    img = Image.fromarray(img_array)

    shrink = int(np.floor(qsize / output_size * 0.5))
    if shrink > 1:
        rsize = (int(np.rint(float(img.size[0]) / shrink)), int(np.rint(float(img.size[1]) / shrink)))
        img = img.resize(rsize, pil_resample(Image, "LANCZOS"))
        quad /= shrink
        qsize /= shrink

    border = max(int(np.rint(qsize * 0.1)), 3)
    crop = (
        int(np.floor(min(quad[:, 0]))),
        int(np.floor(min(quad[:, 1]))),
        int(np.ceil(max(quad[:, 0]))),
        int(np.ceil(max(quad[:, 1]))),
    )
    crop = (
        max(crop[0] - border, 0),
        max(crop[1] - border, 0),
        min(crop[2] + border, img.size[0]),
        min(crop[3] + border, img.size[1]),
    )
    if crop[2] - crop[0] < img.size[0] or crop[3] - crop[1] < img.size[1]:
        img = img.crop(crop)
        quad -= crop[0:2]

    pad = (
        int(np.floor(min(quad[:, 0]))),
        int(np.floor(min(quad[:, 1]))),
        int(np.ceil(max(quad[:, 0]))),
        int(np.ceil(max(quad[:, 1]))),
    )
    pad = (
        max(-pad[0] + border, 0),
        max(-pad[1] + border, 0),
        max(pad[2] - img.size[0] + border, 0),
        max(pad[3] - img.size[1] + border, 0),
    )
    if enable_padding and max(pad) > border - 4:
        pad = np.maximum(pad, int(np.rint(qsize * 0.3)))
        img_np = np.pad(np.float32(img), ((pad[1], pad[3]), (pad[0], pad[2]), (0, 0)), "reflect")
        h, w, _ = img_np.shape
        yy, xx, _ = np.ogrid[:h, :w, :1]
        mask = np.maximum(
            1.0 - np.minimum(np.float32(xx) / pad[0], np.float32(w - 1 - xx) / pad[2]),
            1.0 - np.minimum(np.float32(yy) / pad[1], np.float32(h - 1 - yy) / pad[3]),
        )
        blur = qsize * 0.02
        img_np += (ndimage.gaussian_filter(img_np, [blur, blur, 0]) - img_np) * np.clip(mask * 3.0 + 1.0, 0.0, 1.0)
        img_np += (np.median(img_np, axis=(0, 1)) - img_np) * np.clip(mask, 0.0, 1.0)
        img = Image.fromarray(np.uint8(np.clip(np.rint(img_np), 0, 255)), "RGB")
        quad += pad[:2]

    img = img.transform(
        (transform_size, transform_size),
        pil_transform_quad(Image),
        (quad + 0.5).flatten(),
        pil_resample(Image, "BILINEAR"),
    )
    if output_size < transform_size:
        img = img.resize((output_size, output_size), pil_resample(Image, "LANCZOS"))
    return img


def default_transform_size(output_size: int) -> int:
    return 4096 if output_size == 1024 else 512


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_images is not None and args.max_images < 1:
        parser.error("--max-images must be a positive integer when provided")

    input_dir = args.input_dir.expanduser()
    output_dir = args.output_dir.expanduser()
    predictor_path = args.predictor.expanduser() if args.predictor is not None else None
    transform_size = args.transform_size or default_transform_size(args.output_size)

    if not input_dir.is_dir():
        parser.error(f"--input-dir does not exist or is not a directory: {input_dir}")
    if not args.dry_run and predictor_path is None:
        parser.error("--predictor is required unless --dry-run is used")
    if not args.dry_run and predictor_path is not None and not predictor_path.is_file():
        parser.error(f"--predictor does not exist or is not a file: {predictor_path}")
    if transform_size < args.output_size:
        parser.error("--transform-size must be greater than or equal to --output-size")

    images = list_images(input_dir, args.max_images)
    if not images:
        print(f"No images with extensions {sorted(IMAGE_EXTENSIONS)} found in {input_dir}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("ALAE face-alignment dry run")
        print(f"input_dir: {input_dir}")
        print(f"output_dir: {output_dir}")
        print(f"predictor: {predictor_path if predictor_path else '<not supplied; required for real run>'}")
        print(f"output_size: {args.output_size}")
        print(f"transform_size: {transform_size}")
        print(f"images_to_scan: {len(images)}")
        for sample in images[:10]:
            print(f"  {sample.name}")
        if len(images) > 10:
            print(f"  ... {len(images) - 10} more")
        print("No dlib import and no files written in dry-run mode.")
        return 0

    try:
        np, Image, ndimage, dlib = import_runtime_dependencies()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(predictor_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    failed_images = 0
    deps = (np, Image, ndimage)
    for image_path in images:
        try:
            img = Image.open(image_path).convert("RGB")
            img_array = np.asarray(img)
        except Exception as exc:
            failed_images += 1
            print(f"[WARN] Could not read {image_path}: {exc}", file=sys.stderr)
            continue

        detections = detector(img_array, 0)
        print(f"{image_path.name}: detected {len(detections)} face(s)")
        for det in detections:
            shape = predictor(img_array, det)
            landmarks = [[part.x, part.y] for part in shape.parts()]
            aligned = align_face_array(
                img_array,
                landmarks,
                output_size=args.output_size,
                transform_size=transform_size,
                enable_padding=not args.disable_padding,
                deps=deps,
            )
            out_path = output_dir / f"{written:05d}.png"
            aligned.save(out_path)
            written += 1

    print(f"aligned_faces_written: {written}")
    print(f"failed_images: {failed_images}")
    print(f"output_dir: {output_dir}")
    if written == 0:
        print("No aligned faces were written. Check face visibility, predictor compatibility, and input image quality.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
