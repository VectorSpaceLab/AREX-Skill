#!/usr/bin/env python3
"""Validate OpenFlamingo generation prompt/media invariants without downloads.

This script intentionally uses only the Python standard library. It does not
import torch, transformers, open_clip, or open_flamingo.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

IMAGE_TOKEN = "<image>"
EOC_TOKEN = "<|endofchunk|>"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate OpenFlamingo vision_x dimensions and prompt media tokens "
            "before running model generation. No downloads or package imports."
        )
    )
    parser.add_argument("--batch-size", default=1, type=int, help="Batch size B. Default: 1")
    parser.add_argument(
        "--num-media",
        default=1,
        type=int,
        help="Number of media/image slots T_img per prompt example. Default: 1",
    )
    parser.add_argument(
        "--num-frames",
        default=1,
        type=int,
        help="Number of frames F per media item. OpenFlamingo requires F=1. Default: 1",
    )
    parser.add_argument("--channels", default=3, type=int, help="Image channels C. Default: 3")
    parser.add_argument("--height", default=224, type=int, help="Preprocessed image height H. Default: 224")
    parser.add_argument("--width", default=224, type=int, help="Preprocessed image width W. Default: 224")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt text containing exact OpenFlamingo <image> markers.",
    )
    return parser


def _add_error(errors: List[Dict[str, str]], code: str, message: str, fix: str) -> None:
    errors.append({"code": code, "message": message, "fix": fix})


def _add_warning(warnings: List[Dict[str, str]], code: str, message: str, fix: str) -> None:
    warnings.append({"code": code, "message": message, "fix": fix})


def validate(args: argparse.Namespace) -> Dict[str, Any]:
    dims = {
        "batch_size_B": args.batch_size,
        "num_media_T_img": args.num_media,
        "num_frames_F": args.num_frames,
        "channels_C": args.channels,
        "height_H": args.height,
        "width_W": args.width,
    }
    shape = [
        args.batch_size,
        args.num_media,
        args.num_frames,
        args.channels,
        args.height,
        args.width,
    ]
    prompt = args.prompt
    image_count = prompt.count(IMAGE_TOKEN)
    eoc_count = prompt.count(EOC_TOKEN)

    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    cli_options = {
        "batch_size_B": "--batch-size",
        "num_media_T_img": "--num-media",
        "num_frames_F": "--num-frames",
        "channels_C": "--channels",
        "height_H": "--height",
        "width_W": "--width",
    }
    for name, value in dims.items():
        if value <= 0:
            _add_error(
                errors,
                "non_positive_dimension",
                f"{name} must be a positive integer, got {value}.",
                f"Pass a positive value for {cli_options[name]} or rebuild the tensor shape.",
            )

    if args.num_frames != 1:
        _add_error(
            errors,
            "unsupported_num_frames",
            f"OpenFlamingo expects F=1 but received F={args.num_frames}.",
            "Use --num-frames 1; this OpenFlamingo path supports single-frame media only.",
        )

    if image_count == 0:
        _add_error(
            errors,
            "missing_image_token",
            f"Prompt contains no exact {IMAGE_TOKEN} token.",
            f"Insert one {IMAGE_TOKEN} marker for each media item in the same example.",
        )

    if args.num_media > 0 and image_count != args.num_media:
        _add_error(
            errors,
            "image_token_media_mismatch",
            f"Prompt has {image_count} {IMAGE_TOKEN} token(s), but --num-media is {args.num_media}.",
            "Make the prompt marker count equal T_img, or validate each batched example separately.",
        )

    if args.channels != 3:
        _add_warning(
            warnings,
            "unusual_channel_count",
            f"C={args.channels}; OpenCLIP image processors normally produce RGB tensors with C=3.",
            "Convert images to RGB before preprocessing unless using a custom compatible vision encoder.",
        )

    if image_count > 1 and eoc_count < image_count - 1:
        _add_warning(
            warnings,
            "few_eoc_markers",
            (
                f"Prompt has {image_count} image markers but only {eoc_count} {EOC_TOKEN} marker(s). "
                "Completed demonstrations are usually separated by end-of-chunk tokens."
            ),
            f"Add {EOC_TOKEN} after each completed in-context image/text example; the final query may remain open.",
        )

    if prompt.rstrip().endswith(IMAGE_TOKEN):
        _add_warning(
            warnings,
            "prompt_ends_with_image_token",
            "Prompt ends immediately after an <image> token, leaving no textual query prefix.",
            "Append a task prefix such as 'An image of' or 'Question:... Short answer:'.",
        )

    if args.batch_size > 1:
        _add_warning(
            warnings,
            "single_prompt_for_batch",
            "The validator receives one prompt string but --batch-size is greater than 1.",
            "Run once per unique prompt/media count, or ensure every batch item has the same token/media contract.",
        )

    estimated_values = None
    if all(value > 0 for value in shape):
        estimated_values = 1
        for value in shape:
            estimated_values *= value
        if estimated_values > 50_000_000:
            _add_warning(
                warnings,
                "large_vision_tensor",
                f"The implied vision tensor contains {estimated_values} scalar values before dtype bytes.",
                "Confirm memory budget before running full model generation.",
            )

    ok = not errors
    result: Dict[str, Any] = {
        "ok": ok,
        "exit_code": 0 if ok else 1,
        "shape_contract": "B x T_img x F x C x H x W",
        "vision_x_shape": shape,
        "dimensions": dims,
        "tokens": {
            "image_token": IMAGE_TOKEN,
            "image_token_count": image_count,
            "endofchunk_token": EOC_TOKEN,
            "endofchunk_token_count": eoc_count,
        },
        "errors": errors,
        "warnings": warnings,
        "next_steps": [],
    }

    if ok:
        result["next_steps"].append(
            "Build vision_x with shape B x T_img x 1 x C x H x W and tokenize the prompt with tokenizer.padding_side='left'."
        )
        result["next_steps"].append(
            "Pass vision_x, lang_x, and attention_mask to model.generate(); do not pre-repeat vision_x for beams."
        )
    else:
        result["next_steps"].append("Fix the listed errors before importing or running OpenFlamingo generation.")
        result["next_steps"].append(
            f"At minimum, use --num-frames 1 and include one exact {IMAGE_TOKEN} token per media item."
        )

    if estimated_values is not None:
        result["estimated_vision_scalar_values"] = estimated_values

    return result


def main(argv: List[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    result = validate(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
