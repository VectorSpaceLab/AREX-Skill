#!/usr/bin/env python3
"""Build a YOLOv7-d2 export.py command and preview artifact names.

Planner only: it does not import YOLOv7-d2, Detectron2, PyTorch, or ONNX.
"""
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath
import shlex
import sys


def qjoin(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def stem_from_weights(weights: str) -> str:
    name = PurePosixPath(weights).name
    if not name:
        raise ValueError("--weights must include a filename")
    return name.split(".")[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a YOLOv7-d2 export.py command and expected outputs.")
    parser.add_argument("--config-file", "--config", dest="config_file", required=True)
    parser.add_argument("--input", required=True, help="Single sample image file; export.py asserts this is a file.")
    parser.add_argument("--weights", required=True, help="Checkpoint path for MODEL.WEIGHTS.")
    parser.add_argument("--device", default="cpu", help="MODEL.DEVICE override; use empty string to omit.")
    parser.add_argument("--verbose", action="store_true", help="Add export.py --verbose.")
    parser.add_argument("--opt", nargs=2, action="append", metavar=("KEY", "VALUE"), help="Extra cfg override; repeat as needed.")
    parser.add_argument("--python", default="python")
    parser.add_argument("--entrypoint", default="export.py")
    parser.add_argument("--output-root", default="weights", help="Source export.py writes under weights/.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    try:
        stem = stem_from_weights(args.weights)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cmd = [args.python, args.entrypoint, "--config-file", args.config_file, "--input", args.input]
    if args.verbose:
        cmd.append("--verbose")
    opts = ["MODEL.WEIGHTS", args.weights]
    if args.device:
        opts += ["MODEL.DEVICE", args.device]
    for key, value in args.opt or []:
        opts += [key, value]
    cmd += ["--opts", *opts]

    root = args.output_root.rstrip("/") or "."
    outputs = {
        "raw_onnx": f"{root}/{stem}.onnx",
        "simplified_onnx": f"{root}/{stem}_sim.onnx",
        "detr_changed_onnx": f"{root}/{stem}_sim.onnx_changed.onnx",
        "torchscript": f"{root}/{stem}.pt",
    }
    payload = {
        "command": qjoin(cmd),
        "argv": cmd,
        "expected_outputs": outputs,
        "caveats": [
            "real export requires YOLOv7-d2, Detectron2, model config, checkpoint, PyTorch, onnx, and onnxsim",
            "output stem uses checkpoint basename before the first dot",
            "DETR graph surgery needs onnx_graphsurgeon imported as gs before it can work",
        ],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["command"])
        print("# expected outputs:")
        for key, value in outputs.items():
            print(f"#   {key}: {value}")
        for caveat in payload["caveats"]:
            print(f"# note: {caveat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
