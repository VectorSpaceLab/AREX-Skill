#!/usr/bin/env python3
"""Print a safe YOLOv5 detection command preview without executing it."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a YOLOv5 detection command without running it")
    parser.add_argument("mode", choices=("predict", "train", "val"), help="detection workflow")
    parser.add_argument("--weights", default="yolov5s.pt", help="checkpoint name or local path")
    parser.add_argument("--source", default="data/images", help="prediction source")
    parser.add_argument("--data", default="coco128.yaml", help="dataset YAML")
    parser.add_argument("--cfg", default="yolov5s.yaml", help="model YAML for scratch training")
    parser.add_argument("--epochs", type=int, default=1, help="training epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="image size")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or device index")
    parser.add_argument("--project", default="runs/planned", help="output project directory")
    parser.add_argument("--name", default="exp", help="output run name")
    parser.add_argument("--nosave", action="store_true", help="avoid prediction media output")
    parser.add_argument("--half", action="store_true", help="request half precision")
    args = parser.parse_args()

    if args.mode == "predict":
        command = [
            "python",
            "detect.py",
            "--weights",
            args.weights,
            "--source",
            args.source,
            "--data",
            args.data,
            "--imgsz",
            str(args.imgsz),
            "--device",
            args.device,
            "--project",
            args.project,
            "--name",
            args.name,
        ]
        if args.nosave:
            command.append("--nosave")
        if args.half:
            command.append("--half")
    elif args.mode == "train":
        command = [
            "python",
            "train.py",
            "--data",
            args.data,
            "--weights",
            args.weights,
            "--cfg",
            args.cfg,
            "--epochs",
            str(args.epochs),
            "--batch-size",
            str(args.batch_size),
            "--imgsz",
            str(args.imgsz),
            "--device",
            args.device,
            "--project",
            args.project,
            "--name",
            args.name,
        ]
    else:
        command = [
            "python",
            "val.py",
            "--weights",
            args.weights,
            "--data",
            args.data,
            "--batch-size",
            str(args.batch_size),
            "--imgsz",
            str(args.imgsz),
            "--device",
            args.device,
            "--project",
            args.project,
            "--name",
            args.name,
        ]
        if args.half:
            command.append("--half")

    print("Command preview:")
    print(shlex.join(command))
    print("\nPreflight warnings:")
    if args.weights.endswith(".pt") and not (args.weights.startswith("/") or args.weights.startswith(".")):
        print("- checkpoint name may trigger a network download; use a local path for offline work")
    if args.data.endswith(".yaml") and not (args.data.startswith("/") or args.data.startswith(".")):
        print("- dataset YAML/path resolution depends on the checkout and dataset layout")
    if args.mode == "train":
        print("- training writes run artifacts and may be long-running; confirm epochs, output dir, and compute budget")
    if args.mode == "predict" and args.source not in {"data/images", "image.jpg"}:
        print("- non-default sources may open media, network streams, webcams, or screen capture")
    if args.half and args.device == "cpu":
        print("- --half is generally inappropriate for CPU execution; remove it or select a compatible CUDA device")
    if args.project.startswith("runs/"):
        print("- confirm that the planned run directory is isolated from existing experiments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
