#!/usr/bin/env python3
"""Print a vLLM OpenAI-compatible serve command from common options."""

from __future__ import annotations

import argparse
import shlex


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def utilization(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("must be in the range (0, 1]")
    return parsed


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["vllm", "serve", args.model]
    if args.host:
        command.extend(["--host", args.host])
    if args.port is not None:
        command.extend(["--port", str(args.port)])
    if args.dtype:
        command.extend(["--dtype", args.dtype])
    if args.tensor_parallel_size is not None:
        command.extend(["--tensor-parallel-size", str(args.tensor_parallel_size)])
    if args.gpu_memory_utilization is not None:
        command.extend([
            "--gpu-memory-utilization",
            str(args.gpu_memory_utilization),
        ])
    if args.max_model_len is not None:
        command.extend(["--max-model-len", str(args.max_model_len)])
    if args.api_key:
        command.extend(["--api-key", args.api_key])
    if args.extra:
        command.extend(args.extra)
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a vllm serve command for OpenAI-compatible serving. "
            "The command is printed only; no server is started."
        )
    )
    parser.add_argument("--model", required=True, help="Model ID or local model path")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=positive_int, default=8000, help="Server port")
    parser.add_argument(
        "--dtype",
        default="auto",
        help="Model dtype to pass to vLLM, for example auto, float16, bfloat16",
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=positive_int,
        help="Number of GPUs for tensor parallelism",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=utilization,
        help="Fraction of GPU memory vLLM may use, for example 0.90",
    )
    parser.add_argument(
        "--max-model-len",
        type=positive_int,
        help="Maximum model context length to serve",
    )
    parser.add_argument(
        "--api-key",
        help="Optional local API token; avoid shell history for real secrets",
    )
    parser.add_argument(
        "--extra",
        nargs=argparse.REMAINDER,
        help="Additional vllm serve flags appended after --extra",
    )
    parser.add_argument(
        "--as-list",
        action="store_true",
        help="Print the argv list instead of a shell-quoted command",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = build_command(args)
    if args.as_list:
        print(command)
    else:
        print(shlex.join(command))


if __name__ == "__main__":
    main()
