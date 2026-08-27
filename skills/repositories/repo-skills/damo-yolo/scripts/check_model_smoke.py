#!/usr/bin/env python3
"""Quick DAMO-YOLO package/config/model smoke check for generated skills."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch

from damo.config.base import parse_config
from damo.detectors.detector import build_local_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a DAMO-YOLO model/config smoke check")
    parser.add_argument("--config", required=True, help="DAMO-YOLO Python config path")
    parser.add_argument("--workdir", default=".", help="Directory used to resolve relative paths inside the config")
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"), help="Device for model construction/optional forward")
    parser.add_argument("--size", type=int, default=64, help="Square synthetic input size for --forward")
    parser.add_argument("--forward", action="store_true", help="Run a synthetic zero-tensor forward pass")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workdir = Path(args.workdir).resolve()
    if not workdir.is_dir():
        raise SystemExit(f"ERROR: --workdir is not a directory: {workdir}")
    os.chdir(workdir)

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (workdir / config_path).resolve()
    if not config_path.exists():
        raise SystemExit(f"ERROR: config not found: {config_path}")

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("ERROR: --device cuda requested but torch.cuda.is_available() is false")

    cfg = parse_config(str(config_path))
    model = build_local_model(cfg, device)
    model.eval()

    result = {
        "config": str(config_path),
        "device": device,
        "package": "damo",
        "num_classes": cfg.model.head.get("num_classes") if hasattr(cfg.model.head, "get") else None,
        "train_ann": list(cfg.dataset.train_ann) if hasattr(cfg.dataset, "train_ann") else None,
        "val_ann": list(cfg.dataset.val_ann) if hasattr(cfg.dataset, "val_ann") else None,
        "class_count": len(cfg.dataset.class_names) if getattr(cfg.dataset, "class_names", None) else None,
        "forward": None,
    }

    if args.forward:
        if args.size <= 0:
            raise SystemExit("ERROR: --size must be positive")
        with torch.no_grad():
            x = torch.zeros(1, 3, args.size, args.size, device=device)
            out = model(x)
        result["forward"] = {
            "output_type": type(out).__name__,
            "length": len(out) if hasattr(out, "__len__") else None,
            "first_type": type(out[0]).__name__ if isinstance(out, (list, tuple)) and out else None,
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("OK: DAMO-YOLO config/model smoke passed")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
