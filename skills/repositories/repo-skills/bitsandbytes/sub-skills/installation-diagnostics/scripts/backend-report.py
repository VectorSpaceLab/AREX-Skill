#!/usr/bin/env python3
"""Read-only bitsandbytes backend diagnostic report.

This helper imports torch and bitsandbytes, inspects version/backend signals, lists
bundled bitsandbytes native libraries, and predicts the library filename requested
by the current PyTorch runtime plus BNB override variables. It does not allocate
accelerator tensors, run kernels, download packages, or mutate the environment.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import re
import sys
from typing import Any


def _safe_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"


def _version_of(module: Any) -> str | None:
    return getattr(module, "__version__", None) if module is not None else None


def _dynamic_suffix() -> str:
    if platform.system() == "Windows":
        return ".dll"
    if platform.system() == "Darwin":
        return ".dylib"
    return ".so"


def _version_code(version: str | None) -> str | None:
    if not version:
        return None
    match = re.match(r"^(\d+)\.(\d+)", version)
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def _torch_backend(torch_mod: Any) -> str:
    if torch_mod is None:
        return "unknown"
    version = getattr(torch_mod, "version", None)
    if getattr(version, "hip", None):
        return "rocm"
    cuda_available = False
    try:
        cuda_available = bool(torch_mod.cuda.is_available())
    except Exception:
        cuda_available = False
    if cuda_available and getattr(version, "cuda", None):
        return "cuda"
    try:
        if bool(getattr(torch_mod._C, "_has_xpu", False)):
            return "xpu"
    except Exception:
        pass
    return "cpu"


def _package_dir(bnb_mod: Any) -> Path | None:
    file_name = getattr(bnb_mod, "__file__", None) if bnb_mod is not None else None
    if not file_name:
        return None
    return Path(file_name).resolve().parent


def _library_files(package_dir: Path | None) -> list[str]:
    if package_dir is None:
        return []
    return sorted(path.name for path in package_dir.glob("libbitsandbytes_*") if path.is_file())


def _requested_library(torch_mod: Any, backend: str) -> str | None:
    suffix = _dynamic_suffix()
    version = getattr(torch_mod, "version", None) if torch_mod is not None else None
    cuda_override = os.environ.get("BNB_CUDA_VERSION")
    rocm_override = os.environ.get("BNB_ROCM_VERSION")

    if backend == "rocm":
        code = rocm_override or _version_code(getattr(version, "hip", None))
        return f"libbitsandbytes_rocm{code}{suffix}" if code else None
    if backend == "cuda":
        code = cuda_override or _version_code(getattr(version, "cuda", None))
        return f"libbitsandbytes_cuda{code}{suffix}" if code else None
    if backend == "xpu":
        return f"libbitsandbytes_xpu{suffix}"
    if backend == "cpu":
        return f"libbitsandbytes_cpu{suffix}"
    return None


def _device_summary(torch_mod: Any, include_device_names: bool) -> dict[str, Any]:
    summary: dict[str, Any] = {"cuda_device_count": None, "cuda_capabilities": []}
    if torch_mod is None:
        return summary
    try:
        count = int(torch_mod.cuda.device_count())
    except Exception:
        count = None
    summary["cuda_device_count"] = count
    if count:
        capabilities = []
        for index in range(count):
            item: dict[str, Any] = {"index": index}
            try:
                major, minor = torch_mod.cuda.get_device_capability(index)
                item["compute_capability"] = f"{major}.{minor}"
            except Exception as exc:
                item["compute_capability_error"] = f"{type(exc).__name__}: {exc}"
            if include_device_names:
                try:
                    item["name"] = torch_mod.cuda.get_device_name(index)
                except Exception as exc:
                    item["name_error"] = f"{type(exc).__name__}: {exc}"
            capabilities.append(item)
        summary["cuda_capabilities"] = capabilities
    return summary


def build_report(include_device_names: bool = False) -> dict[str, Any]:
    torch_mod, torch_error = _safe_import("torch")
    bnb_mod, bnb_error = _safe_import("bitsandbytes")
    backend = _torch_backend(torch_mod)
    package_dir = _package_dir(bnb_mod)
    libraries = _library_files(package_dir)
    requested = _requested_library(torch_mod, backend)

    version = getattr(torch_mod, "version", None) if torch_mod is not None else None
    cuda_available = None
    if torch_mod is not None:
        try:
            cuda_available = bool(torch_mod.cuda.is_available())
        except Exception as exc:
            cuda_available = f"error: {type(exc).__name__}: {exc}"

    report: dict[str, Any] = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "libc": "-".join(platform.libc_ver()) if platform.system() == "Linux" else None,
        },
        "imports": {
            "torch": "ok" if torch_error is None else torch_error,
            "bitsandbytes": "ok" if bnb_error is None else bnb_error,
        },
        "versions": {
            "torch": _version_of(torch_mod),
            "bitsandbytes": _version_of(bnb_mod),
            "torch_cuda": getattr(version, "cuda", None),
            "torch_hip": getattr(version, "hip", None),
            "torch_xpu": getattr(version, "xpu", None),
        },
        "backend": {
            "classified": backend,
            "torch_cuda_is_available": cuda_available,
            "torch_has_xpu": bool(getattr(getattr(torch_mod, "_C", object()), "_has_xpu", False))
            if torch_mod is not None
            else None,
        },
        "overrides": {
            "BNB_CUDA_VERSION": os.environ.get("BNB_CUDA_VERSION"),
            "BNB_ROCM_VERSION": os.environ.get("BNB_ROCM_VERSION"),
        },
        "native_libraries": {
            "package_dir_available": package_dir is not None,
            "available_bnb_libraries": libraries,
            "requested_library": requested,
            "requested_library_present": requested in libraries if requested else None,
        },
        "devices": _device_summary(torch_mod, include_device_names),
        "notes": [],
    }

    notes = report["notes"]
    if torch_error:
        notes.append("Install a compatible PyTorch package before debugging bitsandbytes.")
    if bnb_error:
        notes.append("bitsandbytes import failed; inspect the import error before running backend kernels.")
    if backend == "cpu" and cuda_available is False:
        notes.append("CPU-only report: import checks can pass, but CUDA/ROCm kernels are not proven available.")
    if os.environ.get("BNB_CUDA_VERSION") and backend != "cuda":
        notes.append("BNB_CUDA_VERSION is set outside a CUDA-classified runtime; clear it unless switching to CUDA.")
    if os.environ.get("BNB_ROCM_VERSION") and backend != "rocm":
        notes.append("BNB_ROCM_VERSION is set outside a ROCm-classified runtime; clear it unless switching to ROCm.")
    if requested and requested not in libraries:
        notes.append("The requested bitsandbytes native library is not bundled in the imported package.")

    return report


def print_text(report: dict[str, Any]) -> None:
    print("bitsandbytes backend report")
    print(f"Platform: {report['platform']['system']} {report['platform']['release']} {report['platform']['machine']}")
    print(f"Python: {report['platform']['python']}")
    print(f"Imports: torch={report['imports']['torch']} bitsandbytes={report['imports']['bitsandbytes']}")
    versions = report["versions"]
    print(
        "Versions: "
        f"torch={versions['torch']} bitsandbytes={versions['bitsandbytes']} "
        f"cuda={versions['torch_cuda']} hip={versions['torch_hip']} xpu={versions['torch_xpu']}"
    )
    backend = report["backend"]
    print(
        "Backend: "
        f"classified={backend['classified']} "
        f"torch.cuda.is_available={backend['torch_cuda_is_available']} "
        f"torch._C._has_xpu={backend['torch_has_xpu']}"
    )
    print(
        "Overrides: "
        f"BNB_CUDA_VERSION={report['overrides']['BNB_CUDA_VERSION']} "
        f"BNB_ROCM_VERSION={report['overrides']['BNB_ROCM_VERSION']}"
    )
    native = report["native_libraries"]
    print(f"Requested library: {native['requested_library']} present={native['requested_library_present']}")
    print("Available bitsandbytes libraries:")
    for name in native["available_bnb_libraries"] or ["(none found)"]:
        print(f"  - {name}")
    if report["notes"]:
        print("Notes:")
        for note in report["notes"]:
            print(f"  - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only bitsandbytes backend diagnostic report.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--include-device-names",
        action="store_true",
        help="Include CUDA device names. Omit this when sharing reports publicly if device names are sensitive.",
    )
    args = parser.parse_args(argv)

    report = build_report(include_device_names=args.include_device_names)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
