#!/usr/bin/env python3
"""Check that a YOLOP checkout can be imported and can build/run the model.

Example:
  python check_install.py --repo-root /path/to/YOLOP --device cpu --image-size 128

The script is safe by default: it uses a dummy tensor, does not download data,
does not run training, and only loads a checkpoint when --checkpoint is passed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _shape(value: Any) -> Any:
    if hasattr(value, "shape"):
        return list(value.shape)
    if isinstance(value, (list, tuple)):
        return [_shape(v) for v in value]
    return type(value).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOP source import and model smoke check")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout containing lib/")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, or another torch device")
    parser.add_argument("--image-size", type=int, default=128, help="Square dummy image size; use a multiple of 32")
    parser.add_argument("--checkpoint", help="Optional YOLOP .pth checkpoint to load before the forward smoke")
    parser.add_argument("--skip-forward", action="store_true", help="Only import modules and build the model")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON summary")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "lib" / "models" / "YOLOP.py").is_file():
        print(f"ERROR: {repo_root} does not look like a YOLOP checkout with lib/models/YOLOP.py", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))

    summary: dict[str, Any] = {"repo_root_ok": True, "repo_root": str(repo_root)}
    try:
        import torch
        import torchvision
        from lib.config import cfg
        from lib.models import get_net
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"ERROR: failed to import YOLOP dependencies: {exc}", file=sys.stderr)
        return 3

    summary.update(
        {
            "torch": getattr(torch, "__version__", "unknown"),
            "torchvision": getattr(torchvision, "__version__", "unknown"),
            "cuda_available": bool(torch.cuda.is_available()),
            "cfg_dataset": str(cfg.DATASET.DATASET),
            "cfg_image_size": list(cfg.MODEL.IMAGE_SIZE),
        }
    )

    device_name = args.device
    if device_name != "cpu" and device_name.startswith("cuda") and not torch.cuda.is_available():
        print("ERROR: CUDA device requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 4
    device = torch.device(device_name)

    model = get_net(cfg).to(device)
    model.eval()
    summary["model_class"] = type(model).__name__
    summary["names"] = list(getattr(model, "names", []))

    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint).expanduser().resolve()
        if not checkpoint_path.is_file():
            print(f"ERROR: checkpoint does not exist: {checkpoint_path}", file=sys.stderr)
            return 5
        checkpoint = torch.load(str(checkpoint_path), map_location=device)
        state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        summary["checkpoint_loaded"] = str(checkpoint_path)
        summary["checkpoint_missing_keys"] = list(missing)
        summary["checkpoint_unexpected_keys"] = list(unexpected)

    if not args.skip_forward:
        size = int(args.image_size)
        if size <= 0 or size % 32 != 0:
            print("ERROR: --image-size must be a positive multiple of 32", file=sys.stderr)
            return 6
        with torch.no_grad():
            dummy = torch.zeros(1, 3, size, size, device=device)
            output = model(dummy)
        summary["forward_output_shape"] = _shape(output)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("YOLOP import/model smoke passed")
        for key, value in summary.items():
            if key != "repo_root":
                print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
