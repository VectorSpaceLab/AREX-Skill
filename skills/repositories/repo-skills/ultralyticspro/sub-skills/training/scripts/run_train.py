#!/usr/bin/env python3
"""Run Ultralytics training presets safely.

The default mode is a dry run that prints the resolved preset, model, dataset,
and training kwargs. Pass ``--execute`` to launch the actual training run.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TrainPreset:
    name: str
    family: str
    model: str
    data: str
    epochs: int
    imgsz: int
    workers: int
    batch: int
    device: str | int | None = None
    notes: str = ""


PRESETS: dict[str, TrainPreset] = {
    "train-v8": TrainPreset(
        name="train-v8",
        family="yolo",
        model="cfg/models/v8/yolov8.yaml",
        data="coco128.yaml",
        epochs=2,
        imgsz=640,
        workers=2,
        batch=2,
        notes="Matches train_v8.py.",
    ),
    "train-v8-linux": TrainPreset(
        name="train-v8-linux",
        family="yolo",
        model="cfg/models/v8/yolov8.yaml",
        data="coco128.yaml",
        epochs=2,
        imgsz=640,
        workers=0,
        batch=1,
        device="cpu",
        notes="Matches train_v8_linux.py and keeps CPU execution explicit.",
    ),
    "train-yolo11": TrainPreset(
        name="train-yolo11",
        family="yolo",
        model="cfg/models/11/yolo11.yaml",
        data="coco128.yaml",
        epochs=2,
        imgsz=640,
        workers=2,
        batch=2,
        notes="Matches train_yolo11.py.",
    ),
    "train-yolov10": TrainPreset(
        name="train-yolov10",
        family="yolo",
        model="cfg/models/v10/yolov10s.yaml",
        data="coco128.yaml",
        epochs=10,
        imgsz=640,
        workers=2,
        batch=2,
        device=0,
        notes="Matches train_yolov10.py.",
    ),
    "train-yolo12": TrainPreset(
        name="train-yolo12",
        family="yolo",
        model="cfg_yolov12/yolo12.yaml",
        data="coco128.yaml",
        epochs=2,
        imgsz=640,
        workers=2,
        batch=2,
        notes=(
            "Matches train_yolo12.py. The verified public Ultralytics install "
            "used for skill authoring does not ship this YAML path, so a local "
            "custom config file is required to execute the preset."
        ),
    ),
    "train-cls": TrainPreset(
        name="train-cls",
        family="yolo",
        model="cfg/models/11/yolo11-cls.yaml",
        data="mnist160",
        epochs=100,
        imgsz=640,
        workers=2,
        batch=8,
        notes="Matches train_cls.py.",
    ),
    "train-obb": TrainPreset(
        name="train-obb",
        family="yolo",
        model="cfg/models/11/yolo11-obb.yaml",
        data="dota8.yaml",
        epochs=2,
        imgsz=640,
        workers=2,
        batch=2,
        notes="Matches train_obb.py.",
    ),
    "train-pose": TrainPreset(
        name="train-pose",
        family="yolo",
        model="cfg/models/11/yolo11-pose.yaml",
        data="coco8-pose.yaml",
        epochs=300,
        imgsz=640,
        workers=2,
        batch=4,
        notes="Matches train_pose.py.",
    ),
    "train-seg": TrainPreset(
        name="train-seg",
        family="yolo",
        model="cfg/models/11/yolo11-seg.yaml",
        data="coco8-seg.yaml",
        epochs=300,
        imgsz=640,
        workers=2,
        batch=2,
        notes="Matches train_seg01.py.",
    ),
    "train-rtdetr": TrainPreset(
        name="train-rtdetr",
        family="rtdetr",
        model="cfg/models/rt-detr/rtdetr-l.yaml",
        data="coco128.yaml",
        epochs=100,
        imgsz=320,
        workers=1,
        batch=1,
        notes="Matches train_rtdetr.py.",
    ),
}


def _pkg_root() -> Path:
    import ultralytics

    return Path(ultralytics.__file__).resolve().parent


def _resolve_model(model: str) -> tuple[str, Path | None]:
    if model.startswith(("http://", "https://")):
        return model, None
    if model.startswith("cfg/") or model.startswith("cfg_yolov12/"):
        path = _pkg_root() / model
        return str(path), path
    path = Path(model)
    if path.exists():
        return str(path.resolve()), path.resolve()
    return model, None


def _load_model_class(family: str):
    if family == "rtdetr":
        from ultralytics import RTDETR

        return RTDETR
    from ultralytics import YOLO

    return YOLO


def _print_plan(preset: TrainPreset, model: str, resolved: Path | None, data: str, extra: dict[str, Any]) -> None:
    print(f"preset: {preset.name}")
    print(f"family: {preset.family}")
    print(f"model: {model}")
    if resolved is not None:
        print(f"resolved model path: {resolved}")
    print(f"data: {data}")
    print(
        "defaults: "
        f"epochs={preset.epochs}, imgsz={preset.imgsz}, workers={preset.workers}, batch={preset.batch}, "
        f"device={preset.device!r}"
    )
    print(f"notes: {preset.notes}")
    print("effective kwargs:")
    print(json.dumps(extra, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ultralytics training presets safely.")
    parser.add_argument(
        "--preset",
        default="train-yolo11",
        choices=sorted(PRESETS),
        help="Named training preset that matches a source script.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the preset model path, config, or weight name.",
    )
    parser.add_argument("--data", default=None, help="Override the preset dataset YAML or name.")
    parser.add_argument("--epochs", type=int, default=None, help="Override preset epochs.")
    parser.add_argument("--imgsz", type=int, default=None, help="Override preset image size.")
    parser.add_argument("--workers", type=int, default=None, help="Override preset dataloader workers.")
    parser.add_argument("--batch", type=int, default=None, help="Override preset batch size.")
    parser.add_argument("--device", default=None, help="Override preset device, e.g. cpu or 0.")
    parser.add_argument("--project", default=None, help="Ultralytics project directory.")
    parser.add_argument("--name", default=None, help="Ultralytics run name.")
    parser.add_argument("--execute", action="store_true", help="Actually launch training.")
    parser.add_argument("--list-presets", action="store_true", help="Print the preset table and exit.")
    args = parser.parse_args()

    if args.list_presets:
        for key in sorted(PRESETS):
            preset = PRESETS[key]
            print(f"{preset.name}: {preset.notes}")
        return 0

    preset = PRESETS[args.preset]
    model_value = args.model or preset.model
    data_value = args.data or preset.data
    model_value, resolved = _resolve_model(model_value)
    effective = {
        "data": data_value,
        "epochs": args.epochs if args.epochs is not None else preset.epochs,
        "imgsz": args.imgsz if args.imgsz is not None else preset.imgsz,
        "workers": args.workers if args.workers is not None else preset.workers,
        "batch": args.batch if args.batch is not None else preset.batch,
        "device": args.device if args.device is not None else preset.device,
        "project": args.project,
        "name": args.name,
    }
    _print_plan(preset, model_value, resolved, data_value, effective)

    if not args.execute:
        print("dry-run: no training started")
        return 0

    if preset.name == "train-yolo12" and resolved is not None and not resolved.exists():
        raise SystemExit(
            "The train-yolo12 preset requires a local yolo12.yaml file. "
            "The inspected public Ultralytics install does not ship cfg_yolov12/yolo12.yaml."
        )

    model_cls = _load_model_class(preset.family)
    model = model_cls(model_value)
    kwargs = {k: v for k, v in effective.items() if v is not None}
    model.train(**kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
