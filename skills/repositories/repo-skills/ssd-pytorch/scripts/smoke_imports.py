#!/usr/bin/env python3
"""No-download import/model smoke checks for SSD.PyTorch."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any


def status_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "version": getattr(module, "__version__", "unknown")}
    except Exception as exc:  # noqa: BLE001 - diagnostic smoke checker
        result = {"name": name, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        if "coco_labels.txt" in str(exc):
            result["hint"] = "Set up the COCO label map or rerun with --coco-label-map so package-level data imports can complete."
        return result


def prepare_temp_home(label_map: str | None) -> tempfile.TemporaryDirectory[str] | None:
    if not label_map:
        return None
    src = Path(label_map).expanduser()
    tmp = tempfile.TemporaryDirectory(prefix="ssd-pytorch-home-")
    target = Path(tmp.name) / "data" / "coco" / "coco_labels.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
    os.environ["HOME"] = tmp.name
    return tmp


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe SSD.PyTorch import checks")
    parser.add_argument("--repo-root", default=None, help="optional source root to prepend to sys.path for this process")
    parser.add_argument("--coco-label-map", default=None, help="optional coco_labels.txt copied into a temporary HOME for import-only checks")
    parser.add_argument("--build-model", action="store_true", help="construct build_ssd('train', 300, 21)")
    parser.add_argument("--run-forward", action="store_true", help="also run a train-phase zero forward when --build-model is set")
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(Path(args.repo_root).expanduser()))

    temp_home = prepare_temp_home(args.coco_label_map)
    report: dict[str, Any] = {
        "ok": True,
        "imports": [],
        "notes": ["No datasets, weights, downloads, webcam, or GUI windows are used."],
    }

    try:
        for name in ["torch", "torchvision", "cv2", "numpy", "PIL"]:
            report["imports"].append(status_import(name))

        repo_modules = ["data.config", "data.voc0712", "data.coco", "data", "layers.box_utils", "ssd", "utils.augmentations"]
        for name in repo_modules:
            report["imports"].append(status_import(name))

        if args.build_model:
            try:
                torch = importlib.import_module("torch")
                ssd = importlib.import_module("ssd")
                net = ssd.build_ssd("train", 300, 21)
                model_report: dict[str, Any] = {
                    "class": type(net).__name__ if net is not None else None,
                    "size": getattr(net, "size", None),
                    "num_classes": getattr(net, "num_classes", None),
                    "prior_shape": list(getattr(net, "priors").shape) if net is not None and hasattr(net, "priors") else None,
                    "loc_heads": len(getattr(net, "loc", [])) if net is not None else None,
                    "conf_heads": len(getattr(net, "conf", [])) if net is not None else None,
                }
                if args.run_forward:
                    net.eval()
                    with torch.no_grad():
                        out = net(torch.zeros(1, 3, 300, 300))
                    model_report["forward_shapes"] = [list(item.shape) for item in out]
                report["model"] = model_report
            except Exception as exc:  # noqa: BLE001
                report["ok"] = False
                report["model_error"] = {"type": type(exc).__name__, "error": str(exc), "traceback_tail": traceback.format_exc().splitlines()[-8:]}

        failed = [item for item in report["imports"] if not item.get("ok")]
        if failed:
            report["ok"] = False
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1
    finally:
        if temp_home is not None:
            temp_home.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
