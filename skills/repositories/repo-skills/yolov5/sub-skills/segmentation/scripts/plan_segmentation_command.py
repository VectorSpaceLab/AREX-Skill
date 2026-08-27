#!/usr/bin/env python3
"""Print a safe YOLOv5 segmentation command preview without executing it."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a YOLOv5 segmentation command without running it")
    parser.add_argument("mode", choices=("predict", "train", "val"), help="segmentation workflow")
    parser.add_argument("--weights", default="yolov5s-seg.pt", help="segmentation checkpoint")
    parser.add_argument("--source", default="data/images", help="prediction source")
    parser.add_argument("--data", default="coco128-seg.yaml", help="segmentation data YAML")
    parser.add_argument("--cfg", default="models/segment/yolov5s-seg.yaml", help="segmentation model YAML")
    parser.add_argument("--epochs", type=int, default=1, help="training epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="image size")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or device index")
    parser.add_argument("--project", default="runs/planned-seg", help="output project directory")
    parser.add_argument("--name", default="exp", help="output run name")
    parser.add_argument("--retina-masks", action="store_true", help="request high-resolution prediction masks")
    parser.add_argument("--overlap", action="store_true", help="use overlap mask behavior for train/val where supported")
    args = parser.parse_args()

    script = {"predict": "segment/predict.py", "train": "segment/train.py", "val": "segment/val.py"}[args.mode]
    command = ["python", script, "--weights", args.weights, "--data", args.data, "--imgsz", str(args.imgsz), "--device", args.device, "--project", args.project, "--name", args.name]
    if args.mode == "predict":
        command.extend(["--source", args.source])
        if args.retina_masks:
            command.append("--retina-masks")
    elif args.mode == "train":
        command.extend(["--cfg", args.cfg, "--epochs", str(args.epochs), "--batch-size", str(args.batch_size)])
        if args.overlap:
            command.append("--overlap")
    else:
        command.extend(["--batch-size", str(args.batch_size)])
        if args.overlap:
            command.append("--overlap")

    print("Command preview:")
    print(shlex.join(command))
    print("\nPreflight warnings:")
    if "-seg" not in args.weights and args.weights.endswith(".pt"):
        print("- checkpoint name does not look segmentation-specific; verify task compatibility")
    if args.data.endswith(".yaml") and "seg" not in args.data.lower():
        print("- data YAML name does not indicate segmentation; verify polygon labels exist")
    if args.weights.endswith(".pt") and not (args.weights.startswith("/") or args.weights.startswith(".")):
        print("- checkpoint name may trigger a network download")
    if args.mode == "train":
        print("- segmentation training writes run artifacts and requires polygon labels")
    if args.retina_masks:
        print("- retina masks can increase memory/output size")
    if args.overlap:
        print("- overlap changes mask target/evaluation behavior; confirm this is intended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
