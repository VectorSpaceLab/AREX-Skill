#!/usr/bin/env python3
"""Print Ultralytics Results attribute expectations without loading models.

This helper is safe for documentation and CI smoke checks because it imports the
public results classes only; it does not construct YOLO models, download weights,
read media, or run inference.
"""

from __future__ import annotations

import argparse
import inspect
import json
from collections import OrderedDict


FALLBACK_SIGNATURES = OrderedDict(
    [
        (
            "Results",
            "(orig_img, path, names, boxes=None, masks=None, probs=None, keypoints=None, obb=None, speed=None, semantic_mask=None)",
        ),
        ("Boxes", "(boxes, orig_shape)"),
        ("Masks", "(masks, orig_shape)"),
        ("Keypoints", "(keypoints, orig_shape)"),
        ("Probs", "(probs, orig_shape=None)"),
        ("OBB", "(boxes, orig_shape)"),
        ("SemanticMask", "(data, orig_shape)"),
    ]
)

TASK_CONTRACT = OrderedDict(
    [
        (
            "detect",
            {
                "present": ["boxes"],
                "absent": ["masks", "keypoints", "probs", "obb", "semantic_mask"],
                "primary": ["result.boxes.xyxy", "result.boxes.xywhn", "result.boxes.conf", "result.boxes.cls"],
            },
        ),
        (
            "segment",
            {
                "present": ["boxes", "masks"],
                "absent": ["keypoints", "probs", "obb", "semantic_mask"],
                "primary": ["result.masks.data", "result.masks.xy", "result.masks.xyn", "result.boxes.cls"],
            },
        ),
        (
            "semantic",
            {
                "present": ["semantic_mask"],
                "absent": ["boxes", "masks", "keypoints", "probs", "obb"],
                "primary": ["result.semantic_mask.data", "result.summary(normalize=False)"],
            },
        ),
        (
            "classify",
            {
                "present": ["probs"],
                "absent": ["boxes", "masks", "keypoints", "obb", "semantic_mask"],
                "primary": ["result.probs.top1", "result.probs.top1conf", "result.probs.top5", "result.probs.top5conf"],
            },
        ),
        (
            "pose",
            {
                "present": ["boxes", "keypoints"],
                "absent": ["masks", "probs", "obb", "semantic_mask"],
                "primary": ["result.keypoints.xy", "result.keypoints.xyn", "result.keypoints.conf"],
            },
        ),
        (
            "obb",
            {
                "present": ["obb"],
                "absent": ["boxes", "masks", "keypoints", "probs", "semantic_mask"],
                "primary": ["result.obb.xywhr", "result.obb.xyxyxyxy", "result.obb.xyxyxyxyn", "result.obb.conf"],
            },
        ),
    ]
)

SNIPPETS = OrderedDict(
    [
        (
            "memory_safe_stream",
            """for result in model.predict(source='video.mp4', stream=True):\n    rows = result.summary(normalize=True)\n    # Store rows or counters, not every Results object.\n""",
        ),
        (
            "detect_boxes",
            """if result.boxes is not None:\n    boxes = result.boxes.xyxy.cpu().tolist()\n    classes = result.boxes.cls.int().cpu().tolist()\n""",
        ),
        (
            "classification",
            """if result.probs is not None:\n    top1 = result.probs.top1\n    label = result.names[top1]\n    confidence = float(result.probs.top1conf)\n""",
        ),
        (
            "semantic_mask",
            """if result.semantic_mask is not None:\n    class_map = result.semantic_mask.data.cpu().numpy()\n    coverage = result.summary(normalize=False)\n""",
        ),
        (
            "oriented_boxes",
            """if result.obb is not None:\n    corners = result.obb.xyxyxyxy.cpu().tolist()\n    scores = result.obb.conf.cpu().tolist()\n""",
        ),
    ]
)


def load_result_classes() -> tuple[str, dict[str, str]]:
    """Import result classes and return status plus constructor signatures."""
    try:
        from ultralytics.engine.results import Boxes, Keypoints, Masks, OBB, Probs, Results, SemanticMask
    except ModuleNotFoundError as exc:
        return f"not importable: {exc.name}", dict(FALLBACK_SIGNATURES)

    classes = OrderedDict(
        [
            ("Results", Results),
            ("Boxes", Boxes),
            ("Masks", Masks),
            ("Keypoints", Keypoints),
            ("Probs", Probs),
            ("OBB", OBB),
            ("SemanticMask", SemanticMask),
        ]
    )
    return "imported", {name: str(inspect.signature(cls)) for name, cls in classes.items()}


def build_payload(include_snippets: bool) -> OrderedDict:
    """Build the printable contract payload."""
    import_status, signatures = load_result_classes()
    payload = OrderedDict()
    payload["import_status"] = import_status
    payload["class_signatures"] = signatures
    payload["task_contract"] = TASK_CONTRACT
    if include_snippets:
        payload["snippets"] = SNIPPETS
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print Ultralytics Results signatures and task-specific extraction expectations without inference."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--snippets", action="store_true", help="Include safe extraction snippets in the output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(include_snippets=args.snippets)
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("Ultralytics Results contract")
    print(f"Import status: {payload['import_status']}")
    print("\nClass signatures:")
    for name, signature in payload["class_signatures"].items():
        print(f"- {name}{signature}")

    print("\nTask-specific payloads:")
    for task, contract in payload["task_contract"].items():
        print(f"- {task}")
        print(f"  present: {', '.join(contract['present'])}")
        print(f"  absent: {', '.join(contract['absent'])}")
        print(f"  primary: {', '.join(contract['primary'])}")

    if args.snippets:
        print("\nSnippets:")
        for name, snippet in payload["snippets"].items():
            print(f"\n[{name}]\n{snippet.rstrip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
