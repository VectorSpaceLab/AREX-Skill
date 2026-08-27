#!/usr/bin/env python3
"""Check whether the current Python can inspect/use davidsandberg/facenet modules.

This script is intentionally read-only: it imports modules and reports versions, but
it does not download models, open cameras, train, or load checkpoints.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Dict, List

MODULES = [
    "tensorflow",
    "numpy",
    "scipy",
    "sklearn",
    "cv2",
    "h5py",
    "PIL",
    "facenet",
    "lfw",
    "align.detect_face",
    "models.inception_resnet_v1",
    "models.inception_resnet_v2",
    "models.squeezenet",
]


def module_version(module):
    for attr in ("__version__", "VERSION"):
        value = getattr(module, attr, None)
        if value is not None:
            return str(value)
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Facenet import/dependency readiness.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--expect-tf1", action="store_true", default=True, help="Fail when TensorFlow does not look like TF1.")
    args = parser.parse_args()

    results: Dict[str, Dict[str, str]] = {}
    failures: List[str] = []
    for name in MODULES:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            results[name] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
            failures.append(name)
        else:
            results[name] = {"status": "ok", "version": module_version(module)}

    tf_status = results.get("tensorflow", {})
    if args.expect_tf1 and tf_status.get("status") == "ok":
        try:
            import tensorflow as tf  # type: ignore
            has_tf1 = hasattr(tf, "Session") and hasattr(tf, "Graph") and hasattr(tf, "train") and hasattr(tf, "contrib")
        except Exception:
            has_tf1 = False
        results["tensorflow"]["tf1_apis"] = "ok" if has_tf1 else "missing"
        if not has_tf1:
            failures.append("tensorflow.tf1_apis")

    payload = {"python": sys.version, "results": results, "ok": not failures, "failures": failures}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {sys.version.split()[0]}")
        for name in MODULES:
            item = results[name]
            if item["status"] == "ok":
                extra = f" version={item.get('version', 'unknown')}"
                if name == "tensorflow":
                    extra += f" tf1_apis={item.get('tf1_apis', 'not-checked')}"
                print(f"OK   {name}{extra}")
            else:
                print(f"FAIL {name}: {item['error']}")
        if failures:
            print("Failures: " + ", ".join(failures), file=sys.stderr)

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
