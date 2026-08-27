#!/usr/bin/env python3
"""Static validator for InternGPT app.py --load and --tab launch plans.

This script intentionally does not import app.py or iGPT. It hard-codes the
exported model/tool class names and UI tabs observed during skill construction,
then checks a planned command for common static mistakes before any model import,
model download, credential use, Gradio launch, or GPU execution.

Examples:
  python scripts/validate_load_plan.py \
    --load "StyleGAN_cuda:0" --tab "DragGAN" --https --e-mode

  python scripts/validate_load_plan.py \
    --load "HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0" \
    --tab "Image" --port 3456

  python scripts/validate_load_plan.py \
    --load "ActionRecognition_cuda:0,VideoCaption_cuda:0,DenseCaption_cuda:0" \
    --tab "Video" --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable

DEFAULT_LOAD = "HuskyVQA_cuda:0,ImageOCRRecognition_cuda:0,SegmentAnything_cuda:0"
DEFAULT_TAB = "Audio,DragGAN,Image,Video"
SUPPORTED_TABS = ("Audio", "DragGAN", "Image", "Video")

# Exported from the model package evidence. Keep sorted for stable output.
KNOWN_EXPORTED_CLASSES = tuple(sorted({
    "ActionRecognition",
    "Anything2Image",
    "Audio2Image",
    "AudioImage2Image",
    "AudioText2Image",
    "CannyText2Image",
    "DenseCaption",
    "DepthText2Image",
    "ExtractMaskedAnything",
    "GenerateTikTokVideo",
    "HedText2Image",
    "HuskyVQA",
    "Image2Canny",
    "Image2Depth",
    "Image2Hed",
    "Image2Line",
    "Image2Normal",
    "Image2Pose",
    "Image2Scribble",
    "ImageOCRRecognition",
    "ImageText2Image",
    "InstructPix2Pix",
    "LDMInpainting",
    "LineText2Image",
    "NormalText2Image",
    "PoseText2Image",
    "ReplaceMaskedAnything",
    "ScribbleText2Image",
    "SegText2Image",
    "SegmentAnything",
    "StyleGAN",
    "Text2Image",
    "Thermal2Image",
    "VideoCaption",
}))

# Direct classes whose constructors accept the app.py direct load call pattern:
# globals()[class_name](device=device, e_mode=e_mode).
DIRECT_LOADABLE_CLASSES = tuple(sorted({
    "ActionRecognition",
    "Anything2Image",
    "CannyText2Image",
    "DenseCaption",
    "HuskyVQA",
    "Image2Canny",
    "Image2Hed",
    "Image2Line",
    "Image2Scribble",
    "ImageOCRRecognition",
    "LDMInpainting",
    "ReplaceMaskedAnything",
    "ScribbleText2Image",
    "SegText2Image",
    "SegmentAnything",
    "StyleGAN",
    "Text2Image",
    "VideoCaption",
}))

TEMPLATE_PREREQUISITES = {
    "Audio2Image": ("Anything2Image",),
    "Thermal2Image": ("Anything2Image",),
    "AudioImage2Image": ("Anything2Image",),
    "AudioText2Image": ("Anything2Image",),
    "ExtractMaskedAnything": ("SegmentAnything",),
    "ImageText2Image": ("SegText2Image", "SegmentAnything"),
    "GenerateTikTokVideo": ("ActionRecognition", "VideoCaption", "DenseCaption"),
}

# Exported classes that are not template-only but do not accept the current app
# direct-load e_mode keyword/argument pattern.
EXPORTED_BUT_NOT_APP_CLI_LOADABLE = tuple(sorted(
    set(KNOWN_EXPORTED_CLASSES) - set(DIRECT_LOADABLE_CLASSES) - set(TEMPLATE_PREREQUISITES)
))

TAB_GUIDANCE = {
    "DragGAN": {
        "required_any": ("StyleGAN",),
        "message": "DragGAN tab needs StyleGAN in --load; use StyleGAN_cuda:0, not DragGAN_cuda:0.",
    },
    "Image": {
        "recommended_any": ("HuskyVQA", "SegmentAnything", "ImageOCRRecognition", "Text2Image", "LDMInpainting", "ReplaceMaskedAnything"),
        "message": "Image tab is most useful with image/VQA/SAM/OCR/generation classes loaded.",
    },
    "Audio": {
        "recommended_any": ("Anything2Image",),
        "message": "Audio ImageBind generation needs Anything2Image; browser microphone use also expects HTTPS.",
    },
    "Video": {
        "recommended_any": ("VideoCaption", "ActionRecognition", "DenseCaption"),
        "message": "Video tab is most useful with VideoCaption, ActionRecognition, or DenseCaption loaded.",
    },
}

DEVICE_RE = re.compile(r"^(cpu|mps|cuda(?::\d+)?|rocm(?::\d+)?|xpu(?::\d+)?)$")
CUDA_RE = re.compile(r"^cuda(?::\d+)?$")


@dataclass(frozen=True)
class LoadItem:
    class_name: str
    device: str
    raw: str


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_load(load_string: str, errors: list[str], warnings: list[str]) -> list[LoadItem]:
    parts = split_csv(load_string)
    if not parts:
        errors.append("--load is empty; provide at least one <ClassName>_<device> item.")
        return []

    items: list[LoadItem] = []
    seen: dict[str, str] = {}
    for raw in parts:
        if raw.count("_") != 1:
            errors.append(f"Load item {raw!r} must contain exactly one underscore: <ClassName>_<device>.")
            continue
        class_name, device = [piece.strip() for piece in raw.split("_", 1)]
        if not class_name or not device:
            errors.append(f"Load item {raw!r} has an empty class name or device.")
            continue
        if class_name not in KNOWN_EXPORTED_CLASSES:
            errors.append(f"Unknown exported class {class_name!r} in load item {raw!r}.")
        elif class_name in TEMPLATE_PREREQUISITES:
            prereq = ", ".join(TEMPLATE_PREREQUISITES[class_name])
            errors.append(f"{class_name} is template-only; load its prerequisite(s) instead: {prereq}.")
        elif class_name in EXPORTED_BUT_NOT_APP_CLI_LOADABLE:
            errors.append(
                f"{class_name} is exported but is not a safe direct app.py --load class in this app version."
            )
        elif class_name not in DIRECT_LOADABLE_CLASSES:
            errors.append(f"{class_name} is not supported as a direct app.py --load class.")

        if not DEVICE_RE.match(device):
            warnings.append(f"Device {device!r} for {class_name} is unusual; common values are cuda:0, cuda:1, cpu, or mps.")
        if class_name in seen:
            warnings.append(
                f"Duplicate class {class_name!r}: app.py stores load entries in a dict, so {seen[class_name]!r} is overwritten by {raw!r}."
            )
        seen[class_name] = raw
        items.append(LoadItem(class_name=class_name, device=device, raw=raw))
    return items


def parse_tabs(tab_string: str, errors: list[str]) -> list[str]:
    tabs = split_csv(tab_string)
    if not tabs:
        errors.append("--tab is empty; choose one or more of Audio, DragGAN, Image, Video.")
        return []
    for tab in tabs:
        if tab not in SUPPORTED_TABS:
            errors.append(f"Unknown tab {tab!r}; supported tabs are: {', '.join(SUPPORTED_TABS)}.")
    return tabs


def derive_templates(loaded_classes: Iterable[str]) -> list[str]:
    loaded = set(loaded_classes)
    derived = []
    for template, prereqs in sorted(TEMPLATE_PREREQUISITES.items()):
        if set(prereqs).issubset(loaded):
            derived.append(template)
    return derived


def validate_relationships(
    items: list[LoadItem], tabs: list[str], https: bool, debug: bool, e_mode: bool, warnings: list[str], errors: list[str]
) -> None:
    loaded = {item.class_name for item in items}

    for tab in tabs:
        guidance = TAB_GUIDANCE.get(tab, {})
        required_any = guidance.get("required_any", ())
        recommended_any = guidance.get("recommended_any", ())
        if required_any and not any(cls in loaded for cls in required_any):
            errors.append(guidance["message"])
        if recommended_any and not any(cls in loaded for cls in recommended_any):
            warnings.append(guidance["message"])

    if "Audio" in tabs and not https:
        warnings.append("Audio tab can render without --https, but browser microphone/voice workflows commonly require HTTPS.")

    if debug:
        warnings.append("--debug bypasses the UI key gate, but it is only a local-debug convenience and does not remove backend credential requirements for real chat calls.")

    if "StyleGAN" in loaded and "DragGAN" not in tabs:
        warnings.append("StyleGAN is loaded but DragGAN tab is not enabled; add --tab DragGAN if the user needs interactive dragging.")

    if "Anything2Image" in loaded and "Audio" not in tabs:
        warnings.append("Anything2Image is loaded but Audio tab is not enabled; enable Audio for upload-driven ImageBind workflows.")

    if "GenerateTikTokVideo" in derive_templates(loaded):
        warnings.append("GenerateTikTokVideo will be auto-created; it also needs OpenAI credentials, ffmpeg, Bark/speech dependencies, and video checkpoints.")

    if not any(CUDA_RE.match(item.device) for item in items):
        warnings.append("The app initializes a speech model on cuda:0 during startup; a non-CUDA --load plan may still fail without CUDA.")

    if e_mode:
        warnings.append("--e-mode saves VRAM for wrappers that implement offload, but it is not CPU-only mode and does not remove checkpoint requirements.")

    if https:
        warnings.append("--https expects certificate/cert.pem and certificate/key.pem in the app working directory.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate InternGPT app.py --load/--tab launch plans without importing app.py or iGPT.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  python scripts/validate_load_plan.py --load 'StyleGAN_cuda:0' --tab DragGAN --https --e-mode\n"
        "  python scripts/validate_load_plan.py --load 'HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0' --tab Image\n"
        "  python scripts/validate_load_plan.py --load 'ActionRecognition_cuda:0,VideoCaption_cuda:0,DenseCaption_cuda:0' --tab Video --json",
    )
    parser.add_argument("--load", default=DEFAULT_LOAD, help=f"Comma-separated <ClassName>_<device> items. Default: {DEFAULT_LOAD}")
    parser.add_argument("--tab", default=DEFAULT_TAB, help=f"Comma-separated tabs. Default: {DEFAULT_TAB}")
    parser.add_argument("--port", type=int, default=7862, help="Planned Gradio port; checked for a valid range only.")
    parser.add_argument("--https", action="store_true", help="Validate with HTTPS expectations enabled.")
    parser.add_argument("--debug", "-d", action="store_true", help="Include debug-login caveats for the app UI.")
    parser.add_argument("--e-mode", "-e", action="store_true", help="Include e-mode memory-saving caveats.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation output.")
    parser.add_argument("--list-known", action="store_true", help="Print known classes/tabs and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_known:
        print("Known exported classes:")
        for name in KNOWN_EXPORTED_CLASSES:
            marker = "direct"
            if name in TEMPLATE_PREREQUISITES:
                marker = "template-only"
            elif name in EXPORTED_BUT_NOT_APP_CLI_LOADABLE:
                marker = "exported-not-direct-cli"
            print(f"  {name} ({marker})")
        print("Supported tabs:", ", ".join(SUPPORTED_TABS))
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not (1 <= args.port <= 65535):
        errors.append(f"Port {args.port} is outside the valid TCP range 1-65535.")

    items = parse_load(args.load, errors, warnings)
    tabs = parse_tabs(args.tab, errors)
    validate_relationships(items, tabs, args.https, args.debug, args.e_mode, warnings, errors)
    loaded_classes = [item.class_name for item in items]
    derived = derive_templates(loaded_classes)

    result = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "load_items": [item.__dict__ for item in items],
        "tabs": tabs,
        "derived_template_classes": derived,
        "port": args.port,
        "https": args.https,
        "e_mode": args.e_mode,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("InternGPT launch-plan validation")
        print(f"  load: {args.load}")
        print(f"  tabs: {args.tab}")
        print(f"  port: {args.port}")
        if items:
            print("  parsed load items:")
            for item in items:
                print(f"    - {item.class_name} on {item.device}")
        if derived:
            print("  auto-created template classes if prerequisites load:")
            for name in derived:
                print(f"    - {name}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  WARN: {warning}")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("OK: no static load/tab errors found.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
