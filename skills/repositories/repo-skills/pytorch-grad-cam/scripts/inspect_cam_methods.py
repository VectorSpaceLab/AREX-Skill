#!/usr/bin/env python3
"""List grad-cam method classes and installed signatures safely.

This adapts method/flag knowledge from the repository's public examples without
loading pretrained models or reading the original checkout. Examples:

  python inspect_cam_methods.py --list-methods
  python inspect_cam_methods.py --signatures
"""

from __future__ import annotations

import argparse
import inspect

METHODS = {
    "gradcam": "GradCAM",
    "hirescam": "HiResCAM",
    "scorecam": "ScoreCAM",
    "gradcam++": "GradCAMPlusPlus",
    "ablationcam": "AblationCAM",
    "xgradcam": "XGradCAM",
    "eigencam": "EigenCAM",
    "eigengradcam": "EigenGradCAM",
    "layercam": "LayerCAM",
    "fullgrad": "FullGrad",
    "gradcamelementwise": "GradCAMElementWise",
    "kpcacam": "KPCA_CAM",
    "shapleycam": "ShapleyCAM",
    "finercam": "FinerCAM",
    "segeigencam": "SegEigenCAM",
    "refinecam": "RefineCAM",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect installed pytorch-grad-cam method names and signatures.")
    parser.add_argument("--list-methods", action="store_true", help="Print CLI-style method keys and class names.")
    parser.add_argument("--signatures", action="store_true", help="Print installed constructor signatures.")
    args = parser.parse_args()
    if not args.list_methods and not args.signatures:
        args.list_methods = True

    import pytorch_grad_cam

    if args.list_methods:
        for key, class_name in METHODS.items():
            status = "available" if hasattr(pytorch_grad_cam, class_name) else "missing"
            print(f"{key:18s} {class_name:24s} {status}")

    if args.signatures:
        for _, class_name in METHODS.items():
            obj = getattr(pytorch_grad_cam, class_name, None)
            if obj is None:
                continue
            try:
                print(f"{class_name}{inspect.signature(obj)}")
            except Exception as exc:  # pragma: no cover - diagnostic path
                print(f"{class_name}: could not inspect signature: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
