#!/usr/bin/env python3
"""Validate a Photo2Cartoon source tree and common external assets.

Safe by default: no downloads, no model execution, no imports from the target
repo. Use this before routing to inference, preprocessing, data/training, or
model-internals helpers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

REQUIRED_SOURCE = [
    "README.md",
    "README_EN.md",
    "cog.yaml",
    "test.py",
    "test_onnx.py",
    "data_process.py",
    "train.py",
    "predict.py",
    "dataset.py",
    "models/networks.py",
    "models/UGATIT_sadalin_hourglass.py",
    "models/face_features.py",
    "models/mobilefacenet.py",
    "utils/preprocess.py",
    "utils/face_detect.py",
    "utils/face_seg.py",
    "utils/utils.py",
    "dataset/README.md",
]

OPTIONAL_ASSETS = {
    "models/photo2cartoon_weights.pt": "PyTorch inference checkpoint with genA2B",
    "models/photo2cartoon_weights.onnx": "ONNX inference model",
    "models/model_mobilefacenet.pth": "Face ID training-loss model",
    "utils/seg_model_384.pb": "TensorFlow segmentation graph used by preprocessing",
    "dataset/photo2cartoon/trainA": "preprocessed real-photo training domain",
    "dataset/photo2cartoon/trainB": "cartoon training domain",
    "dataset/photo2cartoon/testA": "real-photo test domain",
    "dataset/photo2cartoon/testB": "cartoon test domain",
}


def check(root: Path, require_assets: bool) -> Dict[str, object]:
    source_rows: List[Dict[str, object]] = []
    for rel in REQUIRED_SOURCE:
        path = root / rel
        source_rows.append({"path": rel, "exists": path.exists(), "status": "pass" if path.exists() else "fail"})

    asset_rows: List[Dict[str, object]] = []
    for rel, purpose in OPTIONAL_ASSETS.items():
        path = root / rel
        exists = path.exists()
        status = "pass" if exists else ("fail" if require_assets else "warn")
        row: Dict[str, object] = {"path": rel, "purpose": purpose, "exists": exists, "status": status}
        if exists and path.is_file():
            row["bytes"] = path.stat().st_size
        asset_rows.append(row)

    failures = [row for row in source_rows + asset_rows if row["status"] == "fail"]
    warnings = [row for row in asset_rows if row["status"] == "warn"]
    return {
        "root": str(root),
        "source": source_rows,
        "assets": asset_rows,
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Photo2Cartoon source files and external asset placeholders.")
    parser.add_argument("--root", required=True, type=Path, help="Target Photo2Cartoon checkout root.")
    parser.add_argument("--require-assets", action="store_true", help="Fail if external model/data assets are missing.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        result = {"root": str(root), "status": "fail", "error": "root is not a directory"}
        print(json.dumps(result, indent=2) if args.json else f"FAIL root is not a directory: {root}")
        return 1

    result = check(root, args.require_assets)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Photo2Cartoon repository check: {str(result['status']).upper()} ({root})")
        for row in result["source"]:
            print(f"[{row['status'].upper()}] source {row['path']}")
        for row in result["assets"]:
            extra = f" ({row.get('bytes')} bytes)" if row.get("bytes") is not None else ""
            print(f"[{row['status'].upper()}] asset {row['path']}: {row['purpose']}{extra}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
