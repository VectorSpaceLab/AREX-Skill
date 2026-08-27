#!/usr/bin/env python3
"""Validate chest-X-ray tool arguments without importing model packages.

This helper only checks local paths, suffixes, and scalar/list schemas. It never
opens image contents, downloads resources, loads model weights, or runs inference.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ORGANS = {
    "Left Clavicle",
    "Right Clavicle",
    "Left Scapula",
    "Right Scapula",
    "Left Lung",
    "Right Lung",
    "Left Hilus Pulmonis",
    "Right Hilus Pulmonis",
    "Heart",
    "Aorta",
    "Facies Diaphragmatica",
    "Mediastinum",
    "Weasand",
    "Spine",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--tool",
        required=True,
        choices=("classifier", "segmentation", "report", "vqa", "grounding", "llava", "generation"),
    )
    p.add_argument("--image-path", action="append", default=[], help="Image path; repeat for VQA")
    p.add_argument("--prompt", help="VQA or generation prompt")
    p.add_argument("--question", help="LLaVA-Med question")
    p.add_argument("--phrase", help="MAIRA-2 phrase to ground")
    p.add_argument("--organ", action="append", default=[], help="Segmentation organ; repeat as needed")
    p.add_argument("--max-new-tokens", type=int, default=None)
    p.add_argument("--height", type=int, default=512)
    p.add_argument("--width", type=int, default=512)
    p.add_argument("--num-inference-steps", type=int, default=75)
    p.add_argument("--guidance-scale", type=float, default=4.0)
    return p


def require_text(errors: list[str], value: str | None, field: str) -> None:
    if value is None or not value.strip():
        errors.append(f"{field} must be non-empty")


def validate(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    images = [Path(value) for value in args.image_path]
    image_required = args.tool in {"classifier", "segmentation", "report", "grounding", "vqa"}
    if image_required and not images:
        errors.append("at least one --image-path is required")
    if args.tool in {"classifier", "segmentation", "report", "grounding"} and len(images) > 1:
        errors.append(f"{args.tool} accepts exactly one --image-path")
    if args.tool == "llava" and len(images) > 1:
        errors.append("llava accepts at most one --image-path")

    for image in images:
        if not image.is_file():
            errors.append(f"image is not a regular file: {image}")
        elif image.suffix.lower() not in IMAGE_SUFFIXES:
            errors.append(f"unsupported image suffix for {image}; use JPG or PNG")

    if args.tool == "segmentation":
        invalid = [organ for organ in args.organ if organ not in ORGANS]
        if invalid:
            errors.append(f"invalid organs: {invalid}")
    if args.tool == "vqa":
        require_text(errors, args.prompt, "--prompt")
        if args.max_new_tokens is not None and args.max_new_tokens <= 0:
            errors.append("--max-new-tokens must be positive")
    if args.tool == "grounding":
        require_text(errors, args.phrase, "--phrase")
        if args.max_new_tokens is not None and args.max_new_tokens <= 0:
            errors.append("--max-new-tokens must be positive")
    if args.tool == "llava":
        require_text(errors, args.question, "--question")
    if args.tool == "generation":
        require_text(errors, args.prompt, "--prompt")
        if args.height <= 0 or args.width <= 0:
            errors.append("--height and --width must be positive")
        if args.num_inference_steps <= 0:
            errors.append("--num-inference-steps must be positive")
        if args.guidance_scale < 0:
            errors.append("--guidance-scale must be non-negative")

    checked: dict[str, Any] = {
        "tool": args.tool,
        "image_paths": [str(path) for path in images],
        "organs": args.organ,
    }
    for name in ("prompt", "question", "phrase"):
        value = getattr(args, name)
        if value is not None:
            checked[name] = value
    if args.max_new_tokens is not None:
        checked["max_new_tokens"] = args.max_new_tokens
    if args.tool == "generation":
        checked.update(
            {
                "height": args.height,
                "width": args.width,
                "num_inference_steps": args.num_inference_steps,
                "guidance_scale": args.guidance_scale,
            }
        )
    return checked, errors


def main() -> int:
    args = parser().parse_args()
    checked, errors = validate(args)
    result = {"valid": not errors, **checked}
    if errors:
        result["errors"] = errors
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
