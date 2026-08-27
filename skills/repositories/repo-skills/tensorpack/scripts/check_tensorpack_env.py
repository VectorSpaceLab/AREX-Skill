#!/usr/bin/env python3
"""Check Tensorpack runtime imports and optional dependencies.

This diagnostic is safe by default: it imports packages, reports versions and
optional dependency status, and exits nonzero only for dependencies explicitly
required by command-line flags. It does not train, download data, or inspect a
source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def module_status(name: str) -> Dict[str, Any]:
    try:
        module = __import__(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def tensorpack_status() -> Dict[str, Any]:
    try:
        import tensorpack  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "version": getattr(tensorpack, "__version__", None),
        "git_version": getattr(tensorpack, "__git_version__", None),
        "has_tensorflow": getattr(tensorpack, "_HAS_TF", None),
    }


def tensorflow_status() -> Dict[str, Any]:
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    devices = []
    try:
        devices = [d.name for d in tf.config.list_physical_devices("GPU")]
    except Exception as exc:
        devices = [f"device-query-error: {type(exc).__name__}: {exc}"]
    compat_v1 = hasattr(tf, "compat") and hasattr(tf.compat, "v1")
    return {
        "ok": True,
        "version": getattr(tf, "__version__", None),
        "compat_v1": bool(compat_v1),
        "gpu_devices": devices,
    }


def collect() -> Dict[str, Any]:
    return {
        "tensorpack": tensorpack_status(),
        "tensorflow": tensorflow_status(),
        "optional": {
            "cv2": module_status("cv2"),
            "lmdb": module_status("lmdb"),
            "h5py": module_status("h5py"),
            "pyarrow": module_status("pyarrow"),
            "diskcache": module_status("diskcache"),
            "gym": module_status("gym"),
            "caffe": module_status("caffe"),
        },
    }


def print_text(report: Dict[str, Any]) -> None:
    tp = report["tensorpack"]
    if tp["ok"]:
        print(f"tensorpack: OK version={tp.get('version')} has_tensorflow={tp.get('has_tensorflow')}")
    else:
        print(f"tensorpack: FAIL {tp['error']}")

    tf = report["tensorflow"]
    if tf["ok"]:
        print(
            "tensorflow: OK version={} compat_v1={} gpu_devices={}".format(
                tf.get("version"), tf.get("compat_v1"), len(tf.get("gpu_devices") or [])
            )
        )
        for dev in tf.get("gpu_devices") or []:
            print(f"  gpu: {dev}")
    else:
        print(f"tensorflow: FAIL {tf['error']}")

    for name, status in report["optional"].items():
        if status["ok"]:
            print(f"optional {name}: OK version={status.get('version')}")
        else:
            print(f"optional {name}: missing ({status['error']})")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report Tensorpack, TensorFlow, and optional dependency status."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--require-tf", action="store_true", help="Fail if TensorFlow is unavailable.")
    parser.add_argument("--require-cv2", action="store_true", help="Fail if OpenCV/cv2 is unavailable.")
    parser.add_argument("--require-lmdb", action="store_true", help="Fail if lmdb is unavailable.")
    parser.add_argument("--require-h5py", action="store_true", help="Fail if h5py is unavailable.")
    parser.add_argument("--require-gpu", action="store_true", help="Fail if TensorFlow sees no GPU devices.")
    args = parser.parse_args(argv)

    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    failures = []
    if not report["tensorpack"]["ok"]:
        failures.append("tensorpack")
    if args.require_tf and not report["tensorflow"]["ok"]:
        failures.append("tensorflow")
    if args.require_cv2 and not report["optional"]["cv2"]["ok"]:
        failures.append("cv2")
    if args.require_lmdb and not report["optional"]["lmdb"]["ok"]:
        failures.append("lmdb")
    if args.require_h5py and not report["optional"]["h5py"]["ok"]:
        failures.append("h5py")
    if args.require_gpu:
        tf_status = report["tensorflow"]
        if not tf_status["ok"] or not tf_status.get("gpu_devices"):
            failures.append("tensorflow-gpu")

    if failures:
        print("required checks failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
