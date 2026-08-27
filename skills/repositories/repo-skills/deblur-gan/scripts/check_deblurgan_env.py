#!/usr/bin/env python3
"""Check the DeblurGAN environment and public module surface.

This script is safe to run from a DeblurGAN checkout or any working directory
that can point at one with --repo-root. It performs import-only checks unless
--cuda is requested.
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import inspect
import sys
from pathlib import Path


MODULES = [
    "options.base_options",
    "options.train_options",
    "options.test_options",
    "data.data_loader",
    "data.image_folder",
    "models.models",
    "models.networks",
    "models.losses",
    "models.test_model",
    "util.metrics",
    "util.visualizer",
    "util.html",
]


def metadata_version(name: str) -> str:
    try:
        return md.version(name)
    except Exception as exc:  # pragma: no cover - defensive for optional extras
        return f"unavailable ({type(exc).__name__})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the DeblurGAN runtime environment")
    parser.add_argument("--repo-root", required=True, help="Path to the DeblurGAN checkout")
    parser.add_argument("--cuda", action="store_true", help="Require a working CUDA tensor smoke")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"repo root is not a directory: {repo_root}")

    sys.path.insert(0, str(repo_root))

    import torch
    import torchvision

    print("python", sys.version.replace("\n", " "))
    print("torch", torch.__version__, torch.version.cuda, torch.cuda.is_available())
    print("torchvision", torchvision.__version__)
    print("dominate", metadata_version("dominate"))
    print("opencv-python-headless", metadata_version("opencv-python-headless"))
    print("ssim", metadata_version("ssim"))

    for module_name in MODULES:
        module = __import__(module_name, fromlist=["*"])
        print("imported", module_name, getattr(module, "__file__", "<builtin>"))

    from options.base_options import BaseOptions
    from data.data_loader import CreateDataLoader
    from data.custom_dataset_data_loader import CreateDataset
    from models.models import create_model
    from models.networks import define_G, define_D
    from models.losses import init_loss
    from util.metrics import PSNR, SSIM
    from util.visualizer import Visualizer
    from util.html import HTML

    print("BaseOptions.parse", inspect.signature(BaseOptions.parse))
    print("CreateDataLoader", inspect.signature(CreateDataLoader))
    print("CreateDataset", inspect.signature(CreateDataset))
    print("create_model", inspect.signature(create_model))
    print("define_G", inspect.signature(define_G))
    print("define_D", inspect.signature(define_D))
    print("init_loss", inspect.signature(init_loss))
    print("PSNR", inspect.signature(PSNR))
    print("SSIM", inspect.signature(SSIM))
    print("Visualizer", inspect.signature(Visualizer))
    print("HTML", inspect.signature(HTML))

    if args.cuda:
        if not torch.cuda.is_available():
            raise SystemExit("CUDA requested but torch.cuda.is_available() is false")
        x = torch.empty((1,), device="cuda")
        print("cuda_tensor", x.device)
        print("cuda_device_count", torch.cuda.device_count())
        print("cuda_device_name", torch.cuda.get_device_name(0))
        print("cuda_capability", torch.cuda.get_device_capability(0))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
