#!/usr/bin/env python3
"""Check a PaddleDetection runtime environment without running training.

Examples:
  python check_paddledet_environment.py
  python check_paddledet_environment.py --config configs/ppyoloe/ppyoloe_crn_s_300e_coco.yml
  python check_paddledet_environment.py --expect-cuda
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def try_import(name: str):
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__version__", None), None
    except Exception as exc:  # pragma: no cover - diagnostic script
        return False, None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight PaddleDetection imports, optional modules, device, and config loading.")
    parser.add_argument("--config", help="Optional PaddleDetection YAML config to load from a target checkout.")
    parser.add_argument("--repo-root", help="Optional target PaddleDetection checkout to add to sys.path before importing ppdet.")
    parser.add_argument("--expect-cuda", action="store_true", help="Fail if PaddlePaddle is not compiled with CUDA.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if args.repo_root:
        root = Path(args.repo_root).resolve()
        if not root.exists():
            print(f"ERROR: repo root does not exist: {root}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(root))

    report = {"python": sys.version.split()[0], "imports": {}, "device": {}, "config": None, "warnings": []}

    for name in ["paddle", "ppdet", "cv2", "yaml", "pycocotools", "visualdl"]:
        ok, version, error = try_import(name)
        report["imports"][name] = {"ok": ok, "version": version, "error": error}

    optional = ["numba", "sahi", "paddle_serving_client", "paddle2onnx", "fastdeploy"]
    for name in optional:
        ok, version, error = try_import(name)
        report["imports"][name] = {"ok": ok, "version": version, "error": error, "optional": True}

    if report["imports"].get("paddle", {}).get("ok"):
        import paddle

        report["device"]["compiled_with_cuda"] = bool(paddle.is_compiled_with_cuda())
        try:
            report["device"]["device"] = paddle.device.get_device()
        except Exception as exc:
            report["device"]["device_error"] = f"{type(exc).__name__}: {exc}"
        if args.expect_cuda and not report["device"].get("compiled_with_cuda"):
            report["warnings"].append("Expected CUDA, but this PaddlePaddle build is CPU-only.")

    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            report["config"] = {"ok": False, "error": f"Config not found: {args.config}"}
        elif not report["imports"].get("ppdet", {}).get("ok"):
            report["config"] = {"ok": False, "error": "Cannot load config because ppdet import failed."}
        else:
            try:
                from ppdet.core.workspace import load_config

                cfg = load_config(str(cfg_path))
                report["config"] = {
                    "ok": True,
                    "filename": getattr(cfg, "filename", None),
                    "architecture": getattr(cfg, "architecture", None),
                    "metric": getattr(cfg, "metric", None),
                    "num_classes": getattr(cfg, "num_classes", None),
                    "save_dir": getattr(cfg, "save_dir", None),
                }
            except Exception as exc:  # pragma: no cover - diagnostic script
                report["config"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    failures = [name for name, item in report["imports"].items() if not item.get("ok") and not item.get("optional")]
    if args.expect_cuda and not report["device"].get("compiled_with_cuda"):
        failures.append("cuda")
    if report.get("config") and not report["config"].get("ok"):
        failures.append("config")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PaddleDetection environment report")
        print(json.dumps(report, indent=2, sort_keys=True))
        if failures:
            print("FAILED checks: " + ", ".join(failures), file=sys.stderr)
        else:
            print("Required checks passed. Optional missing modules may still block selected workflows.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
