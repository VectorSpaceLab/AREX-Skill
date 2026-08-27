#!/usr/bin/env python3
"""Validated wrapper for composing FLUX LoRAs with Nunchaku."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from nunchaku.lora.flux.compose import compose_lora


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compose FLUX LoRA safetensors with per-LoRA strengths by calling "
            "nunchaku.lora.flux.compose.compose_lora."
        )
    )
    parser.add_argument(
        "-i",
        "--input-paths",
        nargs="+",
        required=True,
        help="LoRA safetensors paths or Hugging Face repo/file specs. Provide one strength per input.",
    )
    parser.add_argument(
        "-s",
        "--strengths",
        nargs="+",
        type=float,
        required=True,
        help="Strength values to apply to the corresponding input LoRAs.",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        required=True,
        help="Destination safetensors path for the composed LoRA.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if len(args.input_paths) != len(args.strengths):
        parser.error(
            "--input-paths and --strengths must have the same length "
            f"(got {len(args.input_paths)} paths and {len(args.strengths)} strengths)."
        )

    bad_strengths = [value for value in args.strengths if not math.isfinite(value)]
    if bad_strengths:
        parser.error(f"all strengths must be finite floats; invalid values: {bad_strengths!r}")

    output_path = Path(args.output_path)
    if output_path.exists() and not args.overwrite:
        parser.error(f"output path already exists: {output_path}. Use --overwrite to replace it.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    loras = list(zip(args.input_paths, args.strengths))
    compose_lora(loras, output_path=str(output_path))
    print(f"Composed {len(loras)} LoRA(s) into {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
