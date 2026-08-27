#!/usr/bin/env python3
"""Check a public DeepCTR installation without relying on a source checkout.

Example:
  python check_deepctr_env.py --json
  python check_deepctr_env.py --fail-if-no-estimator
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DeepCTR, TensorFlow, and optional backend availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--fail-if-no-estimator", action="store_true", help="Return non-zero if tf.estimator is unavailable.")
    parser.add_argument("--fail-if-no-gpu", action="store_true", help="Return non-zero if TensorFlow sees no GPU devices.")
    args = parser.parse_args()

    report = {
        "python": sys.version.split()[0],
        "ok": False,
        "deepctr": None,
        "tensorflow": None,
        "imports": {},
        "api_signatures": {},
        "backends": {},
        "warnings": [],
        "errors": [],
    }

    try:
        import tensorflow as tf  # noqa: WPS433
        report["tensorflow"] = getattr(tf, "__version__", "unknown")
        report["backends"]["gpu_devices"] = [device.name for device in tf.config.list_physical_devices("GPU")]
        report["backends"]["has_estimator"] = hasattr(tf, "estimator")
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["errors"].append(f"TensorFlow import failed: {type(exc).__name__}: {exc}")
        tf = None

    try:
        import deepctr  # noqa: WPS433
        report["deepctr"] = getattr(deepctr, "__version__", "unknown")
        modules = [
            "deepctr.feature_column",
            "deepctr.models",
            "deepctr.models.sequence",
            "deepctr.models.multitask",
            "deepctr.layers",
        ]
        for module_name in modules:
            importlib.import_module(module_name)
            report["imports"][module_name] = "ok"
        from deepctr.feature_column import DenseFeat, SparseFeat, VarLenSparseFeat  # noqa: WPS433
        from deepctr.models import DeepFM, DIN, MMOE  # noqa: WPS433
        for obj in [SparseFeat, DenseFeat, VarLenSparseFeat, DeepFM, DIN, MMOE]:
            report["api_signatures"][obj.__name__] = str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["errors"].append(f"DeepCTR import/API check failed: {type(exc).__name__}: {exc}")

    if report["tensorflow"] and report["deepctr"] and not report["errors"]:
        report["ok"] = True
    if args.fail_if_no_estimator and not report["backends"].get("has_estimator"):
        report["errors"].append("tf.estimator is unavailable in this TensorFlow runtime.")
        report["ok"] = False
    if args.fail_if_no_gpu and not report["backends"].get("gpu_devices"):
        report["errors"].append("TensorFlow sees no GPU devices. Use CPU workflows or install a compatible GPU TensorFlow stack.")
        report["ok"] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"DeepCTR: {report['deepctr']}")
        print(f"TensorFlow: {report['tensorflow']}")
        print(f"tf.estimator: {report['backends'].get('has_estimator')}")
        print(f"GPU devices: {len(report['backends'].get('gpu_devices') or [])}")
        if report["errors"]:
            print("Errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
