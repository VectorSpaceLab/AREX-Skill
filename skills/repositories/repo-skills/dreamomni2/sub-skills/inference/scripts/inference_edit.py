#!/usr/bin/env python3
"""DreamOmni2 two-image editing CLI."""

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
    parser = argparse.ArgumentParser(description="Run the DreamOmni2 editing workflow.")
    parser.add_argument(
        "--vlm-path",
        default="models/vlm-model",
        help="Path to the Qwen2.5-VL checkpoint directory or hub id.",
    )
    parser.add_argument(
        "--edit-lora-path",
        default="models/edit_lora",
        help="Path to the editing LoRA directory or hub id.",
    )
    parser.add_argument(
        "--base-model-path",
        default=DEFAULT_BASE_MODEL,
        help="DreamOmni2 base diffusion model directory or hub id.",
    )
    parser.add_argument(
        "--input_img_path",
        nargs=2,
        metavar=("SOURCE_IMAGE", "REFERENCE_IMAGE"),
        required=True,
        help="Source image first, reference image second.",
    )
    parser.add_argument(
        "--input_instruction",
        required=True,
        help="Editing instruction passed to the VLM prompt stage.",
    )
    parser.add_argument(
        "--output_path",
        default="dreamomni2_edit.png",
        help="Where to save the edited image.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = run_dreamomni2_workflow(
        mode="edit",
        image_paths=args.input_img_path,
        instruction=args.input_instruction,
        output_path=args.output_path,
        vlm_path=args.vlm_path,
        adapter_path=args.edit_lora_path,
        base_model_path=args.base_model_path,
    )
    print(f"saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
