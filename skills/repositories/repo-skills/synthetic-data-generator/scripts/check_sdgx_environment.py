#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version


def safe_version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SDGX imports, registries, CLI, and optional CUDA backend.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip sdgx --help check.")
    args = parser.parse_args()

    report: dict[str, object] = {"ok": True, "errors": [], "warnings": []}

    try:
        import sdgx

        report["sdgx_version"] = getattr(sdgx, "__version__", None)
        report["sdgx_distribution_version"] = safe_version("sdgx")
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["ok"] = False
        report["errors"].append(f"sdgx import failed: {type(exc).__name__}: {exc}")

    registry_specs = {
        "models": ("sdgx.models.manager", "ModelManager", "registed_models"),
        "data_connectors": ("sdgx.data_connectors.manager", "DataConnectorManager", "registed_data_connectors"),
        "data_processors": ("sdgx.data_processors.manager", "DataProcessorManager", "registed_data_processors"),
        "data_exporters": ("sdgx.data_exporters.manager", "DataExporterManager", "registed_exporters"),
        "cachers": ("sdgx.cachers.manager", "CacherManager", "registed_cachers"),
        "inspectors": ("sdgx.data_models.inspectors.manager", "InspectorManager", "registed_inspectors"),
    }
    registries = {}
    for key, (module_name, cls_name, prop_name) in registry_specs.items():
        try:
            mod = importlib.import_module(module_name)
            mgr = getattr(mod, cls_name)()
            registries[key] = sorted(getattr(mgr, prop_name).keys())
        except Exception as exc:
            report["ok"] = False
            report["errors"].append(f"{key} registry failed: {type(exc).__name__}: {exc}")
    report["registries"] = registries

    if not args.skip_cli:
        cli = shutil.which("sdgx")
        if not cli:
            report["warnings"].append("sdgx console script is not on PATH")
        else:
            proc = subprocess.run([cli, "--help"], text=True, capture_output=True, timeout=20)
            report["cli_help_exit_code"] = proc.returncode
            if proc.returncode != 0:
                report["ok"] = False
                report["errors"].append((proc.stderr or proc.stdout).strip()[:500])

    try:
        import torch

        cuda = {
            "torch_version": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            cuda["device_name_0"] = torch.cuda.get_device_name(0)
            cuda["capability_0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
        report["torch"] = cuda
        if args.require_cuda and not torch.cuda.is_available():
            report["ok"] = False
            report["errors"].append("--require-cuda was set but torch.cuda.is_available() is false")
    except Exception as exc:
        if args.require_cuda:
            report["ok"] = False
            report["errors"].append(f"torch/CUDA check failed: {type(exc).__name__}: {exc}")
        else:
            report["warnings"].append(f"torch check failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for k, v in report.items():
            print(f"{k}: {v}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
