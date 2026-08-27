#!/usr/bin/env python3
"""Print a safe Diffusers from_single_file loading skeleton."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote(value: str) -> str:
    return json.dumps(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a local/offline-safe Diffusers single-file loader skeleton.")
    parser.add_argument("--pipeline", default="StableDiffusionXLPipeline", help="Diffusers pipeline class name.")
    parser.add_argument("--checkpoint", required=True, help="Single-file checkpoint path or URL.")
    parser.add_argument("--config", help="Diffusers config repo id or local config directory. Recommended for offline loads.")
    parser.add_argument("--original-config", help="Legacy original YAML/config path. Do not combine with --config for model-level loads.")
    parser.add_argument("--controlnet", help="Optional local ControlNet directory/repo id to pass into ControlNet pipelines.")
    parser.add_argument("--torch-dtype", default="float16", choices=["float32", "float16", "bfloat16"], help="torch dtype name.")
    parser.add_argument("--device", default="cuda", help="Device string for pipeline.to(...).")
    parser.add_argument("--local-files-only", action="store_true", help="Include local_files_only=True.")
    parser.add_argument("--safety-checker-none", action="store_true", help="Pass safety_checker=None for pipelines that accept it.")
    args = parser.parse_args()

    if not VALID_NAME.match(args.pipeline):
        raise SystemExit("--pipeline must be a Python class name such as StableDiffusionXLPipeline")
    if args.config and args.original_config:
        raise SystemExit("Choose only one of --config or --original-config for this template.")

    checkpoint_path = Path(args.checkpoint).expanduser()
    if not (args.checkpoint.startswith("http://") or args.checkpoint.startswith("https://")) and not checkpoint_path.exists():
        raise SystemExit(f"Checkpoint path does not exist: {args.checkpoint}")
    if args.config and "/" not in args.config:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            raise SystemExit(f"Config path does not exist: {args.config}")
    if args.controlnet and "/" not in args.controlnet:
        controlnet_path = Path(args.controlnet).expanduser()
        if not controlnet_path.exists():
            raise SystemExit(f"ControlNet path does not exist: {args.controlnet}")

    imports = ["import torch", f"from diffusers import {args.pipeline}"]
    if args.controlnet:
        imports.append("from diffusers import ControlNetModel")

    lines = [*imports, ""]
    if args.controlnet:
        lines.extend(
            [
                "controlnet = ControlNetModel.from_pretrained(",
                f"    {quote(args.controlnet)},",
                f"    torch_dtype=torch.{args.torch_dtype},",
            ]
        )
        if args.local_files_only:
            lines.append("    local_files_only=True,")
        lines.extend([")", ""])

    lines.extend(
        [
            f"pipe = {args.pipeline}.from_single_file(",
            f"    {quote(args.checkpoint)},",
            f"    torch_dtype=torch.{args.torch_dtype},",
        ]
    )
    if args.config:
        lines.append(f"    config={quote(args.config)},")
    if args.original_config:
        lines.append(f"    original_config={quote(args.original_config)},")
    if args.controlnet:
        lines.append("    controlnet=controlnet,")
    if args.safety_checker_none:
        lines.append("    safety_checker=None,")
    if args.local_files_only:
        lines.append("    local_files_only=True,")
    lines.extend([")", f"pipe = pipe.to({quote(args.device)})", ""])

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
