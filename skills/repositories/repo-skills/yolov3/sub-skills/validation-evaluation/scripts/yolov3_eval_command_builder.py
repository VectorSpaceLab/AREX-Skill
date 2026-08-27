#!/usr/bin/env python3
"""Build YOLOv3 val.py commands without executing them."""
from __future__ import annotations

import argparse
import json
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a reproducible python val.py command for YOLOv3.")
    parser.add_argument("--python", default="python")
    parser.add_argument("--data", default="data/coco128.yaml")
    parser.add_argument("--weights", default="yolov3-tiny.pt")
    parser.add_argument("--batch-size", "--batch", dest="batch_size", type=int, default=32)
    parser.add_argument("--imgsz", "--img", "--img-size", dest="imgsz", type=int, default=640)
    parser.add_argument("--conf-thres", type=float, default=None)
    parser.add_argument("--iou-thres", type=float, default=None)
    parser.add_argument("--task", choices=("train", "val", "test", "speed", "study"), default="val")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--project", default="runs/val")
    parser.add_argument("--name", default="exp")
    parser.add_argument("--exist-ok", action="store_true")
    parser.add_argument("--save-txt", action="store_true")
    parser.add_argument("--save-conf", action="store_true")
    parser.add_argument("--save-json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--dnn", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    cmd = [args.python, "val.py", "--data", args.data, "--weights", args.weights, "--batch-size", str(args.batch_size), "--imgsz", str(args.imgsz), "--task", args.task, "--device", args.device, "--project", args.project, "--name", args.name]
    for flag, value in (("--conf-thres", args.conf_thres), ("--iou-thres", args.iou_thres)):
        if value is not None:
            cmd.extend([flag, str(value)])
    for flag in ("exist_ok", "save_txt", "save_conf", "save_json", "verbose", "half", "dnn"):
        if getattr(args, flag):
            cmd.append("--" + flag.replace("_", "-"))
    payload = {"command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd)}
    print(json.dumps(payload, indent=2) if args.json else payload["shell"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
