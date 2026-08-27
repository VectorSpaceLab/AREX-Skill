#!/usr/bin/env python3
"""Check Android TFLite assets for a tensorflow-yolov4-tflite target app.

This helper only inspects files; it does not run Gradle, modify assets, or load
Android code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Android assets for tensorflow-yolov4-tflite.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--android-root", help="Target android/ directory containing app/src/main/assets.")
    group.add_argument("--assets-dir", help="Target app assets directory directly.")
    parser.add_argument("--model", default="yolov4-416-fp32.tflite", help="Expected TFLite model asset filename.")
    parser.add_argument("--labels", default="coco.txt", help="Expected labels asset filename.")
    parser.add_argument("--expected-classes", type=int, default=80, help="Expected number of label lines.")
    parser.add_argument("--min-model-bytes", type=int, default=1024, help="Minimum non-empty model size threshold.")
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir).expanduser().resolve() if args.assets_dir else (
        Path(args.android_root).expanduser().resolve() / "app" / "src" / "main" / "assets"
    )

    model_path = assets_dir / args.model
    labels_path = assets_dir / args.labels
    result: Dict[str, Any] = {
        "assets_dir": str(assets_dir),
        "model": args.model,
        "labels": args.labels,
        "ok": False,
        "checks": [],
        "warnings": [],
        "errors": [],
    }

    if not assets_dir.is_dir():
        result["errors"].append(f"assets directory not found: {assets_dir}")
    else:
        result["checks"].append("assets directory exists")

    if model_path.exists():
        size = model_path.stat().st_size
        result["model_bytes"] = size
        if size < args.min_model_bytes:
            result["errors"].append(f"model asset is unexpectedly small: {size} bytes")
        if model_path.suffix != ".tflite":
            result["warnings"].append("model asset does not use .tflite extension")
    else:
        result["errors"].append(f"model asset not found: {model_path}")

    if labels_path.exists():
        labels = [line.strip() for line in labels_path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        result["label_count"] = len(labels)
        result["first_label"] = labels[0] if labels else None
        result["last_label"] = labels[-1] if labels else None
        if len(labels) != args.expected_classes:
            result["errors"].append(
                f"label count {len(labels)} does not match expected classes {args.expected_classes}"
            )
    else:
        result["errors"].append(f"labels asset not found: {labels_path}")

    result["ok"] = not result["errors"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
