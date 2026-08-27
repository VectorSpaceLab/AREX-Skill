#!/usr/bin/env python3
"""Print a safe Mask_RCNN training plan summary.

This helper does not train. It helps choose the config, weight source, layer
stage, and data requirements before writing a project-specific training script.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan a Mask_RCNN training run.")
    ap.add_argument("--dataset-train", type=Path, required=True, help="Training dataset root.")
    ap.add_argument("--dataset-val", type=Path, required=True, help="Validation dataset root.")
    ap.add_argument("--classes", type=int, required=True, help="Foreground class count.")
    ap.add_argument("--weights", choices=["coco", "imagenet", "last", "path"], default="coco")
    ap.add_argument("--weights-path", type=Path, help="Path to a custom .h5 checkpoint when --weights path.")
    ap.add_argument("--layers", default="heads", help="Layer stage, e.g. heads, 4+, all.")
    ap.add_argument("--image-min-dim", type=int, default=512)
    ap.add_argument("--image-max-dim", type=int, default=512)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--learning-rate", type=float, default=0.001)
    ap.add_argument("--output-json", action="store_true")
    args = ap.parse_args()

    summary = {
        "dataset_train": str(args.dataset_train),
        "dataset_val": str(args.dataset_val),
        "num_classes": 1 + args.classes,
        "weights": args.weights,
        "weights_path": str(args.weights_path) if args.weights_path else None,
        "layers": args.layers,
        "image_min_dim": args.image_min_dim,
        "image_max_dim": args.image_max_dim,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "checks": [
            "verify datasets are prepared and contain images",
            "verify class count includes background",
            "verify dimensions are compatible with Mask_RCNN graph constraints",
            "verify weight source matches class count",
        ],
        "notes": [
            "Start with heads for transfer learning; route data layout fixes to data-preparation.",
            "Use CPU only for smoke tests; real training is usually GPU-oriented.",
        ],
    }

    if args.weights == "path" and not args.weights_path:
        ap.error("--weights-path is required when --weights path")

    if args.output_json:
        print(json.dumps(summary, indent=2))
    else:
        print("Mask_RCNN training plan")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
