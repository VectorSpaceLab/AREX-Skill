#!/usr/bin/env python3
"""Check a Python environment for Waymo Open Dataset package usability."""
from __future__ import annotations
import argparse, importlib, json, sys
from importlib import metadata

def check_module(name: str) -> dict:
    try:
        mod = importlib.import_module(name)
        return {"module": name, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}

def main() -> int:
    parser = argparse.ArgumentParser(description="Check WOD package imports and optional backends.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--require-gpu", action="store_true", help="Fail if TensorFlow does not list a GPU device.")
    args = parser.parse_args()
    result = {"python": sys.version, "distributions": {}, "modules": [], "tensorflow": {}}
    for dist in ["waymo-open-dataset-tf-2-12-0", "tensorflow", "pyarrow", "pandas", "dask"]:
        try:
            result["distributions"][dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            result["distributions"][dist] = None
    modules = ["waymo_open_dataset", "waymo_open_dataset.v2", "waymo_open_dataset.v2.component", "waymo_open_dataset.utils.frame_utils", "waymo_open_dataset.metrics.python.config_util_py", "waymo_open_dataset.utils.sim_agents.submission_specs"]
    result["modules"] = [check_module(m) for m in modules]
    try:
        from waymo_open_dataset import v2
        result["v2_tags"] = list(v2.ALL_TAGS)
    except Exception as exc:
        result["v2_tags_error"] = f"{type(exc).__name__}: {exc}"
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        result["tensorflow"] = {"version": tf.__version__, "gpu_devices": [str(g) for g in gpus]}
    except Exception as exc:
        result["tensorflow"] = {"error": f"{type(exc).__name__}: {exc}"}
    failed = [m for m in result["modules"] if not m["ok"]]
    if args.require_gpu and not result.get("tensorflow", {}).get("gpu_devices"):
        failed.append({"module": "tensorflow-gpu", "error": "--require-gpu set but no GPU devices listed"})
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Waymo Open Dataset environment check")
        for k, v in result["distributions"].items(): print(f"  {k}: {v or 'missing'}")
        for item in result["modules"]: print(f"  {'OK' if item['ok'] else 'FAIL'} {item['module']}")
        if "v2_tags" in result: print(f"V2 component tags: {len(result['v2_tags'])}")
        print(f"TensorFlow: {result.get('tensorflow')}")
    return 1 if failed else 0
if __name__ == "__main__": raise SystemExit(main())
