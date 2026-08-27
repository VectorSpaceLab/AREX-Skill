#!/usr/bin/env python3
"""Suggest an Ultralytics model family and task from text cues.

This script is intentionally static and offline: it does not import ultralytics,
load weights, touch media, or download assets.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Suggestion:
    family: str
    public_class: str
    task: str
    model_cues: list[str]
    expected_outputs: list[str]
    notes: list[str]


SUGGESTIONS = {
    "semantic": Suggestion(
        family="YOLO semantic segmentation",
        public_class="YOLO",
        task="semantic",
        model_cues=["yolo26*-sem.pt", "yolo26*-sem.yaml", "task=semantic", "CLI task: semantic"],
        expected_outputs=["result.semantic_mask", "dense HxW class-id map", "no default per-instance boxes"],
        notes=["Use for pixel-level scene labeling, not object tracking boxes."],
    ),
    "segment": Suggestion(
        family="YOLO instance segmentation",
        public_class="YOLO",
        task="segment",
        model_cues=["*-seg.pt", "*-seg.yaml", "CLI task: segment"],
        expected_outputs=["result.masks", "result.masks.data", "result.masks.xy", "usually result.boxes"],
        notes=["Use for one mask per detected object instance."],
    ),
    "detect": Suggestion(
        family="YOLO detection",
        public_class="YOLO",
        task="detect",
        model_cues=["yolo26n.pt", "yolo26*.yaml", "no task suffix", "CLI task: detect"],
        expected_outputs=["result.boxes", "boxes.xyxy", "boxes.conf", "boxes.cls"],
        notes=["Use for ordinary axis-aligned bounding boxes."],
    ),
    "classify": Suggestion(
        family="YOLO classification",
        public_class="YOLO",
        task="classify",
        model_cues=["*-cls.pt", "*-cls.yaml", "CLI task: classify"],
        expected_outputs=["result.probs", "top class probabilities"],
        notes=["Use for whole-image labels, not object locations."],
    ),
    "pose": Suggestion(
        family="YOLO pose estimation",
        public_class="YOLO",
        task="pose",
        model_cues=["*-pose.pt", "*-pose.yaml", "CLI task: pose"],
        expected_outputs=["result.keypoints", "result.boxes"],
        notes=["Use for keypoints attached to detected instances."],
    ),
    "obb": Suggestion(
        family="YOLO oriented bounding boxes",
        public_class="YOLO",
        task="obb",
        model_cues=["*-obb.pt", "*-obb.yaml", "CLI task: obb"],
        expected_outputs=["result.obb", "obb.xywhr", "rotated-box polygon accessors"],
        notes=["Use for rotated boxes; do not read ordinary boxes for angle data."],
    ),
    "world": Suggestion(
        family="YOLO-World open-vocabulary detection",
        public_class="YOLOWorld",
        task="detect",
        model_cues=["*world*.pt", "*world*.yaml", "YOLO(...-world...) auto-switch"],
        expected_outputs=["result.boxes", "open-vocabulary class names"],
        notes=["Call set_classes([...]); this is boxes, not masks."],
    ),
    "yoloe": Suggestion(
        family="YOLOE open-vocabulary detection/segmentation",
        public_class="YOLOE",
        task="detect or segment",
        model_cues=["yoloe-*.pt", "yoloe-*-seg.pt", "yoloe-*-pf.pt", "YOLO(yoloe-...) auto-switch"],
        expected_outputs=["result.boxes for detect", "result.masks for segment"],
        notes=["Supports text/classes and visual_prompts with matching bboxes and cls entries."],
    ),
    "sam3": Suggestion(
        family="SAM3 promptable concept segmentation",
        public_class="SAM or SAM3SemanticPredictor",
        task="segment",
        model_cues=["sam3.pt", "SAM3SemanticPredictor for text concepts"],
        expected_outputs=["segmentation masks for prompted concepts or visual prompts"],
        notes=["SAM3 weights are not automatically downloaded; text concept examples use SAM3SemanticPredictor."],
    ),
    "sam": Suggestion(
        family="SAM/SAM2 promptable segmentation",
        public_class="SAM",
        task="segment",
        model_cues=["sam_b.pt", "sam2*.pt", "*.pth"],
        expected_outputs=["result.masks", "prompted masks from bboxes/points/labels/masks"],
        notes=["Constructor requires .pt or .pth weights."],
    ),
    "fastsam": Suggestion(
        family="FastSAM promptable instance segmentation",
        public_class="FastSAM",
        task="segment",
        model_cues=["FastSAM-s.pt", "FastSAM-x.pt"],
        expected_outputs=["result.masks", "prompt-guided instance segmentation"],
        notes=["Uses weights only, not YAML; faster CNN-based alternative to SAM-style prompts."],
    ),
    "rtdetr": Suggestion(
        family="RT-DETR detection",
        public_class="RTDETR",
        task="detect",
        model_cues=["rtdetr-l.pt", "rtdetr-x.pt", "rtdetr-*.yaml"],
        expected_outputs=["result.boxes"],
        notes=["Detection-only; requires torch>=1.11."],
    ),
    "nas": Suggestion(
        family="YOLO-NAS detection",
        public_class="NAS",
        task="detect",
        model_cues=["yolo_nas_s.pt", "yolo_nas_m.pt", "yolo_nas_l.pt"],
        expected_outputs=["result.boxes"],
        notes=["Detection-only; Ultralytics does not support NAS training and constructor rejects YAML."],
    ),
}

KEYWORDS = [
    ("semantic", ["semantic", "dense", "class map", "class-map", "pixel", "scene parsing", "sem"]),
    ("sam3", ["sam3", "sam 3", "concept", "text prompt", "text-prompt", "exemplar", "noun phrase"]),
    ("world", ["yolo-world", "yolo world", "worldv2", "open vocabulary boxes", "open-vocabulary box"]),
    ("yoloe", ["yoloe", "seeing anything", "visual prompt", "prompt-free", "open vocabulary mask"]),
    ("fastsam", ["fastsam", "fast sam"]),
    ("sam", ["sam2", "sam 2", "sam", "segment anything", "point prompt", "box prompt"]),
    ("rtdetr", ["rtdetr", "rt-detr", "detr", "transformer detector"]),
    ("nas", ["yolo-nas", "yolo nas", "nas", "supergradients"]),
    ("obb", ["obb", "oriented", "rotated", "angle", "dota"]),
    ("pose", ["pose", "keypoint", "skeleton", "joint"]),
    ("classify", ["classify", "classification", "image label", "probs", "top1", "top5"]),
    ("segment", ["instance segmentation", "instance mask", "polygon", "mask per object", "seg", "masks"]),
    ("detect", ["detect", "detection", "box", "bbox", "bounding box"]),
]


def choose(cue: str) -> Suggestion:
    text = cue.lower()
    for key, words in KEYWORDS:
        if any(word in text for word in words):
            return SUGGESTIONS[key]
    return SUGGESTIONS["detect"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest an Ultralytics model family/task from a short cue.")
    parser.add_argument("--cue", required=True, help="Natural-language cue, e.g. 'dense semantic mask no boxes'.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args()

    suggestion = choose(args.cue)
    payload = asdict(suggestion)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Family: {suggestion.family}")
        print(f"Public class: {suggestion.public_class}")
        print(f"Task: {suggestion.task}")
        print("Model cues: " + ", ".join(suggestion.model_cues))
        print("Expected outputs: " + ", ".join(suggestion.expected_outputs))
        print("Notes: " + " ".join(suggestion.notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
