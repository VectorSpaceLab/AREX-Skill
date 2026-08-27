#!/usr/bin/env python3
"""Create a tiny YOLO crop fixture for Lightly without importing Lightly."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Sequence

try:
    from PIL import Image, ImageDraw
except Exception as exc:  # pragma: no cover - exercised only without Pillow
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    PIL_IMPORT_ERROR = exc
else:
    PIL_IMPORT_ERROR = None

CLASS_NAMES = ["object_a", "object_b", "object_c"]


def yolo_box(index: int, object_index: int) -> tuple[float, float, float, float]:
    x_center = 0.35 + 0.15 * ((index + object_index) % 3)
    y_center = 0.40 + 0.12 * (object_index % 2)
    width = 0.28
    height = 0.30
    return x_center, y_center, width, height


def normalized_to_pixels(
    box: tuple[float, float, float, float], image_size: int
) -> tuple[int, int, int, int]:
    x_center, y_center, width, height = box
    left = int((x_center - width / 2) * image_size)
    top = int((y_center - height / 2) * image_size)
    right = int((x_center + width / 2) * image_size)
    bottom = int((y_center + height / 2) * image_size)
    return left, top, right, bottom


def ensure_output_dir(path: Path, force: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not force:
            raise SystemExit(
                f"output directory exists and is not empty: {path}\n"
                "Use --force to replace it."
            )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_data_yaml(path: Path, class_names: Sequence[str]) -> None:
    names = ", ".join(class_names)
    path.write_text(f"names: [{names}]\n", encoding="utf-8")


def create_fixture(args: argparse.Namespace) -> dict[str, object]:
    if Image is None or ImageDraw is None:
        raise SystemExit(
            "Pillow is required to create PNG/JPG fixture images. "
            f"Import error: {PIL_IMPORT_ERROR}"
        )

    output_dir: Path = args.output_dir
    ensure_output_dir(output_dir, force=args.force)
    image_root = output_dir / "images"
    label_root = output_dir / "labels"
    image_root.mkdir(parents=True, exist_ok=True)
    label_root.mkdir(parents=True, exist_ok=True)

    created_images: list[str] = []
    created_labels: list[str] = []
    class_names = CLASS_NAMES[: args.num_classes]

    for index in range(args.num_images):
        subdir = Path()
        if args.nested_class_dirs:
            subdir = Path(class_names[index % len(class_names)])
            (image_root / subdir).mkdir(parents=True, exist_ok=True)
            (label_root / subdir).mkdir(parents=True, exist_ok=True)

        suffix = ".png" if index % 2 == 0 else ".jpg"
        stem = f"img_{index:03d}"
        image_path = image_root / subdir / f"{stem}{suffix}"
        label_path = label_root / subdir / f"{stem}.txt"

        color = (40 + index * 30 % 180, 90 + index * 20 % 120, 160 + index * 10 % 80)
        image = Image.new("RGB", (args.image_size, args.image_size), color=color)
        draw = ImageDraw.Draw(image)
        label_lines: list[str] = []
        for object_index in range(args.objects_per_image):
            class_id = object_index % len(class_names)
            box = yolo_box(index, object_index)
            rect = normalized_to_pixels(box, args.image_size)
            draw.rectangle(rect, outline=(255, 255, 255), width=max(1, args.image_size // 32))
            x_center, y_center, width, height = box
            label_lines.append(
                f"{class_id} {x_center:.4f} {y_center:.4f} {width:.4f} {height:.4f}\n"
            )

        image.save(image_path)
        label_path.write_text("".join(label_lines), encoding="utf-8")
        created_images.append(str(image_path.relative_to(output_dir)))
        created_labels.append(str(label_path.relative_to(output_dir)))

    data_yaml = None
    if not args.no_data_yaml:
        data_yaml_path = output_dir / "data.yaml"
        write_data_yaml(data_yaml_path, class_names)
        data_yaml = str(data_yaml_path.relative_to(output_dir))

    crop_output = output_dir / "cropped"
    command = (
        f"lightly-crop input_dir={image_root} label_dir={label_root} "
        f"output_dir={crop_output} crop_padding={args.crop_padding}"
    )
    if data_yaml is not None:
        command += f" label_names_file={output_dir / data_yaml}"

    return {
        "output_dir": str(output_dir),
        "images": created_images,
        "labels": created_labels,
        "data_yaml": data_yaml,
        "example_crop_command": command,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny image + YOLO-label fixture for testing Lightly crop commands. "
            "The script imports Pillow only, never Lightly or the original repository."
        )
    )
    parser.add_argument("output_dir", type=Path, help="Directory to create or replace with --force.")
    parser.add_argument("--num-images", type=int, default=4, help="Number of images to create; default: 4.")
    parser.add_argument("--objects-per-image", type=int, default=2, help="YOLO rows per image; default: 2.")
    parser.add_argument("--image-size", type=int, default=64, help="Square image size in pixels; default: 64.")
    parser.add_argument("--num-classes", type=int, default=3, choices=range(1, 4), metavar="1..3", help="Number of class names to write; default: 3.")
    parser.add_argument("--crop-padding", type=float, default=0.1, help="Crop padding value printed in the example command.")
    parser.add_argument("--nested-class-dirs", action="store_true", help="Create mirrored class subdirectories under images/ and labels/.")
    parser.add_argument("--no-data-yaml", action="store_true", help="Do not create data.yaml with class names.")
    parser.add_argument("--force", action="store_true", help="Replace a non-empty output directory.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.num_images < 1:
        parser.error("--num-images must be at least 1")
    if args.objects_per_image < 0:
        parser.error("--objects-per-image must be non-negative")
    if args.image_size < 16:
        parser.error("--image-size must be at least 16 pixels")
    if args.crop_padding < 0:
        parser.error("--crop-padding must be non-negative")

    summary = create_fixture(args)
    print(f"created fixture under: {summary['output_dir']}")
    print("images:")
    for path in summary["images"]:  # type: ignore[index]
        print(f"  {path}")
    print("labels:")
    for path in summary["labels"]:  # type: ignore[index]
        print(f"  {path}")
    if summary["data_yaml"]:
        print(f"data yaml: {summary['data_yaml']}")
    print("example crop command (not executed):")
    print(f"  {summary['example_crop_command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
