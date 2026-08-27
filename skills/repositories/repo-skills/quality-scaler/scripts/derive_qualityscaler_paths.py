#!/usr/bin/env python3
"""Derive QualityScaler output filenames and directories.

Purpose:
- Reproduce the app's output naming rules without importing the GUI module.
- Preview image, video, and frame output paths safely from any working directory.

Example:
  python derive_qualityscaler_paths.py --mode image --source-path input.png \
      --selected-ai-model BSRGANx4 --input-resize-factor 0.5 \
      --output-resize-factor 1.0 --selected-image-extension .jpg \
      --selected-blending-factor 0.3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

OUTPUT_PATH_CODED = "Same path as input files"


def _suffix(model: str, input_resize_factor: float, output_resize_factor: float, blending_factor: float) -> str:
    suffix = f"_{model}"
    suffix += f"_InputR-{int(input_resize_factor * 100)}"
    suffix += f"_OutputR-{int(output_resize_factor * 100)}"
    if blending_factor == 0.3:
        suffix += "_Blending-Low"
    elif blending_factor == 0.5:
        suffix += "_Blending-Medium"
    elif blending_factor == 0.7:
        suffix += "_Blending-High"
    return suffix


def _stem_or_join(source_path: str, selected_output_path: str) -> str:
    source = Path(source_path)
    if selected_output_path == OUTPUT_PATH_CODED:
        return str(source.with_suffix(""))
    return str(Path(selected_output_path) / source.with_suffix("").name)


def prepare_output_image_filename(
    image_path: str,
    selected_output_path: str,
    selected_ai_model: str,
    input_resize_factor: float,
    output_resize_factor: float,
    selected_image_extension: str,
    selected_blending_factor: float,
) -> str:
    return (
        _stem_or_join(image_path, selected_output_path)
        + _suffix(selected_ai_model, input_resize_factor, output_resize_factor, selected_blending_factor)
        + selected_image_extension
    )


def prepare_output_video_directory_name(
    video_path: str,
    selected_output_path: str,
    selected_ai_model: str,
    input_resize_factor: float,
    output_resize_factor: float,
    selected_blending_factor: float,
) -> str:
    return _stem_or_join(video_path, selected_output_path) + _suffix(
        selected_ai_model,
        input_resize_factor,
        output_resize_factor,
        selected_blending_factor,
    )


def prepare_output_video_filename(
    video_path: str,
    selected_output_path: str,
    selected_ai_model: str,
    input_resize_factor: float,
    output_resize_factor: float,
    selected_video_extension: str,
    selected_blending_factor: float,
) -> str:
    return (
        _stem_or_join(video_path, selected_output_path)
        + _suffix(selected_ai_model, input_resize_factor, output_resize_factor, selected_blending_factor)
        + selected_video_extension
    )


def prepare_output_video_frame_filename(
    frame_path: str,
    selected_ai_model: str,
    input_resize_factor: float,
    output_resize_factor: float,
    selected_blending_factor: float,
) -> str:
    return (
        str(Path(frame_path).with_suffix(""))
        + _suffix(selected_ai_model, input_resize_factor, output_resize_factor, selected_blending_factor)
        + ".jpg"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview QualityScaler output filenames and directories.",
    )
    parser.add_argument("--mode", choices={"image", "video", "frame"}, required=True)
    parser.add_argument("--source-path", required=True, help="Input image, video, or frame path.")
    parser.add_argument(
        "--selected-output-path",
        default=OUTPUT_PATH_CODED,
        help='Chosen output directory or "Same path as input files".',
    )
    parser.add_argument("--selected-ai-model", required=True)
    parser.add_argument("--input-resize-factor", type=float, required=True)
    parser.add_argument("--output-resize-factor", type=float, required=True)
    parser.add_argument("--selected-blending-factor", type=float, default=0.0)
    parser.add_argument("--selected-image-extension", default=".jpg")
    parser.add_argument("--selected-video-extension", default=".mp4")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.mode == "image":
        result = {
            "mode": "image",
            "output": prepare_output_image_filename(
                args.source_path,
                args.selected_output_path,
                args.selected_ai_model,
                args.input_resize_factor,
                args.output_resize_factor,
                args.selected_image_extension,
                args.selected_blending_factor,
            ),
        }
    elif args.mode == "video":
        result = {
            "mode": "video",
            "output_directory": prepare_output_video_directory_name(
                args.source_path,
                args.selected_output_path,
                args.selected_ai_model,
                args.input_resize_factor,
                args.output_resize_factor,
                args.selected_blending_factor,
            ),
            "output_video": prepare_output_video_filename(
                args.source_path,
                args.selected_output_path,
                args.selected_ai_model,
                args.input_resize_factor,
                args.output_resize_factor,
                args.selected_video_extension,
                args.selected_blending_factor,
            ),
        }
    else:
        result = {
            "mode": "frame",
            "output": prepare_output_video_frame_filename(
                args.source_path,
                args.selected_ai_model,
                args.input_resize_factor,
                args.output_resize_factor,
                args.selected_blending_factor,
            ),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
