#!/usr/bin/env python3
"""Verify that the NanoDet package and its common optional dependencies import.

Usage:
    python check_install.py
    python check_install.py --config path/to/config.yml
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the NanoDet installation.")
    parser.add_argument(
        "--config",
        help="Optional NanoDet config path to build as an additional smoke check.",
    )
    return parser.parse_args()


def show_module(name: str) -> None:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f"{name}: missing ({exc})")
        return
    version = getattr(module, "__version__", "unknown")
    print(f"{name}: ok ({version})")


def main() -> int:
    args = parse_args()

    print("nanodet version:", metadata.version("nanodet"))
    show_module("nanodet")
    show_module("torch")
    show_module("torchvision")
    show_module("pytorch_lightning")
    show_module("timm")
    show_module("onnx")
    show_module("onnxsim")
    show_module("pycocotools")
    show_module("cv2")

    if args.config:
        from nanodet.model.arch import build_model
        from nanodet.util import cfg, load_config

        config_path = Path(args.config).expanduser().resolve()
        load_config(cfg, str(config_path))
        model = build_model(cfg.model)
        print(f"built model: {type(model).__name__}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
