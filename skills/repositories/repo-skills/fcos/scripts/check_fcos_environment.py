#!/usr/bin/env python3
"""Diagnose FCOS package, dependency, config, and backend availability.

This script is safe by default: it imports packages and optionally merges a
config file, but it does not download weights, run inference, open a display, or
start training.

Example:
  python check_fcos_environment.py --config configs/fcos/fcos_imprv_R_50_FPN_1x.yaml
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path


def check_import(name: str):
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "module": name, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # diagnostics should catch all
        return {"ok": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FCOS runtime availability without running models")
    parser.add_argument("--config", help="Optional FCOS YAML config to merge with fcos_core.config.cfg")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    report = {"python": sys.version.split()[0], "imports": {}, "torch": {}, "config": None, "notes": []}

    for name in ["torch", "torchvision", "yacs", "cv2", "skimage", "fcos_core.config"]:
        report["imports"][name] = check_import(name)

    try:
        import torch  # type: ignore
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
        }
        report["imports"]["fcos_core._C"] = check_import("fcos_core._C")
    except Exception as exc:
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
        report["imports"]["fcos_core._C"] = {"ok": False, "module": "fcos_core._C", "error": "torch import failed first"}

    report["imports"]["fcos"] = check_import("fcos")

    if args.config:
        cfg_path = Path(args.config)
        try:
            from fcos_core.config import cfg
            c = cfg.clone()
            c.merge_from_file(str(cfg_path))
            report["config"] = {
                "ok": True,
                "path": str(cfg_path),
                "model_fcos_on": bool(c.MODEL.FCOS_ON),
                "device": str(c.MODEL.DEVICE),
                "datasets_train": list(c.DATASETS.TRAIN),
                "datasets_test": list(c.DATASETS.TEST),
            }
        except Exception as exc:
            report["config"] = {
                "ok": False,
                "path": str(cfg_path),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=3),
            }

    if not report["imports"].get("fcos_core._C", {}).get("ok"):
        report["notes"].append("Real detector inference and compiled layer tests need fcos_core._C; config-only workflows may still be usable.")
    if report["torch"].get("cuda_available") is False:
        report["notes"].append("CUDA is not available to torch; use CPU-only validation or reduce scope for GPU workflows.")

    print(json.dumps(report, indent=2, sort_keys=True))
    required_ok = report["imports"].get("fcos_core.config", {}).get("ok", False)
    return 0 if required_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
