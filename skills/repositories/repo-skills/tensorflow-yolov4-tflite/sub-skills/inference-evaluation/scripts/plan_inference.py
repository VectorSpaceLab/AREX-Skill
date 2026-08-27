#!/usr/bin/env python3
"""Build safe inference/evaluation command plans for tensorflow-yolov4-tflite.

The script validates option combinations and prints commands without running
TensorFlow, OpenCV video loops, evaluation, or benchmarks.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable, List


def q(value: object) -> str:
    return shlex.quote(str(value))


def command(parts: Iterable[object]) -> str:
    return " ".join(q(part) for part in parts)


def check(label: str, path: str, errors: List[str]) -> None:
    if path and not Path(path).expanduser().exists():
        errors.append(f"{label} does not exist: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan tensorflow-yolov4-tflite inference/evaluation commands.")
    parser.add_argument("--action", choices=["detect-image", "detect-video", "evaluate", "benchmark"], required=True)
    parser.add_argument("--framework", choices=["tf", "tflite", "trt"], default="tf")
    parser.add_argument("--weights", default="checkpoints/yolov4-416", help="SavedModel, .tflite, TF-TRT SavedModel, or Darknet weights for benchmark tf path.")
    parser.add_argument("--input", default=None, help="Image path for detect-image/benchmark or video path for detect-video.")
    parser.add_argument("--output", default=None, help="Output image/video path or mAP output directory name.")
    parser.add_argument("--model", choices=["yolov3", "yolov4"], default="yolov4")
    parser.add_argument("--tiny", action="store_true")
    parser.add_argument("--size", type=int, default=416)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--score", type=float, default=0.25)
    parser.add_argument("--annotation-path", default="data/dataset/val2017.txt", help="Evaluation annotation file; source evaluate.py may still use cfg.TEST.ANNOT_PATH.")
    parser.add_argument("--output-format", default="XVID", help="detectvideo.py codec when --output is supplied.")
    parser.add_argument("--disable-window", action="store_true", help="Add detectvideo.py --dis_cv2_window.")
    parser.add_argument("--check-paths", action="store_true", help="Fail if model/input/annotation paths do not exist on this machine.")
    args = parser.parse_args()

    errors: List[str] = []
    if args.check_paths:
        check("weights/model", args.weights, errors)
        if args.action in {"detect-image", "detect-video", "benchmark"}:
            if not args.input:
                errors.append(f"--input is required for {args.action}")
            else:
                check("input", args.input, errors)
        if args.action == "evaluate":
            check("annotation", args.annotation_path, errors)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    tiny_flag = ["--tiny"] if args.tiny else []
    print("# Run from the target tensorflow-yolov4-tflite checkout root.")
    print("# Confirm artifacts, data paths, and backend before executing.")

    if args.action == "detect-image":
        input_path = args.input or "data/kite.jpg"
        output = args.output or "result.png"
        parts = [
            "python", "detect.py",
            "--framework", args.framework,
            "--weights", args.weights,
            "--size", args.size,
            "--model", args.model,
            "--image", input_path,
            "--output", output,
            "--iou", args.iou,
            "--score", args.score,
            *tiny_flag,
        ]
        print(command(parts))
        if args.framework == "tflite" and args.tiny:
            print("# Validate TFLite output order on a known image before trusting tiny-model detections.")

    elif args.action == "detect-video":
        input_path = args.input or "data/road.mp4"
        parts = [
            "python", "detectvideo.py",
            "--framework", args.framework,
            "--weights", args.weights,
            "--size", args.size,
            "--model", args.model,
            "--video", input_path,
            "--iou", args.iou,
            "--score", args.score,
            "--output_format", args.output_format,
            *tiny_flag,
        ]
        if args.output:
            parts.extend(["--output", args.output])
        if args.disable_window:
            parts.append("--dis_cv2_window")
        print(command(parts))
        if not args.output:
            print("# WARNING: no --output supplied; detectvideo.py will display frames instead of writing a video.")

    elif args.action == "evaluate":
        parts = [
            "python", "evaluate.py",
            "--framework", args.framework,
            "--weights", args.weights,
            "--size", args.size,
            "--model", args.model,
            "--annotation_path", args.annotation_path,
            "--iou", args.iou,
            "--score", args.score,
            *tiny_flag,
        ]
        print(command(parts))
        print("cd mAP/extra && python remove_space.py && cd .. && python main.py --output " + q(args.output or "results_yolov4_tf"))
        print("# WARNING: source evaluate.py iterates cfg.TEST.ANNOT_PATH even when --annotation_path is supplied.")
        print("# It also recreates mAP/predicted and mAP/ground-truth.")

    elif args.action == "benchmark":
        input_path = args.input or "data/kite.jpg"
        parts = [
            "python", "benchmarks.py",
            "--framework", args.framework,
            "--weights", args.weights,
            "--size", args.size,
            "--model", args.model,
            "--image", input_path,
            *tiny_flag,
        ]
        print(command(parts))
        if args.framework in {"trt", "tf"}:
            print("# Record whether TensorFlow reports usable GPU devices before interpreting FPS.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
