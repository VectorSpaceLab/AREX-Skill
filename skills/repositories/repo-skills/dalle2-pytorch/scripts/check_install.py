#!/usr/bin/env python3
"""Cross-cutting DALLE2-pytorch install/import/CLI checks.

This script is safe by default: it does not instantiate CLIP adapters, download
weights, run training, or require a source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from importlib import metadata


PUBLIC_ATTRS = (
    "DALLE2",
    "DiffusionPriorNetwork",
    "DiffusionPrior",
    "Unet",
    "Decoder",
    "OpenAIClipAdapter",
    "OpenClipAdapter",
    "DecoderTrainer",
    "DiffusionPriorTrainer",
    "VQGanVAE",
)


def fail(message: str, hint: str | None = None) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT: {hint}", file=sys.stderr)
    raise SystemExit(1)


def version_of(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "not-installed"


def mode_imports(_: argparse.Namespace) -> None:
    try:
        import torch
        import torchvision
    except Exception as exc:
        fail(f"torch/torchvision import failed: {exc}", "Install a compatible torch and torchvision pair for CPU or the selected accelerator backend.")

    try:
        pkg = importlib.import_module("dalle2_pytorch")
    except Exception as exc:
        fail(f"dalle2_pytorch import failed: {exc}", "Install with `python -m pip install dalle2-pytorch`; if clip reports pkg_resources missing, install `setuptools<81`.")

    missing = [name for name in PUBLIC_ATTRS if not hasattr(pkg, name)]
    if missing:
        fail("missing expected public attributes: " + ", ".join(missing))

    print("OK imports")
    print(f"python={sys.version.split()[0]}")
    print(f"torch={torch.__version__}")
    print(f"torchvision={torchvision.__version__}")
    print(f"torch_cuda_available={torch.cuda.is_available()}")
    print(f"dalle2-pytorch={version_of('dalle2-pytorch')}")
    print("note=CLIP adapters were not instantiated and no model weights were downloaded")


def mode_metadata(_: argparse.Namespace) -> None:
    print(f"dalle2-pytorch={version_of('dalle2-pytorch')}")
    print(f"open-clip-torch={version_of('open-clip-torch')}")
    print(f"clip-anytorch={version_of('clip-anytorch')}")
    print(f"x-clip={version_of('x-clip')}")
    print(f"torch={version_of('torch')}")
    print(f"torchvision={version_of('torchvision')}")


def mode_cli_help(_: argparse.Namespace) -> None:
    dream = shutil.which("dream")
    if dream:
        cmd = [dream, "--help"]
    else:
        cmd = [sys.executable, "-c", "from dalle2_pytorch.cli import dream; dream.main(args=['--help'], prog_name='dream')"]
    completed = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        fail(f"dream help failed with status {completed.returncode}\n{output.strip()}")
    for token in ("--model", "--cond_scale", "TEXT"):
        if token not in output:
            fail(f"dream help did not include expected token {token!r}", "A different executable named dream may be shadowing the package CLI.")
    print("OK cli-help")
    print("command=dream --help")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe DALLE2-pytorch package checks.")
    parser.add_argument("--mode", choices=("imports", "metadata", "cli-help"), default="imports")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "imports":
        mode_imports(args)
    elif args.mode == "metadata":
        mode_metadata(args)
    elif args.mode == "cli-help":
        mode_cli_help(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
