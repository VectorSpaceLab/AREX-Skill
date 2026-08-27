#!/usr/bin/env python3
"""Check the installed Ultralytics runtime and packaged presets.

Safe by default: imports the installed ``ultralytics`` package, prints verified
metadata, and never downloads weights or datasets.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProbeResult:
    package_version: str | None
    package_summary: str | None
    requires_python: str | None
    module_file: str
    cli_command: str | None
    yolo_signature: str
    rtdetr_signature: str
    packaged_assets: dict[str, bool]
    packaged_cfgs: dict[str, bool]


def _safe_sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def _probe() -> ProbeResult:
    try:
        import ultralytics
        from ultralytics import RTDETR, YOLO
    except Exception as exc:  # pragma: no cover - defensive user-facing path
        raise SystemExit(
            "Unable to import the installed 'ultralytics' package. "
            "Install it before using this skill helper."
        ) from exc

    dist = metadata.metadata("ultralytics")
    root = Path(ultralytics.__file__).resolve().parent
    cfgs = [
        "cfg/models/v8/yolov8.yaml",
        "cfg/models/v10/yolov10s.yaml",
        "cfg/models/11/yolo11.yaml",
        "cfg/models/11/yolo11-cls.yaml",
        "cfg/models/11/yolo11-obb.yaml",
        "cfg/models/11/yolo11-pose.yaml",
        "cfg/models/11/yolo11-seg.yaml",
        "cfg/models/rt-detr/rtdetr-l.yaml",
        "cfg_yolov12/yolo12.yaml",
    ]
    assets = ["assets/zidane.jpg", "assets/bus.jpg"]
    return ProbeResult(
        package_version=metadata.version("ultralytics"),
        package_summary=dist.get("Summary"),
        requires_python=dist.get("Requires-Python"),
        module_file=str(Path(ultralytics.__file__).resolve()),
        cli_command=str(Path(sys.executable).with_name("yolo")),
        yolo_signature=_safe_sig(YOLO),
        rtdetr_signature=_safe_sig(RTDETR),
        packaged_assets={rel: (root / rel).exists() for rel in assets},
        packaged_cfgs={rel: (root / rel).exists() for rel in cfgs},
    )


def _print_human(result: ProbeResult, presets: list[dict[str, str]]) -> None:
    print(f"ultralytics version: {result.package_version}")
    print(f"summary: {result.package_summary}")
    print(f"requires-python: {result.requires_python}")
    print(f"module file: {result.module_file}")
    print(f"YOLO signature: {result.yolo_signature}")
    print(f"RTDETR signature: {result.rtdetr_signature}")
    print("packaged assets:")
    for rel, ok in result.packaged_assets.items():
        print(f"  - {rel}: {'yes' if ok else 'no'}")
    print("packaged cfgs:")
    for rel, ok in result.packaged_cfgs.items():
        print(f"  - {rel}: {'yes' if ok else 'no'}")
    print("presets:")
    for item in presets:
        print(f"  - {item['name']}: {item['summary']}")


PRESETS = [
    {"name": "train-v8", "summary": "YOLOv8 detect training preset"},
    {"name": "train-v8-linux", "summary": "YOLOv8 detect training preset with CPU defaults"},
    {"name": "train-yolo11", "summary": "YOLO11 detect training preset"},
    {"name": "train-yolov10", "summary": "YOLOv10 detect training preset"},
    {"name": "train-yolo12", "summary": "YOLOv12 custom-config training preset"},
    {"name": "train-cls", "summary": "YOLO11 classification training preset"},
    {"name": "train-obb", "summary": "YOLO11 oriented bounding-box training preset"},
    {"name": "train-pose", "summary": "YOLO11 pose training preset"},
    {"name": "train-seg", "summary": "YOLO11 segmentation training preset"},
    {"name": "train-rtdetr", "summary": "RT-DETR training preset"},
    {"name": "predict-v8", "summary": "YOLOv8 detection inference preset"},
    {"name": "predict-yolo11", "summary": "YOLO11 detection inference preset"},
    {"name": "predict-yolov10", "summary": "YOLOv10 detection inference preset"},
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the installed Ultralytics package and show repo presets.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--show-presets",
        action="store_true",
        help="Include the bundled training/prediction preset index.",
    )
    args = parser.parse_args()

    result = _probe()
    payload = asdict(result)
    if args.show_presets:
        payload["presets"] = PRESETS
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_human(result, PRESETS if args.show_presets else [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
