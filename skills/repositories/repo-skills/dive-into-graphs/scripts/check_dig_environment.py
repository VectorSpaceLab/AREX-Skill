#!/usr/bin/env python3
"""Safe DIG environment diagnostic.

This script imports public DIG modules and reports optional dependency/backend
state. It does not instantiate datasets, download files, train models, or write
outside stdout.
"""
import argparse
import importlib
import json
import sys

CORE_MODULES = [
    "dig", "dig.ggraph", "dig.ggraph.dataset", "dig.ggraph.evaluation", "dig.ggraph.utils",
    "dig.ggraph3D.dataset", "dig.ggraph3D.method", "dig.ggraph3D.evaluation", "dig.ggraph3D.utils",
    "dig.sslgraph", "dig.sslgraph.dataset", "dig.sslgraph.method", "dig.sslgraph.evaluation", "dig.sslgraph.utils",
    "dig.xgraph", "dig.xgraph.dataset", "dig.xgraph.method", "dig.xgraph.evaluation", "dig.xgraph.models",
    "dig.threedgraph", "dig.threedgraph.dataset", "dig.threedgraph.method", "dig.threedgraph.evaluation",
    "dig.oodgraph", "dig.auggraph", "dig.auggraph.dataset", "dig.auggraph.method.GraphAug",
    "dig.auggraph.method.SMixup", "dig.fairgraph", "dig.fairgraph.dataset", "dig.fairgraph.method",
]
OPTIONAL_MODULES = [
    "torch", "torch_geometric", "torch_scatter", "torch_sparse", "torch_cluster", "torch_spline_conv",
    "rdkit", "captum", "shap", "gdown", "pygmtools", "ogb", "pyscf", "hydra", "omegaconf",
]
LARGE_SCALE_MODULES = ["dig.lsgraph", "dig.lsgraph.method", "dig.lsgraph.dataset"]


def import_status(name):
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        return {"ok": True, "version": version}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main():
    parser = argparse.ArgumentParser(description="Check DIG import/backend readiness without downloads.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--check-optional", action="store_true", help="Include optional dependency imports.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch reports no CUDA device.")
    parser.add_argument("--fail-on-large-scale-extension-missing", action="store_true",
                        help="Fail if dig.lsgraph.dataset cannot import, commonly because dig_ext is unavailable.")
    args = parser.parse_args()

    report = {"modules": {}, "optional": {}, "large_scale": {}, "torch": {}}
    for name in CORE_MODULES:
        report["modules"][name] = import_status(name)
    for name in LARGE_SCALE_MODULES:
        report["large_scale"][name] = import_status(name)
    if args.check_optional:
        for name in OPTIONAL_MODULES:
            report["optional"][name] = import_status(name)

    torch_status = import_status("torch")
    if torch_status["ok"]:
        import torch
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    else:
        report["torch"] = torch_status

    failures = [name for name, status in report["modules"].items() if not status["ok"]]
    if args.fail_on_large_scale_extension_missing:
        failures.extend(name for name, status in report["large_scale"].items() if not status["ok"])
    if args.require_cuda and not report.get("torch", {}).get("cuda_available", False):
        failures.append("cuda")
    report["ok"] = not failures
    report["failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DIG environment check")
        print("OK:" if report["ok"] else "FAILED:", ", ".join(failures) if failures else "all required checks passed")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
