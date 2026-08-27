#!/usr/bin/env python3
"""Print a safe YOLOv5 classification command preview without executing it."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a YOLOv5 classification command without running it")
    parser.add_argument("mode", choices=("predict", "train", "val"), help="classification workflow")
    parser.add_argument("--weights", default="yolov5s-cls.pt", help="classification checkpoint or model name")
    parser.add_argument("--model", default="yolov5s-cls.pt", help="train-time model name or checkpoint")
    parser.add_argument("--source", default="data/images", help="prediction source")
    parser.add_argument("--data", default="cifar100", help="named dataset or local ImageFolder path")
    parser.add_argument("--epochs", type=int, default=1, help="training epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="batch size")
    parser.add_argument("--imgsz", type=int, default=224, help="image size")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or device index")
    parser.add_argument("--project", default="runs/planned-cls", help="output project directory")
    parser.add_argument("--name", default="exp", help="output run name")
    parser.add_argument("--half", action="store_true", help="request half precision")
    parser.add_argument("--pretrained", action="store_true", help="request pretrained initialization")
    args = parser.parse_args()

    script = {"predict": "classify/predict.py", "train": "classify/train.py", "val": "classify/val.py"}[args.mode]
    command = ["python", script, "--data", args.data, "--imgsz", str(args.imgsz), "--device", args.device, "--project", args.project, "--name", args.name]
    if args.mode == "predict":
        command.extend(["--weights", args.weights, "--source", args.source])
        if args.half:
            command.append("--half")
    elif args.mode == "train":
        command.extend(["--model", args.model, "--epochs", str(args.epochs), "--batch-size", str(args.batch_size)])
        if args.pretrained:
            command.append("--pretrained")
    else:
        command.extend(["--weights", args.weights, "--batch-size", str(args.batch_size)])
        if args.half:
            command.append("--half")

    print("Command preview:")
    print(shlex.join(command))
    print("\nPreflight warnings:")
    if args.mode == "train" and not (args.data.startswith("/") or args.data.startswith(".")):
        print("- named dataset strings may download data; confirm network approval and storage budget")
    if args.data and not (args.data.startswith("/") or args.data.startswith(".")) and args.mode != "train":
        print("- data strings may still control class-name lookup or default dataset resolution")
    if args.weights.endswith(".pt") and not (args.weights.startswith("/") or args.weights.startswith(".")):
        print("- checkpoint or model name may trigger a download")
    if args.half and args.device == "cpu":
        print("- --half is generally inappropriate for CPU execution; remove it or select a CUDA device")
    if args.mode == "train":
        print("- training writes run artifacts and may use ImageFolder or named dataset downloads")
    if args.mode == "predict" and args.source not in {"data/images", "image.jpg"}:
        print("- non-default sources may open media, network streams, webcams, or screen capture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
