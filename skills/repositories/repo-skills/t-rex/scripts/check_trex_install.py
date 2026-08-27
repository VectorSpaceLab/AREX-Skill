#!/usr/bin/env python3
"""Check that the T-Rex2 Python package can be inspected offline.

This smoke check imports the public package, verifies the key wrapper methods,
constructs visual-prompt and embedding payloads without making network calls,
postprocesses a tiny fake API object list, and optionally exercises
``trex.visualize`` on a synthetic image.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline T-Rex2 package import, payload, and visualization smoke check.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    parser.add_argument("--skip-visualize", action="store_true", help="Skip the trex.visualize smoke check.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary: dict[str, Any] = {"checks": []}

    try:
        import numpy as np
        from PIL import Image
        import trex
        from trex import TRex2APIWrapper, visualize
        from trex.model_wrapper import encode_image
    except Exception as exc:
        print(f"T-Rex2 import check failed: {exc}", file=sys.stderr)
        return 1

    summary["package_exports"] = list(getattr(trex, "__all__", []))
    summary["TRex2APIWrapper_signature"] = str(inspect.signature(TRex2APIWrapper))
    summary["visualize_signature"] = str(inspect.signature(visualize))
    summary["checks"].append("imports")

    image = Image.new("RGB", (32, 24), color="white")
    encoded = encode_image(image)
    if not isinstance(encoded, str) or len(encoded) < 10:
        print("encode_image did not return a plausible base64 string", file=sys.stderr)
        return 1
    summary["checks"].append("encode_image")

    wrapper = TRex2APIWrapper("dummy-token")
    prompts = [
        {
            "image": image,
            "interactions": [
                {"type": "rect", "category_id": 1, "rect": [1, 2, 10, 12]},
            ],
        }
    ]
    visual_payload = wrapper.convert_visual_prompt(image, prompts, ["bbox", "embedding"])
    if visual_payload.get("model") != "T-Rex-2.0" or visual_payload.get("prompt", {}).get("type") != "visual_images":
        print("convert_visual_prompt returned an unexpected payload", file=sys.stderr)
        return 1
    embedding_payload = wrapper.convert_embedding_prompt(image, "ZmFrZQ==")
    if embedding_payload.get("prompt", {}).get("type") != "embedding":
        print("convert_embedding_prompt returned an unexpected payload", file=sys.stderr)
        return 1
    summary["checks"].append("payload_conversion")

    detections = wrapper.postprocess([{"score": 0.75, "category_id": 1, "bbox": [1, 2, 10, 12]}])
    expected = {"scores": [0.75], "labels": [1], "boxes": [[1, 2, 10, 12]]}
    if detections != expected:
        print(f"postprocess returned {detections!r}, expected {expected!r}", file=sys.stderr)
        return 1
    summary["checks"].append("postprocess")

    if not args.skip_visualize:
        render_target = {
            "scores": np.asarray(detections["scores"], dtype=float),
            "labels": np.asarray(detections["labels"]),
            "boxes": np.asarray(detections["boxes"], dtype=float),
        }
        rendered = visualize(image.copy(), render_target, draw_score=True)
        if rendered.size != image.size:
            print("visualize returned an image with an unexpected size", file=sys.stderr)
            return 1
        summary["checks"].append("visualize")

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("T-Rex2 offline smoke check passed: " + ", ".join(summary["checks"]))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
