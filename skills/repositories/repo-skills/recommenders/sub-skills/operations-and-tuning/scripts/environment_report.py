#!/usr/bin/env python3
"""Safe Recommenders environment readiness report.

This script imports selected modules and probes optional frameworks if present.
It does not install packages, start cloud jobs, create clusters, or download data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version

BASE_MODULES = [
    "recommenders",
    "recommenders.datasets.python_splitters",
    "recommenders.evaluation.python_evaluation",
    "recommenders.models.sar",
    "recommenders.models.tfidf.tfidf_utils",
    "recommenders.tuning.parameter_sweep",
]
OPTIONAL_MODULES = {
    "spark": ["pyspark", "recommenders.datasets.spark_splitters", "recommenders.evaluation.spark_evaluation"],
    "torch": ["torch", "recommenders.models.ncf.ncf_singlenode"],
    "tensorflow": ["tensorflow", "recommenders.models.deeprec.models.dkn", "recommenders.utils.tf_utils"],
    "nni": ["nni"],
    "surprise": ["surprise"],
    "lightfm": ["lightfm"],
    "vowpalwabbit": ["vowpalwabbit"],
}


def import_status(module: str) -> dict:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:
        return {"module": module, "status": "fail", "error_type": type(exc).__name__, "error": str(exc).splitlines()[0]}
    return {"module": module, "status": "ok", "file_present": bool(getattr(imported, "__file__", None))}


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Report Recommenders base and optional backend readiness without side effects.")
    parser.add_argument("--check-optional", action="store_true", help="Probe optional Spark/GPU/experimental imports if present.")
    args = parser.parse_args()

    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {"recommenders": package_version("recommenders")},
        "base_imports": [import_status(m) for m in BASE_MODULES],
        "optional_imports": {},
        "notes": [
            "This report does not install extras or prove cloud credentials.",
            "Spark, GPU, NNI, AzureML, Databricks, and experimental workflows require separate runtime checks.",
        ],
    }
    if args.check_optional:
        for group, modules in OPTIONAL_MODULES.items():
            report["optional_imports"][group] = [import_status(m) for m in modules]
        try:
            import torch

            report["optional_imports"].setdefault("torch_runtime", []).append(
                {
                    "module": "torch.cuda",
                    "status": "ok",
                    "cuda_available": bool(torch.cuda.is_available()),
                    "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
                }
            )
        except Exception:
            pass
    base_ok = all(item["status"] == "ok" for item in report["base_imports"])
    report["status"] = "ok" if base_ok else "base_import_failed"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if base_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
