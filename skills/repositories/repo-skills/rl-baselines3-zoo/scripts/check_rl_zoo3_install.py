#!/usr/bin/env python3
"""Check an installed RL Baselines3 Zoo environment without side effects.

The script imports public packages, reports versions, and optionally checks
plotting dependencies or a tiny PyTorch CUDA allocation. It does not train,
download, upload, render, mutate files, or require the original repository
checkout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

CORE_MODULES = [
    "rl_zoo3",
    "gymnasium",
    "stable_baselines3",
    "sb3_contrib",
    "optuna",
    "torch",
]
PLOT_MODULES = ["seaborn", "pandas", "scipy", "rliable"]


def module_version(module_name: str) -> str | None:
    candidates = {
        "rl_zoo3": "rl_zoo3",
        "stable_baselines3": "stable-baselines3",
        "sb3_contrib": "sb3-contrib",
        "gymnasium": "gymnasium",
        "optuna": "optuna",
        "torch": "torch",
        "seaborn": "seaborn",
        "pandas": "pandas",
        "scipy": "scipy",
        "rliable": "rliable",
    }
    try:
        return version(candidates.get(module_name, module_name))
    except PackageNotFoundError:
        return None


def import_modules(modules: list[str]) -> tuple[dict[str, Any], list[str]]:
    results: dict[str, Any] = {}
    errors: list[str] = []
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            results[module_name] = {
                "ok": True,
                "version": module_version(module_name) or getattr(module, "__version__", None),
            }
        except Exception as exc:  # noqa: BLE001 - diagnostics should report import failures concisely.
            results[module_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
    return results, errors


def cuda_smoke() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"torch import failed: {type(exc).__name__}: {exc}"}, ["torch import failed"]

    result: dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_runtime": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0,
    }
    if not result["cuda_available"]:
        errors.append("torch.cuda.is_available() is False")
        return result, errors

    try:
        result["device0"] = torch.cuda.get_device_name(0)
        result["capability0"] = list(torch.cuda.get_device_capability(0))
        tensor = torch.empty((1,), device="cuda")
        result["tiny_tensor_device"] = str(tensor.device)
    except Exception as exc:  # noqa: BLE001
        result["allocation_error"] = f"{type(exc).__name__}: {exc}"
        errors.append(result["allocation_error"])
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-plots", action="store_true", help="Also import plotting/rliable dependencies")
    parser.add_argument("--check-cuda", action="store_true", help="Also run a tiny torch CUDA availability/allocation check")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    modules = list(CORE_MODULES)
    if args.check_plots:
        modules.extend(PLOT_MODULES)

    imports, errors = import_modules(modules)
    report: dict[str, Any] = {"imports": imports}

    if imports.get("rl_zoo3", {}).get("ok"):
        try:
            import rl_zoo3

            report["rl_zoo3_algos"] = sorted(rl_zoo3.ALGOS.keys())
        except Exception as exc:  # noqa: BLE001
            report["rl_zoo3_algos_error"] = f"{type(exc).__name__}: {exc}"
            errors.append(report["rl_zoo3_algos_error"])

    if args.check_cuda:
        cuda_report, cuda_errors = cuda_smoke()
        report["cuda"] = cuda_report
        errors.extend(cuda_errors)

    report["ok"] = not errors
    report["errors"] = errors

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, data in imports.items():
            if data.get("ok"):
                print(f"{name}: ok {data.get('version') or ''}".rstrip())
            else:
                print(f"{name}: ERROR {data.get('error')}", file=sys.stderr)
        if "rl_zoo3_algos" in report:
            print("algos:", ", ".join(report["rl_zoo3_algos"]))
        if "cuda" in report:
            print("cuda:", json.dumps(report["cuda"], sort_keys=True))
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
