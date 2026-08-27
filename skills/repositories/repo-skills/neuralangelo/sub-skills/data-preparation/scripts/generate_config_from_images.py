#!/usr/bin/env python3
"""Generate a small Neuralangelo YAML config patch from a prepared image folder.

The script is standalone: it does not import Neuralangelo source code and can be
run from any current working directory. It inspects image dimensions, applies the
same scene-type choices documented by the data-preparation skill, and writes a
YAML patch that inherits from Neuralangelo's base config.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Iterable

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _read_size_with_pillow(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            return int(image.size[0]), int(image.size[1])
    except Exception:
        return None


def _read_jpeg_size(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in {0xD8, 0xD9}:
            continue
        if i + 2 > len(data):
            return None
        seg_len = struct.unpack(">H", data[i:i + 2])[0]
        if seg_len < 2 or i + seg_len > len(data):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if seg_len >= 7:
                height = struct.unpack(">H", data[i + 3:i + 5])[0]
                width = struct.unpack(">H", data[i + 5:i + 7])[0]
                return int(width), int(height)
            return None
        i += seg_len
    return None


def read_image_size(path: Path) -> tuple[int, int]:
    """Return (width, height) with Pillow when available and stdlib fallbacks."""
    pillow_size = _read_size_with_pillow(path)
    if pillow_size:
        return pillow_size
    with path.open("rb") as handle:
        data = handle.read(512 * 1024)
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return int(width), int(height)
    if data.startswith(b"BM") and len(data) >= 26:
        width, height = struct.unpack("<ii", data[18:26])
        return abs(int(width)), abs(int(height))
    jpeg_size = _read_jpeg_size(data)
    if jpeg_size:
        return jpeg_size
    raise ValueError(f"could not determine image size for {path}")


def discover_images(images_dir: Path) -> list[Path]:
    if not images_dir.is_dir():
        raise FileNotFoundError(f"image directory does not exist: {images_dir}")
    images = sorted(
        path for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        raise FileNotFoundError(f"no image files found in {images_dir}")
    return images


def val_size_for_short_side(width: int, height: int, short_size: int) -> list[int]:
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    if width > height:
        return [int(short_size), int(round(width / height * short_size))]
    return [int(round(height / width * short_size)), int(short_size)]


def parse_vec3(text: str, name: str) -> list[float]:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(f"{name} must contain exactly three comma-separated numbers")
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must contain numbers") from exc


def build_config(args: argparse.Namespace, width: int, height: int, num_images: int) -> dict[str, Any]:
    if args.scene_type == "outdoor":
        inside_out = False
        init_active_level = 8
        background_enabled = None
        background_samples = None
    elif args.scene_type == "indoor":
        inside_out = True
        init_active_level = 8
        background_enabled = False
        background_samples = 0
    elif args.scene_type == "object":
        inside_out = False
        init_active_level = 4
        background_enabled = None
        background_samples = None
    else:  # argparse should prevent this.
        raise ValueError(f"unknown scene_type: {args.scene_type}")

    model: dict[str, Any] = {
        "object": {
            "sdf": {
                "mlp": {"inside_out": inside_out},
                "encoding": {"coarse2fine": {"init_active_level": init_active_level}},
            }
        },
        "appear_embed": {"enabled": bool(args.auto_exposure_wb)},
    }
    if args.auto_exposure_wb:
        model["appear_embed"]["dim"] = int(args.appearance_dim)
    if background_enabled is not None:
        model["background"] = {"enabled": background_enabled}
    if background_samples is not None:
        model.setdefault("render", {})["num_samples"] = {"background": background_samples}

    data_root = args.data_root if args.data_root is not None else str(args.data_dir)
    train: dict[str, Any] = {"image_size": [int(height), int(width)]}
    val: dict[str, Any] = {"image_size": val_size_for_short_side(width, height, args.val_short_size)}
    if args.train_batch_size is not None:
        train["batch_size"] = int(args.train_batch_size)
    if args.val_batch_size is not None:
        val["batch_size"] = int(args.val_batch_size)

    val_subset = args.val_subset
    if val_subset is None and args.auto_exposure_wb and num_images < 4:
        val_subset = num_images
    if val_subset is not None:
        val["subset"] = int(max(1, min(val_subset, num_images)))
    if args.max_viz_samples is not None:
        val["max_viz_samples"] = int(args.max_viz_samples)

    data: dict[str, Any] = {
        "type": "projects.neuralangelo.data",
        "root": data_root,
        "train": train,
        "val": val,
        "readjust": {"center": args.readjust_center, "scale": float(args.readjust_scale)},
    }
    if args.auto_exposure_wb:
        data["num_images"] = int(num_images)

    return {
        "_parent_": args.parent_config,
        "model": model,
        "data": data,
    }


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("cannot serialize non-finite float")
        return repr(float(value))
    if isinstance(value, str):
        return json.dumps(value)
    raise TypeError(f"unsupported scalar type: {type(value).__name__}")


def yaml_inline_list(values: Iterable[Any]) -> str:
    return "[" + ", ".join(yaml_scalar(value) for value in values) + "]"


def to_yaml(value: Any, indent: int = 0) -> str:
    space = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("YAML keys must be strings")
            if isinstance(item, dict):
                lines.append(f"{space}{key}:")
                lines.append(to_yaml(item, indent + 2))
            elif isinstance(item, list):
                if all(not isinstance(elem, (dict, list)) for elem in item):
                    lines.append(f"{space}{key}: {yaml_inline_list(item)}")
                else:
                    lines.append(f"{space}{key}:")
                    lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{space}{key}: {yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{space}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{space}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{space}{yaml_scalar(value)}"


def compare_transforms(transforms_path: Path, images: list[Path], width: int, height: int) -> None:
    if not transforms_path.exists():
        _warn(f"transforms file was requested but does not exist: {transforms_path}")
        return
    try:
        with transforms_path.open("r", encoding="utf-8") as handle:
            meta = json.load(handle)
    except Exception as exc:
        _warn(f"could not read transforms file {transforms_path}: {exc}")
        return
    frames = meta.get("frames")
    if isinstance(frames, list) and len(frames) != len(images):
        _warn(f"transforms frame count ({len(frames)}) differs from image count ({len(images)})")
    for key, actual in (("w", width), ("h", height)):
        expected = meta.get(key)
        if isinstance(expected, (int, float)) and int(expected) != actual:
            _warn(f"transforms {key}={expected} differs from first image {key}={actual}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained Neuralangelo YAML config patch from a prepared image directory.",
    )
    parser.add_argument("--data-dir", required=True, type=Path, help="Dataset root containing an image subdirectory.")
    parser.add_argument("--images-subdir", default="images", help="Image directory relative to --data-dir (default: images).")
    parser.add_argument("--data-root", default=None, help="Value to write into data.root; defaults to --data-dir as provided.")
    parser.add_argument("--sequence-name", default="recon", help="Human-readable sequence name for the generated header comment.")
    parser.add_argument("--scene-type", choices=["outdoor", "indoor", "object"], default="outdoor")
    parser.add_argument("--auto-exposure-wb", action="store_true", help="Enable appearance embeddings and write data.num_images.")
    parser.add_argument("--appearance-dim", type=int, default=8, help="Appearance embedding dimension when enabled.")
    parser.add_argument("--val-short-size", type=int, default=300, help="Short side for validation image size.")
    parser.add_argument("--val-subset", type=int, default=None, help="Optional validation subset; clamped to image count.")
    parser.add_argument("--train-batch-size", type=int, default=None, help="Optional data.train.batch_size override.")
    parser.add_argument("--val-batch-size", type=int, default=None, help="Optional data.val.batch_size override.")
    parser.add_argument("--max-viz-samples", type=int, default=None, help="Optional data.val.max_viz_samples override.")
    parser.add_argument("--readjust-center", type=lambda s: parse_vec3(s, "--readjust-center"), default=[0.0, 0.0, 0.0], help="Comma-separated data.readjust.center.")
    parser.add_argument("--readjust-scale", type=float, default=1.0, help="data.readjust.scale.")
    parser.add_argument("--parent-config", default="projects/neuralangelo/configs/base.yaml", help="YAML _parent_ value.")
    parser.add_argument("--transforms", type=Path, default=None, help="Optional transforms.json to compare frame count/dimensions against.")
    parser.add_argument("--output", type=Path, default=None, help="Output YAML path. If omitted, write to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.val_short_size <= 0:
        raise SystemExit("--val-short-size must be positive")
    if args.appearance_dim <= 0:
        raise SystemExit("--appearance-dim must be positive")
    if args.readjust_scale <= 0:
        raise SystemExit("--readjust-scale must be positive")

    images_dir = args.data_dir / args.images_subdir
    images = discover_images(images_dir)
    width, height = read_image_size(images[0])
    for path in images[1:]:
        try:
            w, h = read_image_size(path)
        except Exception as exc:
            _warn(f"could not inspect {path}: {exc}")
            continue
        if (w, h) != (width, height):
            _warn(f"{path.name} has size {w}x{h}, first image has {width}x{height}; Neuralangelo will resize but metadata should match the raw source set")

    transforms_path = args.transforms if args.transforms else args.data_dir / "transforms.json"
    if transforms_path.exists():
        compare_transforms(transforms_path, images, width, height)

    config = build_config(args, width, height, len(images))
    header = (
        f"# Generated Neuralangelo data config patch for {args.sequence_name}.\n"
        f"# Source images: {len(images)} files under {args.images_subdir}/, first image {height}x{width} (H x W).\n"
    )
    text = header + to_yaml(config) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote config: {args.output}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
