#!/usr/bin/env python3
"""Run GFPGAN inference with explicit, safe checkpoint handling.

Examples:
    python scripts/run_inference.py --input photo.jpg --output out --model-path weights/GFPGANv1.4.pth --version 1.4 --no-bg-upsampler
    python scripts/run_inference.py --input crops/ --output out --model-path weights/GFPGANv1.3.pth --version 1.3 --aligned
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np
import torch
from basicsr.utils import imwrite
from gfpgan import GFPGANer


MODEL_MAP: Dict[str, Dict[str, object]] = {
    "1": {
        "arch": "original",
        "channel_multiplier": 1,
        "filename": "GFPGANv1.pth",
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v0.1.0/GFPGANv1.pth",
    },
    "1.2": {
        "arch": "clean",
        "channel_multiplier": 2,
        "filename": "GFPGANCleanv1-NoCE-C2.pth",
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v0.2.0/GFPGANCleanv1-NoCE-C2.pth",
    },
    "1.3": {
        "arch": "clean",
        "channel_multiplier": 2,
        "filename": "GFPGANv1.3.pth",
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
    },
    "1.4": {
        "arch": "clean",
        "channel_multiplier": 2,
        "filename": "GFPGANv1.4.pth",
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
    },
    "RestoreFormer": {
        "arch": "RestoreFormer",
        "channel_multiplier": 2,
        "filename": "RestoreFormer.pth",
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/RestoreFormer.pth",
    },
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GFPGAN face restoration on an image or folder.")
    parser.add_argument("-i", "--input", required=True, help="Input image or folder.")
    parser.add_argument("-o", "--output", required=True, help="Output folder.")
    parser.add_argument("-v", "--version", default="1.4", choices=sorted(MODEL_MAP), help="GFPGAN model version.")
    parser.add_argument("-s", "--upscale", type=int, default=2, help="Final upsampling scale.")
    parser.add_argument("--model-path", help="Local GFPGAN checkpoint path. Required unless --allow-download is set and no local candidate exists.")
    parser.add_argument("--weights-dir", default="weights", help="Directory to search for version checkpoint when --model-path is omitted.")
    parser.add_argument("--allow-download", action="store_true", help="Allow GFPGANer/BasicSR to download the version checkpoint URL if no local file is found.")
    parser.add_argument("--bg-upsampler", choices=["none", "realesrgan"], default="none", help="Optional background upsampler.")
    parser.add_argument("--no-bg-upsampler", action="store_const", const="none", dest="bg_upsampler", help="Disable background upsampling.")
    parser.add_argument("--bg-model-path", help="Local Real-ESRGAN checkpoint path when --bg-upsampler realesrgan is used.")
    parser.add_argument("--bg-tile", type=int, default=400, help="Real-ESRGAN tile size; 0 disables tiling.")
    parser.add_argument("--suffix", default=None, help="Suffix for restored face and image filenames.")
    parser.add_argument("--only-center-face", action="store_true", help="Only restore the center face.")
    parser.add_argument("--aligned", action="store_true", help="Treat inputs as already aligned face crops.")
    parser.add_argument("--ext", default="auto", choices=["auto", "jpg", "png"], help="Output extension.")
    parser.add_argument("-w", "--weight", type=float, default=0.5, help="Restoration weight passed to GFPGANer.enhance.")
    parser.add_argument("--device", default="auto", help="Device for GFPGAN, e.g. auto, cpu, cuda, cuda:0.")
    return parser.parse_args()


def iter_images(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    matches = [Path(p) for p in glob.glob(str(input_path))]
    return sorted(p for p in matches if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def resolve_model_path(args: argparse.Namespace) -> str:
    info = MODEL_MAP[args.version]
    filename = str(info["filename"])
    candidates: List[Path] = []
    if args.model_path:
        candidates.append(Path(args.model_path))
    else:
        candidates.extend([
            Path(args.weights_dir) / filename,
            Path("experiments") / "pretrained_models" / filename,
            Path("gfpgan") / "weights" / filename,
        ])
    for path in candidates:
        if path.is_file():
            return str(path)
    if args.allow_download:
        return str(info["url"])
    searched = ", ".join(str(p) for p in candidates) or filename
    raise FileNotFoundError(
        f"Missing checkpoint for version {args.version}. Expected {filename}. "
        f"Searched: {searched}. Pass --model-path or explicitly add --allow-download."
    )


def build_bg_upsampler(args: argparse.Namespace):
    if args.bg_upsampler == "none":
        return None
    if args.bg_upsampler != "realesrgan":
        raise ValueError(f"Unsupported background upsampler: {args.bg_upsampler}")
    try:
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except Exception as exc:
        raise RuntimeError("Real-ESRGAN background upsampling requires the optional 'realesrgan' package.") from exc

    if not torch.cuda.is_available() and args.device != "cuda":
        print("Warning: Real-ESRGAN background upsampling is slow on CPU; continuing because it was explicitly requested.", file=sys.stderr)

    model_path = args.bg_model_path
    if not model_path and args.allow_download:
        model_path = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
    if not model_path or (not str(model_path).startswith("https://") and not Path(model_path).is_file()):
        raise FileNotFoundError("Pass --bg-model-path for Real-ESRGAN or explicitly use --allow-download.")

    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
    half = torch.cuda.is_available() and not str(args.device).startswith("cpu")
    return RealESRGANer(scale=2, model_path=model_path, model=model, tile=args.bg_tile, tile_pad=10, pre_pad=0, half=half)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_image(path: Path, image: np.ndarray) -> None:
    ensure_parent(path)
    imwrite(image, str(path))


def output_extension(input_path: Path, requested: str, img: np.ndarray) -> str:
    if requested != "auto":
        return requested
    ext = input_path.suffix.lower().lstrip(".") or "png"
    if img.ndim == 3 and img.shape[2] == 4:
        return "png"
    return "jpg" if ext == "jpeg" else ext


def process_image(restorer: GFPGANer, img_path: Path, out_dir: Path, args: argparse.Namespace) -> Tuple[int, int]:
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image: {img_path}")

    basename = img_path.stem
    cropped_faces, restored_faces, restored_img = restorer.enhance(
        img,
        has_aligned=args.aligned,
        only_center_face=args.only_center_face,
        paste_back=True,
        weight=args.weight,
    )

    for idx, (cropped_face, restored_face) in enumerate(zip(cropped_faces, restored_faces)):
        save_image(out_dir / "cropped_faces" / f"{basename}_{idx:02d}.png", cropped_face)
        face_name = f"{basename}_{idx:02d}_{args.suffix}.png" if args.suffix else f"{basename}_{idx:02d}.png"
        save_image(out_dir / "restored_faces" / face_name, restored_face)
        cmp_img = np.concatenate((cropped_face, restored_face), axis=1)
        save_image(out_dir / "cmp" / f"{basename}_{idx:02d}.png", cmp_img)

    if restored_img is not None:
        ext = output_extension(img_path, args.ext, restored_img)
        image_name = f"{basename}_{args.suffix}.{ext}" if args.suffix else f"{basename}.{ext}"
        save_image(out_dir / "restored_imgs" / image_name, restored_img)

    return len(cropped_faces), len(restored_faces)


def main() -> int:
    args = parse_args()
    image_paths = iter_images(Path(args.input))
    if not image_paths:
        print(f"No input images found for {args.input}", file=sys.stderr)
        return 2

    model_path = resolve_model_path(args)
    info = MODEL_MAP[args.version]
    device = None if args.device == "auto" else torch.device(args.device)
    bg_upsampler = build_bg_upsampler(args)

    restorer = GFPGANer(
        model_path=model_path,
        upscale=args.upscale,
        arch=str(info["arch"]),
        channel_multiplier=int(info["channel_multiplier"]),
        bg_upsampler=bg_upsampler,
        device=device,
    )

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    total_faces = 0
    for img_path in image_paths:
        try:
            cropped, restored = process_image(restorer, img_path, out_dir, args)
            total_faces += restored
            print(f"Processed {img_path.name}: {cropped} cropped face(s), {restored} restored face(s)")
        except Exception as exc:  # continue batch, fail at end
            failures += 1
            print(f"FAILED {img_path}: {exc.__class__.__name__}: {exc}", file=sys.stderr)

    print(f"Results are in: {out_dir}")
    print(f"Restored faces: {total_faces}; failed images: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
