#!/usr/bin/env python3
"""Run Ultralytics prediction presets safely.

The default mode is a dry run that prints the resolved model and source image.
Pass ``--execute`` to launch the actual prediction call.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PredictPreset:
    name: str
    model: str
    source: str
    imgsz: int
    conf: float
    save: bool
    notes: str = ""


PRESETS: dict[str, PredictPreset] = {
    "predict-v8": PredictPreset(
        name="predict-v8",
        model="yolov8n.pt",
        source="assets/zidane.jpg",
        imgsz=640,
        conf=0.5,
        save=True,
        notes="Matches predict_v8.py.",
    ),
    "predict-yolo11": PredictPreset(
        name="predict-yolo11",
        model="yolo11n.pt",
        source="assets/zidane.jpg",
        imgsz=640,
        conf=0.5,
        save=True,
        notes="Matches predict_yolo11.py.",
    ),
    "predict-yolov10": PredictPreset(
        name="predict-yolov10",
        model="yolov10n.pt",
        source="assets/zidane.jpg",
        imgsz=640,
        conf=0.5,
        save=True,
        notes="Matches predict_yolov10.py.",
    ),
}


def _pkg_root() -> Path:
    import ultralytics

    return Path(ultralytics.__file__).resolve().parent


def _resolve_model(model: str) -> tuple[str, Path | None]:
    if model.startswith(("http://", "https://")):
        return model, None
    path = Path(model)
    if path.exists():
        return str(path.resolve()), path.resolve()
    return model, None


def _resolve_source(source: str) -> tuple[str, Path | None]:
    if source.startswith(("http://", "https://")):
        return source, None
    if source.startswith("assets/"):
        path = _pkg_root() / source
        return str(path), path
    path = Path(source)
    if path.exists():
        return str(path.resolve()), path.resolve()
    return source, None


def _print_plan(preset: PredictPreset, model: str, model_path: Path | None, source: str, source_path: Path | None, extra: dict[str, Any]) -> None:
    print(f"preset: {preset.name}")
    print(f"model: {model}")
    if model_path is not None:
        print(f"resolved model path: {model_path}")
    print(f"source: {source}")
    if source_path is not None:
        print(f"resolved source path: {source_path}")
    print(f"defaults: imgsz={preset.imgsz}, conf={preset.conf}, save={preset.save}")
    print(f"notes: {preset.notes}")
    print("effective kwargs:")
    print(json.dumps(extra, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ultralytics prediction presets safely.")
    parser.add_argument(
        "--preset",
        default="predict-yolo11",
        choices=sorted(PRESETS),
        help="Named prediction preset that matches a source script.",
    )
    parser.add_argument("--model", default=None, help="Override the preset model weights or path.")
    parser.add_argument("--source", default=None, help="Override the preset source image or input.")
    parser.add_argument("--imgsz", type=int, default=None, help="Override preset image size.")
    parser.add_argument("--conf", type=float, default=None, help="Override preset confidence threshold.")
    parser.add_argument("--save", action="store_true", default=None, help="Force save=True.")
    parser.add_argument("--no-save", action="store_true", help="Force save=False.")
    parser.add_argument("--device", default=None, help="Override device, e.g. cpu or 0.")
    parser.add_argument("--project", default=None, help="Ultralytics project directory.")
    parser.add_argument("--name", default=None, help="Ultralytics run name.")
    parser.add_argument("--execute", action="store_true", help="Actually launch prediction.")
    parser.add_argument("--list-presets", action="store_true", help="Print the preset table and exit.")
    args = parser.parse_args()

    if args.list_presets:
        for key in sorted(PRESETS):
            preset = PRESETS[key]
            print(f"{preset.name}: {preset.notes}")
        return 0

    preset = PRESETS[args.preset]
    model_value = args.model or preset.model
    source_value = args.source or preset.source
    model_value, model_path = _resolve_model(model_value)
    source_value, source_path = _resolve_source(source_value)
    save_value = preset.save
    if args.save:
        save_value = True
    if args.no_save:
        save_value = False
    effective = {
        "imgsz": args.imgsz if args.imgsz is not None else preset.imgsz,
        "conf": args.conf if args.conf is not None else preset.conf,
        "save": save_value,
        "device": args.device,
        "project": args.project,
        "name": args.name,
    }
    _print_plan(preset, model_value, model_path, source_value, source_path, effective)

    if not args.execute:
        print("dry-run: no prediction started")
        return 0

    from ultralytics import YOLO

    model = YOLO(model_value)
    kwargs = {k: v for k, v in effective.items() if v is not None}
    model.predict(source_value, **kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
