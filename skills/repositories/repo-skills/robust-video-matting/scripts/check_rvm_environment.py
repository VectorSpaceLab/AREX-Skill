#!/usr/bin/env python3
"""Check that a Python environment can import and smoke-test RobustVideoMatting.

This helper is safe by default: it performs imports and a tiny synthetic forward
pass only. If the repository source is not importable as ``model`` and
``inference``, pass ``--repo-root`` pointing at a local RobustVideoMatting
checkout.

Examples:
  python check_rvm_environment.py --repo-root /path/to/RobustVideoMatting
  python check_rvm_environment.py --repo-root /path/to/RobustVideoMatting --device auto
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    sys.path.insert(0, str(root))


def _import_module(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check RobustVideoMatting imports and a tiny model forward pass.")
    parser.add_argument("--repo-root", help="Optional local RobustVideoMatting checkout to add to sys.path for source imports.")
    parser.add_argument("--variant", default="mobilenetv3", choices=["mobilenetv3", "resnet50"], help="MattingNetwork variant to instantiate.")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"], help="Device for the tiny forward pass.")
    parser.add_argument("--height", type=int, default=32, help="Synthetic input height.")
    parser.add_argument("--width", type=int, default=32, help="Synthetic input width.")
    parser.add_argument("--downsample-ratio", type=float, default=0.5, help="Forward-pass downsample_ratio.")
    parser.add_argument("--skip-forward", action="store_true", help="Only check imports and signatures.")
    args = parser.parse_args()

    _add_repo_root(args.repo_root)

    results: dict[str, Any] = {"imports": [], "forward": None, "warnings": []}
    required = ["torch", "torchvision", "PIL", "tqdm", "model", "inference"]
    optional = ["av", "pims", "cv2", "xlsxwriter", "kornia", "easing_functions", "tensorboard"]
    for name in required + optional:
        info = _import_module(name)
        info["required"] = name in required
        results["imports"].append(info)

    failed_required = [m for m in results["imports"] if m["required"] and not m["ok"]]
    if failed_required:
        print(json.dumps(results, indent=2, sort_keys=True))
        print("Required imports failed. If model/inference failed, retry with --repo-root.", file=sys.stderr)
        return 2

    import inspect
    import torch
    from model import MattingNetwork
    from inference import convert_video

    results["signatures"] = {
        "MattingNetwork.__init__": str(inspect.signature(MattingNetwork)),
        "MattingNetwork.forward": str(inspect.signature(MattingNetwork.forward)),
        "convert_video": str(inspect.signature(convert_video)),
    }
    results["torch"] = {
        "version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print(json.dumps(results, indent=2, sort_keys=True))
        print("CUDA was requested but torch.cuda.is_available() is false.", file=sys.stderr)
        return 3

    if not args.skip_forward:
        if args.height < 8 or args.width < 8:
            raise SystemExit("Synthetic height/width should be at least 8 for the model smoke test.")
        model = MattingNetwork(args.variant).eval().to(device)
        with torch.no_grad():
            src = torch.rand(1, 3, args.height, args.width, device=device)
            fgr, pha, *rec = model(src, None, None, None, None, args.downsample_ratio)
        results["forward"] = {
            "device": device,
            "variant": args.variant,
            "input_shape": list(src.shape),
            "fgr_shape": list(fgr.shape),
            "pha_shape": list(pha.shape),
            "rec_shapes": [list(r.shape) for r in rec],
            "fgr_range": [float(fgr.min().item()), float(fgr.max().item())],
            "pha_range": [float(pha.min().item()), float(pha.max().item())],
        }

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
