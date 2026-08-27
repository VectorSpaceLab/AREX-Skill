#!/usr/bin/env python3
"""Report Faiss backend availability without allocating accelerator resources.

This checker is intentionally a probe, not a GPU smoke test. It never builds,
installs, downloads, starts a server, or calls a GPU allocation API. It can be
run from any working directory:

    python /path/to/check_backend.py
    python /path/to/check_backend.py --json
"""

from __future__ import annotations

import argparse
import ctypes.util
import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any


FAISS_GPU_SYMBOLS = (
    "StandardGpuResources",
    "index_cpu_to_gpu",
    "index_cpu_to_all_gpus",
    "get_num_gpus",
)
CUVS_SYMBOLS = (
    "GpuIndexCagra",
    "GpuIndexIVFPQ",
    "GpuIndexIVFFlat",
)
SVS_SYMBOLS = ("IndexSVSVamana", "IndexSVSIVF")
OPTIONAL_MODULES = ("torch", "cuvs", "rmm", "svs", "numpy")
DISTRIBUTIONS = (
    "faiss-cpu",
    "faiss-gpu",
    "faiss-gpu-cuvs",
    "libcuvs-cu13",
    "librmm-cu13",
    "libraft-cu13",
    "svs",
    "numpy",
    "torch",
)
TOOLS = ("cmake", "nvcc", "hipcc", "nvidia-smi", "rocminfo")


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # metadata plugins should not break the report
        return f"error: {type(exc).__name__}: {exc}"


def _module_probe(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
        return {"available": spec is not None}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def _tool_probe(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    result: dict[str, Any] = {"available": path is not None}
    if path is None:
        return result
    result["path"] = path
    # Version probes are fixed, read-only commands with a short timeout. Some
    # tools write a banner to stderr, hence capture both streams.
    args = [path, "--version"]
    if name == "nvidia-smi":
        args = [path, "--query-gpu=name,driver_version", "--format=csv,noheader"]
    elif name == "rocminfo":
        # --version is not consistently supported; only report discovery.
        return result
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        text = (completed.stdout or completed.stderr).strip()
        if text:
            result["version_or_devices"] = text.splitlines()[:8]
        result["returncode"] = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["probe_error"] = f"{type(exc).__name__}: {exc}"
    return result


def _safe_call(callable_obj: Any) -> tuple[Any, str | None]:
    try:
        return callable_obj(), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def collect_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "probe": {
            "purpose": "availability-only; no accelerator allocation or network activity",
            "python": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cwd": os.getcwd(),
        },
        "distributions": {name: _version(name) for name in DISTRIBUTIONS},
        "optional_modules": {name: _module_probe(name) for name in OPTIONAL_MODULES},
        "tools": {name: _tool_probe(name) for name in TOOLS},
        "libraries": {
            "svs_runtime": ctypes.util.find_library("svs_runtime"),
            "cudart": ctypes.util.find_library("cudart"),
            "cuda": ctypes.util.find_library("cuda"),
            "amdhip64": ctypes.util.find_library("amdhip64"),
        },
    }

    try:
        faiss = importlib.import_module("faiss")
    except Exception as exc:
        report["faiss"] = {
            "imported": False,
            "error": f"{type(exc).__name__}: {exc}",
            "decision": "CPU/GPU Faiss runtime unavailable in this interpreter",
        }
        return report

    report["faiss"] = {
        "imported": True,
        "file": getattr(faiss, "__file__", None),
        "version": getattr(faiss, "__version__", None),
        "gpu_symbols": {name: hasattr(faiss, name) for name in FAISS_GPU_SYMBOLS},
        "cuvs_symbols": {name: hasattr(faiss, name) for name in CUVS_SYMBOLS},
        "svs_symbols": {name: hasattr(faiss, name) for name in SVS_SYMBOLS},
        "metal_like_symbols": {
            name: hasattr(faiss, name)
            for name in (
                "StandardGpuResources",
                "index_cpu_to_gpu",
                "index_gpu_to_cpu",
            )
        },
    }

    compile_options = getattr(faiss, "get_compile_options", None)
    if callable(compile_options):
        value, error = _safe_call(compile_options)
        report["faiss"]["compile_options"] = value
        if error:
            report["faiss"]["compile_options_error"] = error

    get_num_gpus = getattr(faiss, "get_num_gpus", None)
    if callable(get_num_gpus):
        value, error = _safe_call(get_num_gpus)
        report["faiss"]["reported_gpu_count"] = value
        if error:
            report["faiss"]["gpu_count_error"] = error
    else:
        report["faiss"]["reported_gpu_count"] = None
        report["faiss"]["gpu_count_note"] = "get_num_gpus symbol absent"

    try:
        options_type = getattr(faiss, "GpuClonerOptions", None)
        # The SWIG field is normally exposed on an instance rather than the
        # class. Constructing this options-only object does not allocate a GPU
        # resource; failures are captured as an unavailable optional signal.
        options = options_type() if options_type is not None else None
        report["faiss"]["cuvs_config_field"] = bool(
            options is not None and hasattr(options, "use_cuvs")
        )
    except Exception as exc:
        report["faiss"]["cuvs_config_field"] = False
        report["faiss"]["cuvs_config_field_error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    gpu_api = all(report["faiss"]["gpu_symbols"].values())
    reported_count = report["faiss"].get("reported_gpu_count")
    report["decisions"] = {
        "cpu_import_and_api": "available",
        "nvidia_gpu_faiss_gate": bool(gpu_api and isinstance(reported_count, int) and reported_count > 0),
        "nvidia_gpu_faiss_gate_reason": (
            "GPU symbols and a positive Faiss device count are present"
            if gpu_api and isinstance(reported_count, int) and reported_count > 0
            else "requires StandardGpuResources/index_cpu_to_gpu/get_num_gpus and a positive device count"
        ),
        "cuvs_candidate": bool(
            gpu_api
            and report["faiss"]["cuvs_config_field"]
            and any(report["faiss"]["cuvs_symbols"].values())
        ),
        "svs_candidate": any(report["faiss"]["svs_symbols"].values()),
        "metal_candidate": bool(
            sys.platform == "darwin"
            and report["faiss"]["metal_like_symbols"]["StandardGpuResources"]
        ),
        "backend_smoke": "not run by this availability-only probe",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report installed Faiss CPU/GPU/cuVS/SVS/Metal signals and tool "
            "availability without allocating accelerator resources."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a compact human report",
    )
    args = parser.parse_args()
    report = collect_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("Faiss backend availability (no accelerator smoke run)")
    print(f"  Python: {report['probe']['python']}")
    print(f"  Platform: {report['probe']['platform']}")
    faiss_report = report.get("faiss", {})
    if not faiss_report.get("imported"):
        print(f"  Faiss import: unavailable ({faiss_report.get('error', 'unknown')})")
        return 0
    print(f"  Faiss: imported from {faiss_report.get('file')}")
    print(f"  Compile options: {faiss_report.get('compile_options', 'not exposed')}")
    print(f"  Faiss-reported GPUs: {faiss_report.get('reported_gpu_count', 'not exposed')}")
    print(f"  GPU API symbols: {faiss_report.get('gpu_symbols')}")
    print(f"  cuVS symbols: {faiss_report.get('cuvs_symbols')}")
    print(f"  SVS symbols: {faiss_report.get('svs_symbols')}")
    decisions = report.get("decisions", {})
    print(f"  NVIDIA GPU gate: {decisions.get('nvidia_gpu_faiss_gate')}")
    print(f"  cuVS candidate: {decisions.get('cuvs_candidate')}")
    print(f"  SVS candidate: {decisions.get('svs_candidate')}")
    print(f"  Metal candidate: {decisions.get('metal_candidate')}")
    print("  Note: candidates require a focused backend smoke before use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
