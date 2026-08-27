#!/usr/bin/env python3
"""Probe YOLOv3 hubconf model creation with optional offline mode."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODEL_TO_FUNCTION = {"yolov3": "yolov3", "yolov3-spp": "yolov3_spp", "yolov3-tiny": "yolov3_tiny"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a YOLOv3 hubconf model locally; optionally run a tiny forward.")
    parser.add_argument("--repo-root", default=".", help="YOLOv3 checkout root containing hubconf.py")
    parser.add_argument("--model", choices=sorted(MODEL_TO_FUNCTION), default="yolov3-tiny")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pretrained", dest="pretrained", action="store_true", help="load pretrained weights; may download")
    group.add_argument("--no-pretrained", dest="pretrained", action="store_false", help="construct from YAML without weights")
    parser.set_defaults(pretrained=False)
    parser.add_argument("--classes", type=int, default=80)
    parser.add_argument("--channels", type=int, default=3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-forward", action="store_true", help="only instantiate the model")
    parser.add_argument("--imgsz", type=int, default=64)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "hubconf.py").exists():
        print(f"missing hubconf.py under {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))
    import torch
    import hubconf

    fn = getattr(hubconf, MODEL_TO_FUNCTION[args.model])
    model = fn(pretrained=args.pretrained, channels=args.channels, classes=args.classes, autoshape=False, _verbose=False, device=args.device)
    result = {"status": "PASS", "model": args.model, "pretrained": args.pretrained, "forward": not args.no_forward}
    if not args.no_forward:
        model.eval()
        x = torch.zeros(1, args.channels, args.imgsz, args.imgsz, device=args.device)
        with torch.no_grad():
            out = model(x)[0]
        result["shape"] = list(out.shape)
    print(json.dumps(result, indent=2) if args.json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
