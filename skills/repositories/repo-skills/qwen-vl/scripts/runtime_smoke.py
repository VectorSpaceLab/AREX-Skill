#!/usr/bin/env python3
"""Print a small Qwen-VL runtime smoke report.

This helper is safe: it only imports packages, prints versions, and optionally
checks that a tiny CUDA tensor allocation works.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version


def _print_version(name: str) -> None:
    try:
        print(f"{name}={version(name)}")
    except PackageNotFoundError:
        print(f"{name}=MISSING")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cuda", action="store_true", help="Allocate one tiny CUDA tensor and print device info")
    parser.add_argument(
        "--import",
        dest="imports",
        action="append",
        default=[],
        help="Import one module and print its __file__ if import succeeds. May be given multiple times.",
    )
    args = parser.parse_args()

    for name in [
        "torch",
        "torchvision",
        "transformers",
        "accelerate",
        "gradio",
        "modelscope",
        "fastapi",
        "uvicorn",
        "openai",
        "pydantic",
        "sse-starlette",
        "deepspeed",
        "peft",
        "pycocotools",
        "pycocoevalcap",
        "av",
    ]:
        _print_version(name)

    if args.imports:
        for module_name in args.imports:
            module = __import__(module_name)
            print(f"{module_name} -> {getattr(module, '__file__', 'built-in')}")

    if args.check_cuda:
        import torch

        print(f"cuda_available={torch.cuda.is_available()}")
        print(f"cuda_count={torch.cuda.device_count()}")
        if torch.cuda.is_available():
            print(f"cuda_name={torch.cuda.get_device_name(0)}")
            print(f"cuda_capability={torch.cuda.get_device_capability(0)}")
            tensor = torch.empty((1,), device="cuda")
            print(f"tiny_tensor={tensor.device}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
