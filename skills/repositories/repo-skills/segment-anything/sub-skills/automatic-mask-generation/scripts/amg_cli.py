#!/usr/bin/env python3
"""Run Segment Anything automatic mask generation on one image or a folder."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
METADATA_HEADER = [
    "id",
    "area",
    "bbox_x0",
    "bbox_y0",
    "bbox_w",
    "bbox_h",
    "point_input_x",
    "point_input_y",
    "predicted_iou",
    "stability_score",
    "crop_box_x0",
    "crop_box_y0",
    "crop_box_w",
    "crop_box_h",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run automatic mask generation on one image or a folder of images. "
            "Outputs either binary PNG masks plus metadata.csv, or COCO RLE JSON."
        )
    )
    parser.add_argument("--input", required=True, help="Path to one input image or a folder of images.")
    parser.add_argument("--output", required=True, help="Directory where mask outputs will be written.")
    parser.add_argument(
        "--model-type",
        required=True,
        choices=["default", "vit_h", "vit_l", "vit_b"],
        help="SAM model registry key matching the checkpoint.",
    )
    parser.add_argument("--checkpoint", required=True, help="Path to the SAM checkpoint.")
    parser.add_argument("--device", default="cuda", help="PyTorch device to use, for example cuda or cpu.")
    parser.add_argument(
        "--convert-to-rle",
        action="store_true",
        help="Write COCO RLE JSON instead of PNG masks. Requires pycocotools.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing per-image output folders or JSON files.",
    )

    amg_settings = parser.add_argument_group("AMG settings")
    amg_settings.add_argument("--points-per-side", type=int, default=None)
    amg_settings.add_argument("--points-per-batch", type=int, default=None)
    amg_settings.add_argument("--pred-iou-thresh", type=float, default=None)
    amg_settings.add_argument("--stability-score-thresh", type=float, default=None)
    amg_settings.add_argument("--stability-score-offset", type=float, default=None)
    amg_settings.add_argument("--box-nms-thresh", type=float, default=None)
    amg_settings.add_argument("--crop-n-layers", type=int, default=None)
    amg_settings.add_argument("--crop-nms-thresh", type=float, default=None)
    amg_settings.add_argument("--crop-overlap-ratio", type=float, default=None)
    amg_settings.add_argument("--crop-n-points-downscale-factor", type=int, default=None)
    amg_settings.add_argument("--min-mask-region-area", type=int, default=None)
    return parser


def collect_targets(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    targets = [
        path
        for path in sorted(input_path.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not targets:
        raise FileNotFoundError(f"No supported image files found in folder: {input_path}")
    return targets


def get_amg_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    values = {
        "points_per_side": args.points_per_side,
        "points_per_batch": args.points_per_batch,
        "pred_iou_thresh": args.pred_iou_thresh,
        "stability_score_thresh": args.stability_score_thresh,
        "stability_score_offset": args.stability_score_offset,
        "box_nms_thresh": args.box_nms_thresh,
        "crop_n_layers": args.crop_n_layers,
        "crop_nms_thresh": args.crop_nms_thresh,
        "crop_overlap_ratio": args.crop_overlap_ratio,
        "crop_n_points_downscale_factor": args.crop_n_points_downscale_factor,
        "min_mask_region_area": args.min_mask_region_area,
    }
    return {key: value for key, value in values.items() if value is not None}


def prepare_destination(path: Path, overwrite: bool, is_dir: bool) -> None:
    if path.exists():
        if not overwrite:
            kind = "directory" if path.is_dir() else "file"
            raise FileExistsError(f"Output {kind} already exists: {path}. Use --overwrite to replace it.")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    if is_dir:
        path.mkdir(parents=True, exist_ok=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)


def write_masks_to_folder(masks: List[Dict[str, Any]], path: Path, cv2_module: Any) -> None:
    rows = [",".join(METADATA_HEADER)]
    for mask_id, mask_data in enumerate(masks):
        filename = f"{mask_id}.png"
        mask_path = path / filename
        ok = cv2_module.imwrite(str(mask_path), mask_data["segmentation"] * 255)
        if not ok:
            raise OSError(f"Failed to write mask PNG: {mask_path}")
        point = mask_data["point_coords"][0]
        row = [
            mask_id,
            mask_data["area"],
            *mask_data["bbox"],
            point[0],
            point[1],
            mask_data["predicted_iou"],
            mask_data["stability_score"],
            *mask_data["crop_box"],
        ]
        rows.append(",".join(str(value) for value in row))
    (path / "metadata.csv").write_text("\n".join(rows), encoding="utf-8")


def ensure_optional_dependencies(convert_to_rle: bool) -> None:
    if convert_to_rle:
        try:
            import pycocotools.mask  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "--convert-to-rle requires pycocotools. Install pycocotools or omit --convert-to-rle."
            ) from exc


def load_image(path: Path, cv2_module: Any):
    image = cv2_module.imread(str(path))
    if image is None:
        return None
    return cv2_module.cvtColor(image, cv2_module.COLOR_BGR2RGB)


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output)
    checkpoint = Path(args.checkpoint)

    if not checkpoint.is_file():
        raise FileNotFoundError(f"Checkpoint file does not exist: {checkpoint}")

    targets = collect_targets(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("This CLI requires OpenCV. Install opencv-python and retry.") from exc

    ensure_optional_dependencies(args.convert_to_rle)

    try:
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
    except ImportError as exc:
        raise RuntimeError("Could not import segment_anything. Install the Segment Anything package first.") from exc

    print("Loading model...")
    sam = sam_model_registry[args.model_type](checkpoint=str(checkpoint))
    try:
        sam.to(device=args.device)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to move model to device '{args.device}'. Use --device cpu if CUDA is unavailable."
        ) from exc

    output_mode = "coco_rle" if args.convert_to_rle else "binary_mask"
    generator = SamAutomaticMaskGenerator(sam, output_mode=output_mode, **get_amg_kwargs(args))

    processed = 0
    skipped = 0
    for target in targets:
        print(f"Processing '{target}'...")
        image = load_image(target, cv2)
        if image is None:
            print(f"Could not load '{target}' as an image; skipping.", file=sys.stderr)
            skipped += 1
            continue

        masks = generator.generate(image)
        stem = target.stem
        if args.convert_to_rle:
            save_file = output_dir / f"{stem}.json"
            prepare_destination(save_file, args.overwrite, is_dir=False)
            save_file.write_text(json.dumps(masks), encoding="utf-8")
        else:
            save_folder = output_dir / stem
            prepare_destination(save_folder, args.overwrite, is_dir=True)
            write_masks_to_folder(masks, save_folder, cv2)
        processed += 1

    print(f"Done. Processed {processed} image(s), skipped {skipped} unreadable image(s).")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:
        parser.exit(status=1, message=f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
