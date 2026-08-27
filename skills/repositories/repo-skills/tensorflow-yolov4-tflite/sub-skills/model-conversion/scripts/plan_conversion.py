#!/usr/bin/env python3
"""Build safe conversion command plans for tensorflow-yolov4-tflite.

The script does not run TensorFlow conversion. It prints the commands a future
agent should review and execute from a target checkout root after confirming
weights, datasets, outputs, and backend requirements.
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


def require_exists(label: str, path: str, errors: List[str]) -> None:
    if path and not Path(path).expanduser().exists():
        errors.append(f"{label} does not exist: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan tensorflow-yolov4-tflite model conversion commands.")
    parser.add_argument("--task", choices=["savedmodel", "tflite", "trt", "full-tflite"], required=True,
                        help="Conversion stage to plan. full-tflite prints save_model plus convert_tflite.")
    parser.add_argument("--weights", default="data/yolov4.weights", help="Darknet .weights for savedmodel/full-tflite, or input SavedModel for tflite/trt when --saved-model is omitted.")
    parser.add_argument("--saved-model", default="checkpoints/yolov4-416", help="SavedModel directory path.")
    parser.add_argument("--output", default=None, help="Final output path for tflite/trt; defaults depend on task.")
    parser.add_argument("--model", choices=["yolov3", "yolov4"], default="yolov4")
    parser.add_argument("--tiny", action="store_true", help="Plan tiny model commands.")
    parser.add_argument("--input-size", type=int, default=416, help="Square model input size.")
    parser.add_argument("--score-thres", type=float, default=0.2, help="save_model.py score threshold for non-TFLite exports.")
    parser.add_argument("--quantize-mode", choices=["float32", "float16", "int8"], default="float32", help="TFLite quantization mode.")
    parser.add_argument("--trt-precision", choices=["float32", "float16", "int8"], default="float16", help="TF-TRT precision mode.")
    parser.add_argument("--dataset", default=None, help="Representative image-list path for int8 TFLite/TF-TRT.")
    parser.add_argument("--check-paths", action="store_true", help="Fail if source weight/SavedModel/dataset paths do not exist on this machine.")
    args = parser.parse_args()

    errors: List[str] = []
    if args.check_paths:
        if args.task in {"savedmodel", "full-tflite"}:
            require_exists("Darknet weights", args.weights, errors)
        if args.task in {"tflite", "trt"}:
            require_exists("SavedModel", args.saved_model or args.weights, errors)
        if args.quantize_mode == "int8" and args.task in {"tflite", "full-tflite"}:
            if not args.dataset:
                errors.append("--dataset is required with --quantize-mode int8")
            else:
                require_exists("representative dataset", args.dataset, errors)
        if args.trt_precision == "int8" and args.task == "trt":
            if not args.dataset:
                errors.append("--dataset is required with --trt-precision int8")
            else:
                require_exists("representative dataset", args.dataset, errors)

    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 2

    tiny_flag = ["--tiny"] if args.tiny else []
    output = args.output
    if output is None:
        if args.task in {"tflite", "full-tflite"}:
            suffix = "" if args.quantize_mode == "float32" else f"-{args.quantize_mode}"
            output = f"checkpoints/{args.model}{'-tiny' if args.tiny else ''}-{args.input_size}{suffix}.tflite"
        elif args.task == "trt":
            output = f"checkpoints/{args.model}{'-tiny' if args.tiny else ''}-trt-{args.trt_precision}-{args.input_size}"
        else:
            output = args.saved_model

    print("# Run these commands from the target tensorflow-yolov4-tflite checkout root.")
    print("# Review paths and backend requirements before executing.")

    if args.task in {"savedmodel", "full-tflite"}:
        framework = "tflite" if args.task == "full-tflite" else "tf"
        save_cmd = [
            "python", "save_model.py",
            "--weights", args.weights,
            "--output", args.saved_model,
            "--input_size", args.input_size,
            "--model", args.model,
            "--framework", framework,
            "--score_thres", args.score_thres,
            *tiny_flag,
        ]
        print(command(save_cmd))

    if args.task in {"tflite", "full-tflite"}:
        tflite_cmd = [
            "python", "convert_tflite.py",
            "--weights", args.saved_model,
            "--output", output,
            "--input_size", args.input_size,
            "--quantize_mode", args.quantize_mode,
        ]
        if args.quantize_mode == "int8":
            if not args.dataset:
                print("# WARNING: int8 quantization needs --dataset with accessible representative image paths.")
            else:
                tflite_cmd.extend(["--dataset", args.dataset])
        print(command(tflite_cmd))

    if args.task == "trt":
        trt_cmd = [
            "python", "convert_trt.py",
            "--weights", args.saved_model,
            "--output", output,
            "--input_size", args.input_size,
            "--quantize_mode", args.trt_precision,
        ]
        if args.trt_precision == "int8":
            if not args.dataset:
                print("# WARNING: int8 TF-TRT needs --dataset and the source typo image_preporcess must be fixed.")
            else:
                trt_cmd.extend(["--dataset", args.dataset])
        print(command(trt_cmd))
        print("# Verify TensorFlow GPU/TensorRT compatibility before running this command.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
