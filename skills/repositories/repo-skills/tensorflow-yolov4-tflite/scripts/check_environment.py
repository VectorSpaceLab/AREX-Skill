#!/usr/bin/env python3
"""Non-destructive environment probe for a target tensorflow-yolov4-tflite checkout.

This helper validates dependency imports, repository-relative class/config paths,
and optional TensorFlow GPU visibility without downloading weights, running
models, or mutating files.

Example:
  python check_environment.py --repo-root /path/to/tensorflow-yolov4-tflite
  python check_environment.py --repo-root . --expect-gpu
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


def _module_version(module: Any, attr: str = "__version__") -> str:
    return str(getattr(module, attr, "unknown"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe tensorflow-yolov4-tflite runtime dependencies and config.")
    parser.add_argument("--repo-root", default=".", help="Target checkout root containing core/ and data/classes/.")
    parser.add_argument("--expect-gpu", action="store_true", help="Fail if TensorFlow imports but reports no GPU devices.")
    parser.add_argument("--skip-tensorflow", action="store_true", help="Only check checkout layout and class file; useful before TensorFlow is installed.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    result: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "ok": False,
        "checks": [],
        "warnings": [],
        "errors": [],
    }

    required_paths = [repo_root / "core" / "config.py", repo_root / "data" / "classes" / "coco.names"]
    for path in required_paths:
        if path.exists():
            result["checks"].append({"path_exists": str(path.relative_to(repo_root))})
        else:
            result["errors"].append(f"missing required checkout path: {path}")

    if result["errors"]:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    # Repo modules evaluate relative config defaults during import, so run imports
    # with cwd set to the target checkout root.
    original_cwd = Path.cwd()
    sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)
    try:
        if not args.skip_tensorflow:
            try:
                import tensorflow as tf  # type: ignore
                result["tensorflow_version"] = _module_version(tf)
                gpus: List[str] = [str(device) for device in tf.config.experimental.list_physical_devices("GPU")]
                result["tensorflow_gpus"] = gpus
                if args.expect_gpu and not gpus:
                    result["errors"].append("--expect-gpu was set but TensorFlow reported no GPU devices")
                elif not gpus:
                    result["warnings"].append("TensorFlow imported but reported no GPU devices; CPU workflows may still be usable")
            except Exception as exc:  # noqa: BLE001 - report concise diagnostic to user
                result["errors"].append(f"tensorflow import/check failed: {type(exc).__name__}: {exc}")

            try:
                import cv2  # type: ignore
                result["opencv_version"] = _module_version(cv2)
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"opencv import failed: {type(exc).__name__}: {exc}")

        try:
            from core.config import cfg  # type: ignore
            from core import utils  # type: ignore

            classes = utils.read_class_names(cfg.YOLO.CLASSES)
            result["class_file"] = cfg.YOLO.CLASSES
            result["class_count"] = len(classes)
            result["first_class"] = classes.get(0)
            result["last_class"] = classes.get(max(classes)) if classes else None
            if len(classes) != 80:
                result["warnings"].append(f"default class file has {len(classes)} classes, expected 80 for COCO")
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"repo config/class inspection failed: {type(exc).__name__}: {exc}")
    finally:
        os.chdir(original_cwd)

    result["ok"] = not result["errors"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
