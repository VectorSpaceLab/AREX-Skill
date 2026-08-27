#!/usr/bin/env python3
"""Print YOLOv3 native smoke-test plans without running repo commands."""
from __future__ import annotations

import argparse
import json
import shlex

CASES = [
    {
        "id": "model-yaml-cpu",
        "owner": "model-architecture",
        "safe": "yes",
        "needs": "base dependencies only",
        "command": ["python", "models/yolo.py", "--cfg", "yolov3-tiny.yaml"],
    },
    {
        "id": "train-tiny-cpu",
        "owner": "training",
        "safe": "network-and-time-dependent",
        "needs": "official weights and coco128 may download",
        "command": [
            "python",
            "train.py",
            "--imgsz",
            "64",
            "--batch-size",
            "32",
            "--weights",
            "yolov3-tiny.pt",
            "--cfg",
            "yolov3-tiny.yaml",
            "--epochs",
            "1",
            "--device",
            "cpu",
            "--name",
            "smoke",
            "--exist-ok",
        ],
    },
    {
        "id": "val-trained-cpu",
        "owner": "validation-evaluation",
        "safe": "after-train-smoke",
        "needs": "trained checkpoint from train-tiny-cpu",
        "command": ["python", "val.py", "--imgsz", "64", "--batch-size", "32", "--weights", "runs/train/smoke/weights/best.pt", "--device", "cpu"],
    },
    {
        "id": "detect-official-cpu",
        "owner": "inference",
        "safe": "network-dependent",
        "needs": "official weights may download",
        "command": ["python", "detect.py", "--imgsz", "64", "--weights", "yolov3-tiny.pt", "--device", "cpu"],
    },
    {
        "id": "export-torchscript-cpu",
        "owner": "export-deployment",
        "safe": "network-dependent",
        "needs": "official weights may download",
        "command": ["python", "export.py", "--weights", "yolov3-tiny.pt", "--img", "64", "--include", "torchscript"],
    },
]


def shell(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print YOLOv3 native smoke commands and safety notes; no commands are run.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--safe-only", action="store_true", help="show only base safe commands")
    args = parser.parse_args()
    cases = [case for case in CASES if not args.safe_only or case["safe"] == "yes"]
    if args.format == "json":
        print(json.dumps(cases, indent=2))
        return 0
    for case in cases:
        print(f"# {case['id']} [{case['owner']}] safe={case['safe']} needs={case['needs']}")
        print(shell(case["command"]))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
