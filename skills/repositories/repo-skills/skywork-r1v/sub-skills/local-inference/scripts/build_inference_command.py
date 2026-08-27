#!/usr/bin/env python3
"""Build safe Skywork-R1V3 local inference commands.

This helper prints a deterministic command for the native Transformers or vLLM
entrypoint. It does not import torch, transformers, vLLM, PIL, or load images.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional

DEFAULT_MODEL = "Skywork/Skywork-R1V3-38B"


def _flatten_image_paths(groups: Optional[List[List[str]]]) -> List[str]:
    if not groups:
        return []
    flattened: List[str] = []
    for group in groups:
        flattened.extend(group)
    return flattened


def _float_text(value: float) -> str:
    """Return a stable Python-like float representation for CLI output."""
    return repr(float(value))


def _positive_int(name: str, value: int) -> int:
    if value < 1:
        raise argparse.ArgumentTypeError(f"{name} must be >= 1")
    return value


def _tensor_parallel(value: str) -> int:
    return _positive_int("--tensor-parallel-size", int(value))


def _max_tokens(value: str) -> int:
    return _positive_int("--max-tokens", int(value))


def build_command(args: argparse.Namespace) -> List[str]:
    image_paths = _flatten_image_paths(args.image_paths)
    if not image_paths:
        raise ValueError("At least one --image-path value is required")

    if args.backend == "transformers":
        return [
            "python",
            "inference_with_transformers.py",
            "--model_path",
            args.model_path,
            "--image_paths",
            *image_paths,
            "--question",
            args.question,
        ]

    temperature = 0.0 if args.temperature is None else args.temperature
    max_tokens = 8000 if args.max_tokens is None else args.max_tokens
    repetition_penalty = 1.05 if args.repetition_penalty is None else args.repetition_penalty
    top_p = 0.95 if args.top_p is None else args.top_p

    return [
        "python",
        "inference_with_vllm.py",
        "--model_path",
        args.model_path,
        "--image_paths",
        *image_paths,
        "--question",
        args.question,
        "--tensor_parallel_size",
        str(args.tensor_parallel_size),
        "--temperature",
        _float_text(temperature),
        "--max_tokens",
        str(max_tokens),
        "--repetition_penalty",
        _float_text(repetition_penalty),
        "--top_p",
        _float_text(top_p),
    ]


def print_prereqs(args: argparse.Namespace, image_paths: Iterable[str]) -> None:
    image_count = len(list(image_paths))
    print("# Prerequisites:")
    print("# - Run the generated command only in a prepared local inference environment.")
    print("# - Replace the script name if your native or adapted entrypoint lives elsewhere.")
    print(f"# - Model path/id: {args.model_path}")
    print(f"# - Image count: {image_count}; ensure prompt image tags match the backend behavior.")
    print("# - Full Skywork-R1V3-38B inference requires CUDA GPUs and large model weights; there is no CPU fallback in the native scripts.")
    if args.backend == "transformers":
        print("# - Transformers native load uses bfloat16, flash-attn, trust_remote_code=True, split_model(), and model.chat().")
        print("# - Native generation is hard-coded: max_new_tokens=64000, temperature=0.6, top_p=0.95, repetition_penalty=1.05.")
    else:
        print(f"# - vLLM tensor_parallel_size={args.tensor_parallel_size}; native initialization uses trust_remote_code=True, limit_mm_per_prompt image=20, gpu_memory_utilization=0.7.")
        print("# - vLLM sampling defaults are temperature=0.0, max_tokens=8000, repetition_penalty=1.05, top_p=0.95 unless overridden.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe command for Skywork-R1V3 local inference without loading models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--backend",
        choices=("transformers", "vllm"),
        required=True,
        help="Inference backend command to build.",
    )
    parser.add_argument(
        "--model-path",
        default=DEFAULT_MODEL,
        help="Model id or local checkpoint path to pass as --model_path.",
    )
    parser.add_argument(
        "--image-path",
        "--image-paths",
        dest="image_paths",
        action="append",
        nargs="+",
        required=True,
        help="Input image path(s). May be repeated or followed by multiple values.",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Question text to pass to the native inference entrypoint.",
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=_tensor_parallel,
        default=4,
        help="vLLM tensor parallel GPU count.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="vLLM sampling temperature. Transformers native CLI does not expose this flag.",
    )
    parser.add_argument(
        "--max-tokens",
        type=_max_tokens,
        default=None,
        help="vLLM max generated tokens. Transformers native max_new_tokens is hard-coded.",
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=None,
        help="vLLM repetition penalty. Transformers native value is hard-coded.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="vLLM nucleus sampling probability. Transformers native value is hard-coded.",
    )
    parser.add_argument(
        "--print-prereqs",
        action="store_true",
        help="Print a concise prerequisites checklist before the command.",
    )
    args = parser.parse_args(argv)
    args.model_path = args.model_path.strip()
    if not args.model_path:
        parser.error("--model-path must not be empty")
    if not args.question:
        parser.error("--question must not be empty")
    if args.backend == "transformers" and any(
        value is not None
        for value in (args.temperature, args.max_tokens, args.repetition_penalty, args.top_p)
    ):
        parser.error(
            "sampling overrides are only emitted for --backend vllm; "
            "the native Transformers CLI uses hard-coded generation values"
        )
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    image_paths = _flatten_image_paths(args.image_paths)
    try:
        command = build_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.print_prereqs:
        print_prereqs(args, image_paths)
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
