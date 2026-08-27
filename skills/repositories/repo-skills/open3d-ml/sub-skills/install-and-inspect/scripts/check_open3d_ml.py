#!/usr/bin/env python3
"""Safe Open3D-ML install/backend smoke check.

This helper imports only installed packages. It performs no network access,
dataset downloads, training, checkpoint loading, or GUI creation.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib import metadata
from pathlib import Path


def version_of(dist: str):
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def try_import(name: str):
    try:
        module = importlib.import_module(name)
        return {"ok": True, "module": name, "file": getattr(module, "__file__", None), "error": None}
    except Exception as exc:  # keep broad: optional backend imports raise many errors
        return {"ok": False, "module": name, "file": None, "error": f"{type(exc).__name__}: {exc}"}


def check_config(config_path: str | None):
    if not config_path:
        return None
    path = Path(config_path)
    result = {"path": str(path), "exists": path.exists(), "loaded": False, "error": None, "names": {}}
    if not path.exists():
        result["error"] = "config path does not exist"
        return result
    try:
        try:
            from open3d.ml.utils import Config
        except Exception:
            from ml3d.utils import Config  # fallback for standalone editable installs
        cfg = Config.load_from_file(str(path))
        for section in ("dataset", "model", "pipeline"):
            try:
                result["names"][section] = cfg[section].get("name")
            except Exception:
                result["names"][section] = None
        result["loaded"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check Open3D-ML imports and selected backend availability.")
    parser.add_argument("--framework", choices=["torch", "tf", "both"], default="torch",
                        help="Framework namespace to check. Default: torch.")
    parser.add_argument("--config", help="Optional Open3D-ML YAML config to load without running training.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero if the requested framework import or config load fails.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    report = {
        "python": {"version": sys.version.split()[0], "executable_basename": Path(sys.executable).name},
        "environment": {"OPEN3D_ML_ROOT_set": bool(os.environ.get("OPEN3D_ML_ROOT"))},
        "distributions": {d: version_of(d) for d in ["open3d", "ml3d", "torch", "tensorflow", "openvino", "numpy"]},
        "imports": {},
        "open3d_build": {},
        "frameworks": {},
        "config": None,
    }

    report["imports"]["open3d"] = try_import("open3d")
    if report["imports"]["open3d"]["ok"]:
        import open3d as o3d
        report["open3d_build"] = {
            "version": getattr(o3d, "__version__", None),
            "BUILD_PYTORCH_OPS": o3d._build_config.get("BUILD_PYTORCH_OPS"),
            "BUILD_TENSORFLOW_OPS": o3d._build_config.get("BUILD_TENSORFLOW_OPS"),
            "BUILD_GUI": o3d._build_config.get("BUILD_GUI"),
        }
        report["imports"]["open3d.ml"] = try_import("open3d.ml")
    else:
        report["imports"]["ml3d"] = try_import("ml3d")

    frameworks = ["torch", "tf"] if args.framework == "both" else [args.framework]
    for fw in frameworks:
        ns = f"open3d.ml.{fw}"
        fw_report = {"namespace": ns, "import": try_import(ns)}
        if fw == "torch" and fw_report["import"]["ok"]:
            try:
                import torch
                fw_report["torch_version"] = torch.__version__
                fw_report["cuda_available"] = bool(torch.cuda.is_available())
                fw_report["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
            except Exception as exc:
                fw_report["torch_probe_error"] = f"{type(exc).__name__}: {exc}"
        report["frameworks"][fw] = fw_report

    report["config"] = check_config(args.config)

    requested_ok = all(report["frameworks"][fw]["import"]["ok"] for fw in frameworks)
    config_ok = report["config"] is None or report["config"].get("loaded", False)
    ok = requested_ok and config_ok and report["imports"].get("open3d", {}).get("ok", False)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if not ok:
            print("\nSmoke check did not fully pass. Read references/troubleshooting.md for recovery paths.", file=sys.stderr)
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
