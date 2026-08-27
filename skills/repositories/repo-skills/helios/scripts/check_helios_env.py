#!/usr/bin/env python3
"""Check the installed environment for the Helios workflows.

This is a read-only smoke check. It reports the package versions that matter
for the bundled Helios workflows and verifies that CUDA is visible.
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
from typing import Iterable


REQUIRED_PACKAGES = [
    ("torch", "torch"),
    ("diffusers", "diffusers"),
    ("transformers", "transformers"),
    ("accelerate", "accelerate"),
    ("peft", "peft"),
    ("omegaconf", "omegaconf"),
    ("kernels", "kernels"),
    ("imageio-ffmpeg", "imageio_ffmpeg"),
]

OPTIONAL_PACKAGES = [
    ("gradio", "gradio"),
    ("spaces", "spaces"),
    ("moviepy", "moviepy"),
]


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except Exception:
        return "missing"


def importable(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def check_cuda() -> list[str]:
    messages: list[str] = []
    try:
        import torch
    except Exception as exc:
        return [f"torch import failed: {exc}"]

    messages.append(f"torch.version={getattr(torch, '__version__', 'unknown')}")
    messages.append(f"cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        messages.append(f"device_count={torch.cuda.device_count()}")
        try:
            messages.append(f"capability={torch.cuda.get_device_capability()}")
        except Exception as exc:
            messages.append(f"capability=unavailable ({exc})")
    return messages


def check_diffusers_symbols() -> list[str]:
    needed = ["AutoencoderKLWan", "HeliosPyramidPipeline", "HeliosDMDScheduler", "ContextParallelConfig"]
    try:
        import diffusers
    except Exception as exc:
        return [f"diffusers import failed: {exc}"]

    found = []
    for name in needed:
        found.append(f"{name}={'yes' if hasattr(diffusers, name) else 'no'}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Helios inspection environment")
    parser.add_argument(
        "--check-demo",
        action="store_true",
        help="Also report whether the optional source/demo packages are importable.",
    )
    args = parser.parse_args()

    print("Helios environment check")
    print("========================")

    all_ok = True
    print("\nRequired packages:")
    for dist_name, import_name in REQUIRED_PACKAGES:
        version = package_version(dist_name)
        ok = importable(import_name)
        print(f"- {dist_name}: {version} {'(import ok)' if ok else '(import failed)'}")
        all_ok &= ok

    print("\nCUDA/backend:")
    for line in check_cuda():
        print(f"- {line}")
    try:
        import torch
        all_ok &= torch.cuda.is_available()
    except Exception:
        all_ok = False

    print("\nHelios-facing diffusers symbols:")
    for line in check_diffusers_symbols():
        print(f"- {line}")

    print("\nNote: this script does not fetch flash-attention kernel variants. If local Helios kernel imports fail, align the torch/CUDA wheel with a supported kernels build.")

    if args.check_demo:
        print("\nAdditional packages:")
        for dist_name, import_name in OPTIONAL_PACKAGES:
            version = package_version(dist_name)
            ok = importable(import_name)
            print(f"- {dist_name}: {version} {'(import ok)' if ok else '(import failed)'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
