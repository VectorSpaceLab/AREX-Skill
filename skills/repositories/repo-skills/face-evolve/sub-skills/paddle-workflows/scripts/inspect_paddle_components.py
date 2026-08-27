#!/usr/bin/env python3
"""Safely inspect face.evoLVe Paddle components without shadowing PaddlePaddle.

This script imports the installed PaddlePaddle framework first, then imports the
repository's Paddle source modules from the checkout's paddle/ directory. It runs
only a tiny CPU backbone forward pass; it does not train, download data, export,
quantize, or run deployment demos.
"""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import re
import sys
import traceback
from typing import Iterable, List, Tuple


BACKBONES = (
    "ppResNet_50",
    "ResNet_50",
    "ResNet_101",
    "ResNet_152",
    "IR_50",
    "IR_101",
    "IR_152",
    "IR_SE_50",
    "IR_SE_101",
    "IR_SE_152",
)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _resolve_repo_and_paddle_src(repo_root_arg: str) -> Tuple[Path, Path]:
    repo_root = Path(repo_root_arg).expanduser().resolve()
    if (repo_root / "paddle" / "config.py").is_file() and (repo_root / "paddle" / "backbone").is_dir():
        paddle_src = repo_root / "paddle"
    elif repo_root.name == "paddle" and (repo_root / "config.py").is_file() and (repo_root / "backbone").is_dir():
        # Be forgiving if the user passed the checkout's paddle/ source directory.
        paddle_src = repo_root
        repo_root = repo_root.parent
    else:
        paddle_src = repo_root / "paddle"

    missing = []
    for relative in ("config.py", "backbone", "head", "loss"):
        if not (paddle_src / relative).exists():
            missing.append(str(paddle_src / relative))
    if missing:
        raise SystemExit(
            "The supplied --repo-root does not look like a face.evoLVe checkout "
            "with Paddle source modules. Missing: " + ", ".join(missing)
        )
    return repo_root, paddle_src


def _prune_shadowing_paths(repo_root: Path) -> None:
    """Remove sys.path entries that make repo_root/paddle shadow PaddlePaddle."""
    pruned: List[str] = []
    cwd = Path.cwd().resolve()
    for entry in sys.path:
        candidate = cwd if entry == "" else Path(entry).expanduser().resolve()
        if candidate == repo_root:
            continue
        pruned.append(entry)
    sys.path[:] = pruned


def _import_installed_paddle(repo_root: Path):
    _prune_shadowing_paths(repo_root)

    already = sys.modules.get("paddle")
    if already is not None:
        origin = getattr(already, "__file__", None)
        if origin and _is_relative_to(Path(origin), repo_root / "paddle"):
            raise RuntimeError(
                "A local face.evoLVe paddle/ module is already loaded as 'paddle'. "
                "Restart Python, unset PYTHONPATH entries pointing at the checkout root, "
                "and run this script directly."
            )

    paddle = importlib.import_module("paddle")
    origin = getattr(paddle, "__file__", None)
    if not hasattr(paddle, "__version__") or (origin and _is_relative_to(Path(origin), repo_root / "paddle")):
        raise RuntimeError(
            "import paddle did not resolve to the installed PaddlePaddle framework. "
            "Avoid running from the checkout root or putting the checkout root on PYTHONPATH."
        )
    return paddle


def _prepare_source_imports(paddle_src: Path) -> None:
    """Import source modules from paddle_src after framework paddle is loaded."""
    os.chdir(str(paddle_src))
    source = str(paddle_src)
    sys.path[:] = [p for p in sys.path if str(Path(p or os.getcwd()).resolve()) != source]
    sys.path.insert(0, source)


def _parse_input_size(value: str) -> List[int]:
    parts = [p for p in re.split(r"[^0-9]+", value) if p]
    if len(parts) == 1:
        size = [int(parts[0]), int(parts[0])]
    elif len(parts) == 2:
        size = [int(parts[0]), int(parts[1])]
    else:
        raise argparse.ArgumentTypeError("use 112, 224, 112x112, or 112,112")
    if size[0] != size[1] or size[0] not in (112, 224):
        raise argparse.ArgumentTypeError("face.evoLVe Paddle backbones expect 112x112 or 224x224")
    return size


def _build_backbone(name: str, input_size: List[int]):
    if name.startswith("IR"):
        module = importlib.import_module("backbone.model_irse")
        return getattr(module, name)(input_size)
    if name.startswith("ResNet"):
        module = importlib.import_module("backbone.model_resnet")
        return getattr(module, name)(input_size)
    if name == "ppResNet_50":
        module = importlib.import_module("backbone.resnet_pp")
        return module.ResNet(input_size=input_size, depth=50)
    raise ValueError(f"Unsupported backbone: {name}")


def _import_component_symbols() -> Tuple[List[str], List[str]]:
    head = importlib.import_module("head.metrics")
    loss = importlib.import_module("loss.focal")
    head_symbols = [
        name
        for name in ("Softmax", "ArcFace", "CosFace", "SphereFace", "Am_softmax")
        if hasattr(head, name)
    ]
    loss_symbols = [name for name in ("FocalLoss",) if hasattr(loss, name)]
    return head_symbols, loss_symbols


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect face.evoLVe PaddlePaddle components with a tiny CPU backbone forward pass."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a face.evoLVe checkout root. Passing its paddle/ source directory is also accepted.",
    )
    parser.add_argument("--backbone", default="IR_50", choices=BACKBONES, help="Paddle backbone constructor to inspect.")
    parser.add_argument(
        "--input-size",
        default="112",
        type=_parse_input_size,
        help="Input size as 112, 224, 112x112, or 112,112. Default: 112.",
    )
    parser.add_argument("--batch-size", default=2, type=int, help="Synthetic CPU batch size. Default: 2.")
    args = parser.parse_args(argv)

    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")

    try:
        repo_root, paddle_src = _resolve_repo_and_paddle_src(args.repo_root)
        framework = _import_installed_paddle(repo_root)
        _prepare_source_imports(paddle_src)
        framework.set_device("cpu")

        model = _build_backbone(args.backbone, args.input_size)
        model.eval()
        x = framework.zeros([args.batch_size, 3, args.input_size[0], args.input_size[1]], dtype="float32")
        with framework.no_grad():
            y = model(x)
        head_symbols, loss_symbols = _import_component_symbols()

        print("face.evoLVe Paddle component inspection")
        print(f"PaddlePaddle version: {framework.__version__}")
        print(f"Source import root: paddle/")
        print(f"Backbone: {args.backbone}")
        print(f"Input shape: {list(x.shape)}")
        print(f"Output shape: {list(y.shape)}")
        print("Head symbols imported: " + ", ".join(head_symbols))
        print("Loss symbols imported: " + ", ".join(loss_symbols))
        print("Status: ok")
        return 0
    except Exception as exc:  # pragma: no cover - exercised by CLI users
        print("face.evoLVe Paddle component inspection failed", file=sys.stderr)
        print(f"Error: {exc}", file=sys.stderr)
        if os.environ.get("FACE_EVOLVE_DEBUG"):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
