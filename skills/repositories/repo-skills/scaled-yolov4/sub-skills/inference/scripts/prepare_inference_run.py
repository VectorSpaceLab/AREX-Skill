#!/usr/bin/env python3
"""Validate a ScaledYOLOv4 inference plan and print a canonical command.

This helper targets the skill-owned ``runtime/`` mirror by default so the
source-classification and output-plan checks stay self-contained.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "detect.py").is_file() and (candidate / "data" / "coco.yaml").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing detect.py")


def resolve_path(base: Path, raw: str) -> Path:
    path = Path(raw.strip())
    if path.is_absolute():
        return path
    return (base / path).resolve()


def classify_source(raw: str) -> str:
    if raw == "0" or raw.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        return "stream"
    if raw.endswith(".txt"):
        return "source-list"
    candidate = Path(raw)
    if candidate.suffix:
        return "file"
    return "folder-or-glob"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="source root used to resolve relative paths; defaults to this skill's bundled runtime/ mirror")
    parser.add_argument("--weights", type=str, default="yolov4-p5.pt", help="checkpoint path")
    parser.add_argument("--source", type=str, default="inference/images", help="file, folder, webcam index, stream URL, or source list")
    parser.add_argument("--output", type=str, default="inference/output", help="output directory")
    parser.add_argument("--img-size", type=int, default=640)
    parser.add_argument("--conf-thres", type=float, default=0.4)
    parser.add_argument("--iou-thres", type=float, default=0.5)
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--view-img", action="store_true")
    parser.add_argument("--save-txt", action="store_true")
    parser.add_argument("--classes", nargs="+", type=int)
    parser.add_argument("--agnostic-nms", action="store_true")
    parser.add_argument("--augment", action="store_true")
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()

    repo_root = (args.repo_root or default_runtime_root()).expanduser().resolve()
    if not (repo_root / "detect.py").is_file():
        parser.error(f"--repo-root is not a ScaledYOLOv4 checkout: {repo_root}")

    if args.img_size < 1:
        parser.error("--img-size must be positive")
    if not (0.0 < args.conf_thres <= 1.0):
        parser.error("--conf-thres must be in (0, 1]")
    if not (0.0 < args.iou_thres <= 1.0):
        parser.error("--iou-thres must be in (0, 1]")

    weight_path = resolve_path(repo_root, args.weights)
    if not weight_path.is_file():
        parser.error(f"weights file not found: {weight_path}")

    source_kind = classify_source(args.source)
    if source_kind == "source-list":
        source_path = resolve_path(repo_root, args.source)
        if not source_path.is_file():
            parser.error(f"source list not found: {source_path}")
    elif source_kind in {"file", "folder-or-glob"}:
        source_path = resolve_path(repo_root, args.source)
        if not source_path.exists() and "*" not in args.source:
            parser.error(f"source path not found: {source_path}")
    else:
        source_path = Path(args.source)

    output_path = resolve_path(repo_root, args.output)
    if output_path.exists() and any(output_path.iterdir()):
        print(f"warning: output directory is not empty and will be replaced: {output_path}")

    print("inference preflight passed")
    print(f"repo_root: {repo_root}")
    print(f"weights: {weight_path}")
    print(f"source_kind: {source_kind}")
    print(f"source: {source_path}")
    print(f"output: {output_path}")
    print(f"img_size: {args.img_size}")
    print(f"conf_thres: {args.conf_thres}")
    print(f"iou_thres: {args.iou_thres}")
    print(f"device: {args.device or '(auto)'}")

    command = [
        "python",
        "detect.py",
        "--weights",
        args.weights,
        "--source",
        args.source,
        "--output",
        args.output,
        "--img-size",
        str(args.img_size),
        "--conf-thres",
        str(args.conf_thres),
        "--iou-thres",
        str(args.iou_thres),
    ]
    if args.device:
        command.extend(["--device", args.device])
    command += ["--view-img"] if args.view_img else []
    command += ["--save-txt"] if args.save_txt else []
    if args.classes:
        command.extend(["--classes", *[str(cls) for cls in args.classes]])
    command += ["--agnostic-nms"] if args.agnostic_nms else []
    command += ["--augment"] if args.augment else []
    command += ["--update"] if args.update else []

    print("canonical command:")
    print("  " + " ".join(shlex.quote(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
