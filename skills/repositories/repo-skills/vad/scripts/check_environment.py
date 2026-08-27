#!/usr/bin/env python3
"""Diagnose generic VAD dependency/CUDA readiness without data, downloads, or model building."""
from __future__ import annotations
import argparse, importlib, json, os, sys


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", help="optional VAD repository root to add to sys.path for plugin probing")
    p.add_argument("--plugin", action="store_true", help="probe projects.mmdet3d_plugin after base checks")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args(argv)
    if args.repo_root: sys.path.insert(0, os.path.abspath(args.repo_root))
    result = {"packages": {}, "cuda": None, "plugin": None, "ok": True}
    for name, module in (("torch", "torch"), ("mmcv-full", "mmcv"), ("mmdet", "mmdet"), ("mmsegmentation", "mmseg"), ("mmdetection3d", "mmdet3d")):
        try:
            mod = importlib.import_module(module)
            result["packages"][name] = {"ok": True, "version": getattr(mod, "__version__", None)}
        except Exception as exc:
            result["packages"][name] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
            result["ok"] = False
    try:
        import torch
        result["cuda"] = {"available": bool(torch.cuda.is_available()), "count": int(torch.cuda.device_count()), "version": torch.version.cuda}
        if not result["cuda"]["available"]: result["ok"] = False
    except Exception as exc: result["cuda"] = {"available": False, "error": str(exc)}; result["ok"] = False
    try:
        importlib.import_module("mmdet3d.ops")
        result["native_ops"] = {"ok": True}
    except Exception as exc:
        result["native_ops"] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
        result["ok"] = False
    if args.plugin:
        try:
            importlib.import_module("projects.mmdet3d_plugin")
            result["plugin"] = {"ok": True}
        except Exception as exc:
            result["plugin"] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}; result["ok"] = False
    if args.as_json: print(json.dumps(result, indent=2, default=str))
    else:
        for k, v in result["packages"].items(): print("%-18s %s" % (k, "OK" if v["ok"] else "FAIL: " + v["error"]))
        print("cuda:", result["cuda"])
        if result["plugin"] is not None: print("plugin:", result["plugin"])
        print("overall:", "READY_FOR_SELECTED_PROBES" if result["ok"] else "NOT_READY")
    return 0 if result["ok"] else 1

if __name__ == "__main__": raise SystemExit(main())
