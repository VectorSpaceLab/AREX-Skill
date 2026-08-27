#!/usr/bin/env python3
"""Build YOLOv3 training commands without executing them."""
from __future__ import annotations

import argparse
import json
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a reproducible python train.py command for YOLOv3.")
    parser.add_argument("--python", default="python")
    parser.add_argument("--data", default="data/coco128.yaml")
    parser.add_argument("--weights", default="yolov3-tiny.pt")
    parser.add_argument("--cfg", default="yolov3-tiny.yaml")
    parser.add_argument("--hyp", default="data/hyps/hyp.scratch-low.yaml")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", "--batch", dest="batch_size", type=int, default=32)
    parser.add_argument("--imgsz", "--img", "--img-size", dest="imgsz", type=int, default=64)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--name", default="smoke")
    parser.add_argument("--project", default="runs/train")
    parser.add_argument("--exist-ok", action="store_true")
    parser.add_argument("--resume", default=None, help="optional resume value; use true for bare --resume")
    parser.add_argument("--cache", default=None, help="optional cache mode, e.g. ram or disk")
    parser.add_argument("--single-cls", action="store_true")
    parser.add_argument("--optimizer", choices=("SGD", "Adam", "AdamW"), default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cmd = [args.python, "train.py", "--imgsz", str(args.imgsz), "--batch-size", str(args.batch_size), "--weights", args.weights, "--cfg", args.cfg, "--data", args.data, "--hyp", args.hyp, "--epochs", str(args.epochs), "--device", args.device, "--project", args.project, "--name", args.name]
    if args.exist_ok:
        cmd.append("--exist-ok")
    if args.resume:
        cmd.append("--resume")
        if args.resume.lower() != "true":
            cmd.append(args.resume)
    if args.cache:
        cmd.extend(["--cache", args.cache])
    if args.single_cls:
        cmd.append("--single-cls")
    if args.optimizer:
        cmd.extend(["--optimizer", args.optimizer])
    if args.json:
        print(json.dumps({"command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd)}, indent=2))
    else:
        print(" ".join(shlex.quote(x) for x in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
