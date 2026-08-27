#!/usr/bin/env python3
"""DreamOmni2 two-image generation CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dreamomni2_common import DEFAULT_BASE_MODEL, run_dreamomni2_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DreamOmni2 generation workflow.")
    parser.add_argument(
        "--vlm-path",
        default="models/vlm-model",
        help="Path to the Qwen2.5-VL checkpoint directory or hub id.",
    )
    parser.add_argument(
        "--gen-lora-path",
        default="models/gen_lora",
        help="Path to the generation LoRA directory or hub id.",
    )
    parser.add_argument(
        "--base-model-path",
        default=DEFAULT_BASE_MODEL,
        help="DreamOmni2 base diffusion model directory or hub id.",
    )
    parser.add_argument(
        "--input_img_path",
        nargs=2,
        metavar=("REFERENCE_IMAGE_1", "REFERENCE_IMAGE_2"),
        required=True,
        help="Two reference images used by the VLM prompt stage.",
    )
    parser.add_argument(
        "--input_instruction",
        required=True,
        help="Generation instruction passed to the VLM prompt stage.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help="Output height passed to the DreamOmni2 pipeline.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Output width passed to the DreamOmni2 pipeline.",
    )
    parser.add_argument(
        "--output_path",
        default="dreamomni2_gen.png",
        help="Where to save the generated image.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = run_dreamomni2_workflow(
        mode="generate",
        image_paths=args.input_img_path,
        instruction=args.input_instruction,
        output_path=args.output_path,
        vlm_path=args.vlm_path,
        adapter_path=args.gen_lora_path,
        base_model_path=args.base_model_path,
        height=args.height,
        width=args.width,
    )
    print(f"saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
