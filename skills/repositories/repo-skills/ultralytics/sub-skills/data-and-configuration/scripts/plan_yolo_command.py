#!/usr/bin/env python3
"""Validate and render a safe Ultralytics YOLO CLI command without running it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

TASKS = {"detect", "segment", "classify", "pose", "obb", "semantic"}
MODES = {"train", "val", "predict", "export", "track", "benchmark"}
TASK_TO_MODEL = {
    "detect": "yolo26n.pt",
    "segment": "yolo26n-seg.pt",
    "classify": "yolo26n-cls.pt",
    "pose": "yolo26n-pose.pt",
    "obb": "yolo26n-obb.pt",
    "semantic": "yolo26n-sem.pt",
}
TASK_TO_DATA = {
    "detect": "coco8.yaml",
    "segment": "coco8-seg.yaml",
    "classify": "imagenet10",
    "pose": "coco8-pose.yaml",
    "obb": "dota8.yaml",
    "semantic": "cityscapes8.yaml",
}
DEPRECATED = {
    "boxes": "show_boxes",
    "line_thickness": "line_width",
    "hide_labels": "show_labels (invert the boolean value)",
    "hide_conf": "show_conf (invert the boolean value)",
}
REMOVED = {"label_smoothing", "save_hybrid", "crop_fraction"}
ALLOWED_KEYS = {
    "agnostic_nms", "amp", "angle", "augment", "auto_augment", "batch", "bgr", "box", "cache", "cfg",
    "classes", "close_mosaic", "cls", "cls_pw", "compile", "conf", "copy_paste", "copy_paste_mode", "cos_lr",
    "cutmix", "data", "degrees", "deterministic", "device", "dfl", "dnn", "dropout", "dynamic", "embed",
    "end2end", "epochs", "erasing", "exist_ok", "fliplr", "flipud", "format", "fraction", "freeze", "half",
    "hsv_h", "hsv_s", "hsv_v", "imgsz", "int8", "iou", "keras", "kobj", "line_width", "lr0", "lrf",
    "mask_ratio", "max_det", "mixup", "mode", "model", "momentum", "mosaic", "multi_scale", "name", "nbs",
    "nms", "opset", "optimize", "optimizer", "overlap_mask", "patience", "perspective", "plots", "pose",
    "pretrained", "profile", "project", "rect", "resume", "retina_masks", "rle", "save", "save_conf", "save_crop",
    "save_frames", "save_json", "save_period", "save_txt", "scale", "seed", "shear", "show", "show_boxes",
    "show_conf", "show_labels", "simplify", "single_cls", "source", "split", "stream_buffer", "task", "time",
    "tracker", "translate", "val", "verbose", "vid_stride", "visualize", "warmup_bias_lr", "warmup_epochs",
    "warmup_momentum", "weight_decay", "workers", "workspace", "augmentations", "save_dir",
}
RISK_KEYS = {
    "train": {"epochs", "time", "batch", "cache", "device", "workers", "project", "name", "save", "amp", "compile"},
    "predict": {"source", "show", "save", "save_frames", "save_crop", "stream_buffer"},
    "track": {"source", "tracker", "show", "save", "save_frames", "stream_buffer"},
    "export": {"format", "int8", "device", "workspace", "data", "fraction", "half"},
    "benchmark": {"format", "int8", "device", "data", "half"},
    "val": {"data", "batch", "device", "save_json", "plots"},
}


def parse_value(text: str) -> Any:
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def parse_arg_pair(token: str) -> tuple[str, Any]:
    if token.startswith("--"):
        raise ValueError(f"Ultralytics CLI does not use '--' prefixes for overrides: {token}")
    if "=" not in token:
        raise ValueError(f"override must be arg=value, got: {token}")
    key, value = token.split("=", 1)
    if not key:
        raise ValueError(f"empty argument name in token: {token}")
    return key, parse_value(value)


def load_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if args.kwargs:
        loaded = json.loads(args.kwargs)
        if not isinstance(loaded, dict):
            raise ValueError("--kwargs must be a JSON object")
        values.update(loaded)
    for pair in args.arg:
        key, value = parse_arg_pair(pair)
        values[key] = value
    if args.model:
        values["model"] = args.model
    if args.data:
        values["data"] = args.data
    return values


def stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(stringify(item) for item in value) + "]"
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def shell_token(key: str, value: Any) -> str:
    return shlex.quote(f"{key}={stringify(value)}")


def validate_values(task: str, mode: str, values: dict[str, Any], strict: bool) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    for key in sorted(values):
        if key in DEPRECATED:
            issues.append(f"deprecated key '{key}'; use {DEPRECATED[key]}")
        elif key in REMOVED:
            issues.append(f"removed key '{key}' is not supported")
        elif strict and key not in ALLOWED_KEYS:
            issues.append(f"unknown key '{key}'")

    if mode in {"train", "val", "benchmark"} and task != "classify" and "data" not in values:
        warnings.append(f"mode '{mode}' usually needs data=...; task default would be {TASK_TO_DATA.get(task)}")
    if mode == "predict" and "source" not in values:
        warnings.append("predict usually needs source=... unless the model call supplies a source elsewhere")
    if mode == "export" and values.get("int8") is True and "data" not in values:
        warnings.append("int8 export should specify reviewed calibration data=...")
    if "model" not in values:
        warnings.append(f"model not supplied; task default candidate is {TASK_TO_MODEL.get(task)}")
    if mode == "train" and int(values.get("epochs", 1) or 1) > 1:
        warnings.append("training is expensive; consider epochs=1 for smoke tests")
    if values.get("cache") in {True, "ram", "disk"}:
        warnings.append("cache may consume substantial RAM or disk")
    if str(values.get("source", "")).isdigit() or str(values.get("source", "")).startswith(("rtsp://", "http://", "https://")):
        warnings.append("source may open a camera, stream, URL, or network media")
    if values.get("device") not in (None, "cpu"):
        warnings.append("non-CPU device requested; verify backend availability before running")

    risk = sorted(RISK_KEYS.get(mode, set()) & set(values))
    if risk:
        warnings.append("side-effect/cost-sensitive keys present: " + ", ".join(risk))
    return issues, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a YOLO CLI command from validated task/mode and kwargs.")
    parser.add_argument("--task", choices=sorted(TASKS), default="detect", help="YOLO task to include in the command")
    parser.add_argument("--mode", choices=sorted(MODES), required=True, help="YOLO mode to run")
    parser.add_argument("--model", help="Model path/name to add as model=...")
    parser.add_argument("--data", help="Dataset path/name to add as data=...")
    parser.add_argument("--kwargs", help="JSON object of Python-style kwargs to translate")
    parser.add_argument("--arg", action="append", default=[], help="Additional arg=value override; may be repeated")
    parser.add_argument("--allow-unknown", action="store_true", help="Warn less strictly about keys outside known defaults")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        values = load_kwargs(args)
        issues, warnings = validate_values(args.task, args.mode, values, strict=not args.allow_unknown)
        command = " ".join(["yolo", args.task, args.mode, *[shell_token(k, values[k]) for k in sorted(values)]])
    except Exception as exc:
        issues, warnings, command = [str(exc)], [], ""

    if args.json:
        print(json.dumps({"ok": not issues, "command": command, "issues": issues, "warnings": warnings}, indent=2))
    else:
        if command:
            print(command)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
