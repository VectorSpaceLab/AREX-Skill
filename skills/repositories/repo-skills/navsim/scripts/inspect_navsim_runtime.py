#!/usr/bin/env python3
"""Run read-only NAVSIM package, API, and optional CUDA diagnostics.

This helper never downloads data, opens datasets, creates caches, starts Hydra
workloads, trains, scores, or uploads. It is safe to run from any directory.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
from typing import Any, Dict, List

MODULES = [
    "navsim",
    "navsim.agents.abstract_agent",
    "navsim.common.dataclasses",
    "navsim.common.dataloader",
    "navsim.planning.script.run_metric_caching",
    "navsim.planning.script.run_pdm_score",
    "navsim.planning.script.run_training",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable diagnostics")
    parser.add_argument("--cuda", action="store_true", help="probe Torch CUDA and allocate one tiny tensor")
    args = parser.parse_args()
    report: Dict[str, Any] = {"modules": {}, "versions": {}, "side_effects": "none"}
    try:
        report["versions"]["navsim"] = importlib.metadata.version("navsim")
    except importlib.metadata.PackageNotFoundError:
        report["versions"]["navsim"] = None
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            report["modules"][name] = {"status": "ok", "file": getattr(module, "__file__", None)}
        except Exception as exc:  # diagnostics should identify optional/runtime gaps
            report["modules"][name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    if args.cuda:
        try:
            import torch
            details: Dict[str, Any] = {
                "torch": torch.__version__,
                "compiled_cuda": torch.version.cuda,
                "available": bool(torch.cuda.is_available()),
                "count": torch.cuda.device_count(),
            }
            if details["available"]:
                details["device"] = torch.cuda.get_device_name(0)
                details["capability"] = list(torch.cuda.get_device_capability(0))
                details["allocation"] = str(torch.zeros(1, device="cuda").device)
            report["cuda"] = details
        except Exception as exc:
            report["cuda"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("NAVSIM runtime diagnostics (read-only)")
        print("navsim version:", report["versions"].get("navsim"))
        for name, result in report["modules"].items():
            print(f"{result['status'].upper()}: {name}" + (f" — {result.get('error')}" if result['status'] != 'ok' else ""))
        if "cuda" in report:
            print("CUDA:", json.dumps(report["cuda"], sort_keys=True))
        print("No dataset/cache/workload side effects were performed.")
    return 0 if report["modules"].get("navsim", {}).get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
