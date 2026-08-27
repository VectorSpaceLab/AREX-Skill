#!/usr/bin/env python3
"""Validate Fast Style Transfer evaluate.py image stylization inputs safely.

The helper checks path semantics, image dimensions, output mapping, device
strings, and batch size. It does not restore checkpoints or run TensorFlow
inference.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _image_info(path: Path) -> Dict[str, Any]:
    try:
        from PIL import Image
        with Image.open(path) as img:
            return {"file": path.name, "ok": True, "mode": img.mode, "size": list(img.size)}
    except Exception as exc:
        return {"file": path.name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _list_files(path: Path) -> List[Path]:
    return sorted([p for p in path.iterdir() if p.is_file()])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate evaluate.py input/output paths and image dimensions without stylizing images.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint directory or checkpoint file/prefix.")
    parser.add_argument("--in-path", required=True, help="Input image file or directory.")
    parser.add_argument("--out-path", required=True, help="Output image file or directory.")
    parser.add_argument("--device", default="/gpu:0", help="TensorFlow device string such as /cpu:0 or /gpu:0.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for directory processing; must be positive.")
    parser.add_argument("--allow-different-dimensions", action="store_true", help="Allow mixed-size directory inputs by grouping dimensions.")
    parser.add_argument("--sample-count", type=int, default=20, help="Maximum directory files to inspect for dimensions.")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checkpoint = Path(args.checkpoint).expanduser()
    in_path = Path(args.in_path).expanduser()
    out_path = Path(args.out_path).expanduser()
    report: Dict[str, Any] = {"ok": True, "errors": [], "warnings": [], "paths": {}, "inputs": {}, "output_mapping": {}, "dimension_groups": {}}

    if not checkpoint.exists():
        report["errors"].append("checkpoint path does not exist")
    report["paths"]["checkpoint"] = {"path": str(args.checkpoint), "exists": checkpoint.exists(), "is_dir": checkpoint.is_dir() if checkpoint.exists() else None}

    if not in_path.exists():
        report["errors"].append("input path does not exist")
    report["paths"]["in_path"] = {"path": str(args.in_path), "exists": in_path.exists(), "is_dir": in_path.is_dir() if in_path.exists() else None}
    report["paths"]["out_path"] = {"path": str(args.out_path), "exists": out_path.exists(), "is_dir": out_path.is_dir() if out_path.exists() else None}

    if args.batch_size <= 0:
        report["errors"].append("batch-size must be positive")
    if not (args.device.startswith("/cpu") or args.device.startswith("/gpu")):
        report["warnings"].append("device string is unusual for this TensorFlow script")

    if in_path.exists() and in_path.is_file():
        info = _image_info(in_path)
        report["inputs"]["mode"] = "file"
        report["inputs"]["sample"] = [info]
        if not info.get("ok"):
            report["errors"].append("input file is not a readable image")
        if out_path.exists() and out_path.is_dir():
            report["output_mapping"] = {"mode": "file-to-existing-dir", "output": str(out_path / in_path.name)}
        else:
            report["output_mapping"] = {"mode": "file-to-file", "output": str(out_path)}
    elif in_path.exists() and in_path.is_dir():
        files = _list_files(in_path)
        sampled = files[: max(args.sample_count, 0)]
        infos = [_image_info(p) for p in sampled]
        report["inputs"] = {"mode": "directory", "file_count_top_level": len(files), "sample": infos}
        if not out_path.exists() or not out_path.is_dir():
            report["warnings"].append("directory input normally expects an existing output directory")
        groups: Dict[str, List[str]] = defaultdict(list)
        for info in infos:
            if info.get("ok"):
                groups[str(info["size"])].append(info["file"])
            else:
                report["warnings"].append(f"sampled file {info['file']} is not a readable image")
        report["dimension_groups"] = groups
        if len(groups) > 1 and not args.allow_different_dimensions:
            report["errors"].append("sampled directory images have different dimensions; use --allow-different-dimensions or resize")
        report["output_mapping"] = {"mode": "directory-to-directory", "example_outputs": [str(out_path / p.name) for p in sampled[:5]]}

    report["ok"] = not report["errors"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
