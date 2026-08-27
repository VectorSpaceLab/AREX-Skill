#!/usr/bin/env python3
"""Probe a YOLOv3 model YAML and print architecture/runtime facts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Instantiate a YOLOv3 YAML and run an optional zero-tensor forward.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--cfg", default="models/yolov3-tiny.yaml")
    parser.add_argument("--imgsz", type=int, default=64)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-forward", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    cfg = Path(args.cfg)
    cfg = cfg if cfg.is_absolute() else repo_root / cfg
    if not (repo_root / "models" / "yolo.py").exists() or not cfg.exists():
        print("missing repo model files or cfg", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))
    import torch
    from models.yolo import Model

    model = Model(str(cfg)).to(args.device).eval()
    detect = model.model[-1]
    result = {
        "status": "PASS",
        "cfg": str(cfg),
        "layers": len(model.model),
        "classes": int(detect.nc),
        "anchors_per_layer": int(detect.na),
        "detect_layers": int(detect.nl),
        "stride": [float(x) for x in detect.stride.tolist()],
    }
    if not args.no_forward:
        x = torch.zeros(1, 3, args.imgsz, args.imgsz, device=args.device)
        with torch.no_grad():
            out = model(x)[0]
        result["shape"] = list(out.shape)
    print(json.dumps(result, indent=2) if args.json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
