#!/usr/bin/env python3
"""Extract CLIP image features from a local image directory into a .npz archive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

DEFAULT_EXTENSIONS = (".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp")


class ImagePathDataset:
    def __init__(self, paths: List[Path], preprocess, fail_on_error: bool):
        self.paths = paths
        self.preprocess = preprocess
        self.fail_on_error = fail_on_error

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int):
        from PIL import Image, UnidentifiedImageError

        path = self.paths[index]
        try:
            with Image.open(path) as image:
                tensor = self.preprocess(image.convert("RGB"))
            return tensor, str(path), ""
        except (OSError, UnidentifiedImageError) as exc:
            if self.fail_on_error:
                raise
            return None, str(path), f"{type(exc).__name__}: {exc}"


def collate_batch(batch):
    import torch

    tensors = []
    paths = []
    errors = []
    for tensor, path, error in batch:
        if error:
            errors.append((path, error))
        else:
            tensors.append(tensor)
            paths.append(path)
    if tensors:
        return torch.stack(tensors), paths, errors
    return None, paths, errors


def parse_extensions(value: str) -> Tuple[str, ...]:
    extensions = []
    for raw_extension in value.split(","):
        extension = raw_extension.strip().lower()
        if not extension:
            continue
        if not extension.startswith("."):
            extension = f".{extension}"
        extensions.append(extension)
    if not extensions:
        raise argparse.ArgumentTypeError("at least one image extension is required")
    return tuple(sorted(set(extensions)))


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def collect_image_paths(image_dir: Path, extensions: Iterable[str], recursive: bool) -> List[Path]:
    normalized_extensions = {extension.lower() for extension in extensions}
    iterator = image_dir.rglob("*") if recursive else image_dir.iterdir()
    return sorted(
        path for path in iterator
        if path.is_file() and path.suffix.lower() in normalized_extensions
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract CLIP image embeddings from a local image directory and save a .npz archive."
    )
    parser.add_argument("--image-dir", required=True, type=Path, help="Directory containing input images.")
    parser.add_argument("--output", required=True, type=Path, help="Output .npz file path.")
    parser.add_argument(
        "--model",
        default="ViT-B/32",
        help="CLIP model name or local checkpoint path accepted by clip.load. Default: ViT-B/32.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device for extraction: auto, cpu, cuda, cuda:0, etc. Default: auto.",
    )
    parser.add_argument(
        "--download-root",
        default=None,
        help="Optional CLIP cache/download directory, or a cache containing a pre-downloaded checkpoint.",
    )
    parser.add_argument("--jit", action="store_true", help="Request JIT model loading from clip.load.")
    parser.add_argument("--batch-size", type=positive_int, default=64, help="Images per batch. Default: 64.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers. Default: 0.")
    parser.add_argument("--recursive", action="store_true", help="Search image-dir recursively.")
    parser.add_argument(
        "--extensions",
        type=parse_extensions,
        default=DEFAULT_EXTENSIONS,
        help="Comma-separated image extensions. Default: bmp,gif,jpeg,jpg,png,webp.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Save raw encoder features instead of L2-normalized features.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Stop on the first unreadable image instead of recording and skipping it.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num_workers < 0:
        parser.error("--num-workers must be >= 0")
    if not args.image_dir.is_dir():
        parser.error(f"--image-dir is not a directory: {args.image_dir}")
    if args.output.suffix.lower() != ".npz":
        parser.error("--output must end with .npz")

    try:
        import numpy as np
        import torch
        from torch.utils.data import DataLoader
        import clip
    except ImportError as exc:
        print(
            "Missing runtime dependency. Install CLIP with its PyTorch/Pillow/numpy dependencies before extraction. "
            f"Original import error: {exc}",
            file=sys.stderr,
        )
        return 2

    image_paths = collect_image_paths(args.image_dir, args.extensions, args.recursive)
    if not image_paths:
        parser.error("no input images matched the requested extensions")

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else "cpu" if args.device == "auto" else args.device
    model, preprocess = clip.load(args.model, device=device, jit=args.jit, download_root=args.download_root)
    model.eval()

    dataset = ImagePathDataset(image_paths, preprocess, args.fail_on_error)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_batch,
    )

    all_features = []
    all_paths = []
    failed_paths = []
    failed_errors = []

    with torch.no_grad():
        for images, paths, errors in loader:
            for failed_path, error in errors:
                failed_paths.append(failed_path)
                failed_errors.append(error)
            if images is None:
                continue
            images = images.to(device)
            features = model.encode_image(images).float()
            if not args.no_normalize:
                features = features / features.norm(dim=-1, keepdim=True).clamp_min(1e-12)
            all_features.append(features.cpu().numpy())
            all_paths.extend(paths)

    if not all_features:
        print("No images were successfully processed.", file=sys.stderr)
        return 1

    features_array = np.concatenate(all_features, axis=0).astype("float32", copy=False)
    paths_array = np.asarray(all_paths, dtype=object)
    failed_paths_array = np.asarray(failed_paths, dtype=object)
    failed_errors_array = np.asarray(failed_errors, dtype=object)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        features=features_array,
        paths=paths_array,
        normalized=np.asarray(not args.no_normalize),
        model=np.asarray(str(args.model)),
        device=np.asarray(str(device)),
        batch_size=np.asarray(args.batch_size),
        recursive=np.asarray(args.recursive),
        extensions=np.asarray(tuple(args.extensions), dtype=object),
        failed_paths=failed_paths_array,
        failed_errors=failed_errors_array,
    )

    print(
        f"saved {features_array.shape[0]} features to {args.output} "
        f"({len(failed_paths)} skipped, normalized={not args.no_normalize})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
