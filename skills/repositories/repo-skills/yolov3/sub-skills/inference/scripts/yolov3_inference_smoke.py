#!/usr/bin/env python3
"""Run an offline YOLOv3 model-construction and forward smoke test."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a YOLOv3 YAML model and run a zero-tensor forward pass.")
    parser.add_argument("--repo-root", default=".", help="YOLOv3 checkout root containing models/ and utils/")
    parser.add_argument("--cfg", default="models/yolov3-tiny.yaml", help="model YAML path relative to repo root or absolute")
    parser.add_argument("--imgsz", type=int, default=64, help="square image size for the probe")
    parser.add_argument("--batch", type=int, default=1, help="batch size")
    parser.add_argument("--device", default="cpu", help="torch device, normally cpu for smoke checks")
    parser.add_argument("--dry-run", action="store_true", help="print the resolved plan without importing torch")
    parser.add_argument("--json", action="store_true", help="print result as JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    cfg = Path(args.cfg)
    cfg_path = cfg if cfg.is_absolute() else repo_root / cfg
    result = {"repo_root": str(repo_root), "cfg": str(cfg_path), "imgsz": args.imgsz, "batch": args.batch, "device": args.device}
    if args.dry_run:
        result["status"] = "DRY_RUN"
        print(json.dumps(result, indent=2) if args.json else result)
        return 0
    if not (repo_root / "models" / "yolo.py").exists():
        print(f"missing YOLOv3 models/yolo.py under {repo_root}", file=sys.stderr)
        return 2
    if not cfg_path.exists():
        print(f"missing cfg {cfg_path}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))
    import torch
    from models.yolo import Model

    model = Model(str(cfg_path)).to(args.device).eval()
    x = torch.zeros(args.batch, 3, args.imgsz, args.imgsz, device=args.device)
    with torch.no_grad():
        y = model(x)[0]
    result.update({"status": "PASS", "shape": list(y.shape)})
    print(json.dumps(result, indent=2) if args.json else f"PASS shape={tuple(y.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
