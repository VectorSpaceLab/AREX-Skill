#!/usr/bin/env python3
"""Pseudo-label an image folder with GroundingDINO detections.

This helper adapts the repository's dataset creation workflow with safer defaults:
- argparse instead of Typer, so --help works without optional Typer/FiftyOne imports
- explicit path/output validation
- no checkpoint, config, dataset, or model downloads
- no GUI launch unless --view is requested
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEFAULT_OUTPUT_DIR = "grounding_dino_pseudolabel_output"
COCO_SUBDIR = "coco_dataset"
ANNOTATED_SUBDIR = "images_with_bounding_boxes"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pseudo-label an image folder with GroundingDINO, optionally export COCO "
            "annotations, draw review images, or launch FiftyOne."
        )
    )
    parser.add_argument("--image-directory", required=True, help="Directory containing input images.")
    parser.add_argument(
        "--text-prompt",
        required=True,
        help='Prompt used for open-vocabulary detection, for example "bus . car .".',
    )
    parser.add_argument("--box-threshold", type=float, default=0.15, help="Box confidence threshold.")
    parser.add_argument("--text-threshold", type=float, default=0.10, help="Text token threshold.")
    parser.add_argument("--weights-path", required=True, help="Path to an existing GroundingDINO checkpoint.")
    parser.add_argument("--config-path", required=True, help="Path to an existing GroundingDINO config file.")
    parser.add_argument("--device", default="cuda", help="Torch device for model inference, e.g. cuda or cpu.")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Parent directory for COCO export and annotated images.",
    )
    parser.add_argument(
        "--subsample",
        type=int,
        default=None,
        help="Optional number of images to label before export/review.",
    )
    parser.add_argument("--export-coco", action="store_true", help="Export detections as a COCO detection dataset.")
    parser.add_argument("--draw-labels", action="store_true", help="Draw annotated review images.")
    parser.add_argument("--view", action="store_true", help="Launch the FiftyOne App after labeling.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove managed output subdirectories before writing new exports.",
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def import_or_fail(module_name: str, install_hint: str):
    try:
        return __import__(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            fail(f"Missing optional dependency '{module_name}'. Install it with: {install_hint}", exit_code=3)
        raise


def iter_images(image_directory: Path) -> Iterable[Path]:
    for path in sorted(image_directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            yield path


def validate_args(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    image_directory = Path(args.image_directory).expanduser()
    config_path = Path(args.config_path).expanduser()
    weights_path = Path(args.weights_path).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    if not image_directory.is_dir():
        fail(f"--image-directory must be an existing directory: {image_directory}")

    image_count = sum(1 for _ in iter_images(image_directory))
    if image_count == 0:
        allowed = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        fail(f"--image-directory contains no supported images ({allowed}): {image_directory}")

    if not config_path.is_file():
        fail(f"--config-path must be an existing file: {config_path}")

    if not weights_path.is_file():
        fail(f"--weights-path must be an existing file: {weights_path}")

    if not args.text_prompt.strip():
        fail("--text-prompt must not be empty")

    if not 0 <= args.box_threshold <= 1:
        fail("--box-threshold must be between 0 and 1")

    if not 0 <= args.text_threshold <= 1:
        fail("--text-threshold must be between 0 and 1")

    if args.subsample is not None and args.subsample <= 0:
        fail("--subsample must be a positive integer when provided")

    if not (args.export_coco or args.draw_labels or args.view):
        fail("choose at least one output action: --export-coco, --draw-labels, or --view")

    if output_dir.exists() and not output_dir.is_dir():
        fail(f"--output-dir exists but is not a directory: {output_dir}")

    managed_outputs = []
    if args.export_coco:
        managed_outputs.append(output_dir / COCO_SUBDIR)
    if args.draw_labels:
        managed_outputs.append(output_dir / ANNOTATED_SUBDIR)

    existing_outputs = [path for path in managed_outputs if path.exists()]
    if existing_outputs and not args.overwrite:
        joined = ", ".join(str(path) for path in existing_outputs)
        fail(f"output path already exists: {joined}. Use --overwrite or choose a new --output-dir")

    return image_directory, config_path, weights_path, output_dir


def prepare_output_dirs(output_dir: Path, args: argparse.Namespace) -> tuple[Path, Path]:
    coco_dir = output_dir / COCO_SUBDIR
    annotated_dir = output_dir / ANNOTATED_SUBDIR

    requested_outputs = []
    if args.export_coco:
        requested_outputs.append(coco_dir)
    if args.draw_labels:
        requested_outputs.append(annotated_dir)

    if requested_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)

    if args.overwrite:
        for path in requested_outputs:
            if path.exists():
                shutil.rmtree(path)

    return coco_dir, annotated_dir


def to_float(value) -> float:
    try:
        return float(value.item())
    except AttributeError:
        return float(value)


def to_box_list(box) -> list[float]:
    try:
        return [float(item) for item in box.tolist()]
    except AttributeError:
        return [float(item) for item in box]


def run(args: argparse.Namespace) -> None:
    image_directory, config_path, weights_path, output_dir = validate_args(args)
    coco_dir, annotated_dir = prepare_output_dirs(output_dir, args)

    fo = import_or_fail("fiftyone", "pip install fiftyone")
    torchvision = import_or_fail("torchvision", "pip install torchvision")

    try:
        from tqdm import tqdm
    except ModuleNotFoundError:
        tqdm = lambda values, **_: values

    try:
        from groundingdino.util.inference import load_image, load_model, predict
    except ModuleNotFoundError as exc:
        fail(
            "GroundingDINO is not importable. Install the package before running pseudo-labeling.",
            exit_code=3,
        )

    print("loading model...", file=sys.stderr)
    model = load_model(str(config_path), str(weights_path), device=args.device)

    dataset = fo.Dataset.from_images_dir(str(image_directory))
    if args.subsample is not None and args.subsample < len(dataset):
        dataset = dataset.take(args.subsample).clone()

    print(f"labeling {len(dataset)} image(s)...", file=sys.stderr)
    for sample in tqdm(dataset, desc="pseudo-labeling"):
        _, image = load_image(sample.filepath)
        boxes, logits, phrases = predict(
            model=model,
            image=image,
            caption=args.text_prompt,
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            device=args.device,
        )

        detections = []
        for box, logit, phrase in zip(boxes, logits, phrases):
            rel_xywh = torchvision.ops.box_convert(box, "cxcywh", "xywh")
            detections.append(
                fo.Detection(
                    label=str(phrase),
                    bounding_box=to_box_list(rel_xywh),
                    confidence=to_float(logit),
                )
            )

        sample["detections"] = fo.Detections(detections=detections)
        sample.save()

    if args.export_coco:
        print(f"exporting COCO dataset to {coco_dir}", file=sys.stderr)
        dataset.export(
            export_dir=str(coco_dir),
            dataset_type=fo.types.COCODetectionDataset,
            label_field="detections",
        )

    if args.draw_labels:
        print(f"drawing annotated images to {annotated_dir}", file=sys.stderr)
        dataset.draw_labels(str(annotated_dir), label_fields=["detections"])

    if args.view:
        print("launching FiftyOne App; omit --view for non-GUI runs", file=sys.stderr)
        session = fo.launch_app(dataset)
        session.wait()

    print("done", file=sys.stderr)


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
