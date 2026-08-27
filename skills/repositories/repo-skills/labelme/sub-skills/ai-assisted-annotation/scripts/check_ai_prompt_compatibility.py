#!/usr/bin/env python3
"""Check labelme AI prompt/model compatibility before model download or inference."""

from __future__ import annotations

import argparse
import json

AI_ASSIST_MODELS = {
    "efficientsam:10m": {"display": "EfficientSam (speed)", "points": True, "box": True},
    "efficientsam:latest": {"display": "EfficientSam (accuracy)", "points": True, "box": True},
    "sam:100m": {"display": "Sam (speed)", "points": True, "box": True},
    "sam:300m": {"display": "Sam (balanced)", "points": True, "box": True},
    "sam:latest": {"display": "Sam (accuracy)", "points": True, "box": True},
    "sam2:small": {"display": "Sam2 (speed)", "points": True, "box": True},
    "sam2:latest": {"display": "Sam2 (balanced)", "points": True, "box": True},
    "sam2:large": {"display": "Sam2 (accuracy)", "points": True, "box": True},
    "sam3:latest": {"display": "Sam3", "points": False, "box": True},
}
AI_TEXT_MODELS = {
    "yoloworld:latest": {"display": "YOLO-World (fast)", "text": True},
    "sam3:latest": {"display": "SAM3 (smart)", "text": True},
}
MASK_REQUIRED_OUTPUTS = {"polygon", "mask"}
BBOX_OK_OUTPUTS = {"rectangle", "oriented_rectangle", "circle"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="model id such as sam2:latest, sam3:latest, or yoloworld:latest")
    parser.add_argument("--prompt", choices=["points", "box", "text"], required=True)
    parser.add_argument("--output-format", choices=["polygon", "mask", "rectangle", "oriented_rectangle", "circle"], default="polygon")
    parser.add_argument("--detections-have-masks", action="store_true", help="set when the model response is known to include masks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.prompt == "text":
        models = AI_TEXT_MODELS
    else:
        models = AI_ASSIST_MODELS
    info = models.get(args.model)
    ok = bool(info and info.get(args.prompt, False))
    reasons = []
    if info is None:
        reasons.append("model is not in labelme's built-in list for this prompt surface")
    elif not info.get(args.prompt, False):
        reasons.append(f"{args.model} does not support {args.prompt} prompts")

    if ok and args.output_format in MASK_REQUIRED_OUTPUTS and not args.detections_have_masks:
        reasons.append(
            f"{args.output_format} output requires model detections with masks; bbox-only detections are dropped"
        )
    elif ok and args.output_format in BBOX_OK_OUTPUTS:
        reasons.append(f"{args.output_format} can be built from bbox detections")

    report = {
        "model": args.model,
        "prompt": args.prompt,
        "outputFormat": args.output_format,
        "compatible": ok,
        "notes": reasons,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("compatible" if ok else "incompatible")
        for reason in reasons:
            print(f"- {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
