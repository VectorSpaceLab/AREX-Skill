#!/usr/bin/env python3
"""Read-only GemPy environment diagnostics.

This checker deliberately does not install packages, inspect a repository, or
access the network. It imports public modules and reads distribution metadata.
It is safe to invoke by absolute or relative path from any working directory.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Probe:
    distribution: str
    module: str
    required: bool
    metadata_version: str | None = None
    import_version: str | None = None
    status: str = "missing"
    detail: str = ""
    recovery: str = ""


# Distribution names are the names accepted by pip; module names are the
# public import names used by GemPy and its optional-dependency guards.
PACKAGES: dict[str, tuple[str, str, str, bool]] = {
    "gempy": ("gempy", "gempy", "python -m pip install --upgrade gempy", True),
    "gempy_engine": (
        "gempy-engine",
        "gempy_engine",
        "python -m pip install --upgrade gempy",
        True,
    ),
    "numpy": ("numpy", "numpy", "python -m pip install numpy", True),
    "pandas": (
        "pandas",
        "pandas",
        'python -m pip install "gempy[base]"',
        False,
    ),
    "matplotlib": (
        "matplotlib",
        "matplotlib",
        'python -m pip install "gempy[base]"',
        False,
    ),
    "gempy_viewer": (
        "gempy-viewer",
        "gempy_viewer",
        'python -m pip install "gempy[base]"',
        False,
    ),
    "pyvista": (
        "pyvista",
        "pyvista",
        "python -m pip install pyvista",
        False,
    ),
    "torch": (
        "torch",
        "torch",
        "Install a matching PyTorch build from the official PyTorch selector",
        False,
    ),
    "pykeops": (
        "pykeops",
        "pykeops",
        "python -m pip install pykeops",
        False,
    ),
    "gstools": (
        "gstools",
        "gstools",
        'python -m pip install "gempy[opt]"',
        False,
    ),
    "gempy_plugins": (
        "gempy-plugins",
        "gempy_plugins",
        'python -m pip install "gempy[opt]"',
        False,
    ),
    "pooch": (
        "pooch",
        "pooch",
        'python -m pip install "gempy[opt]"',
        False,
    ),
    "scipy": (
        "scipy",
        "scipy",
        'python -m pip install "gempy[opt]"',
        False,
    ),
    "skimage": (
        "scikit-image",
        "skimage",
        'python -m pip install "gempy[opt]"',
        False,
    ),
    "subsurface": (
        "subsurface-terra",
        "subsurface",
        "python -m pip install subsurface-terra",
        False,
    ),
}


def _version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # metadata plugins can fail independently
        return f"metadata error: {type(exc).__name__}"


def _import_probe(key: str, required_override: bool | None = None) -> Probe:
    distribution, module_name, recovery, required_by_default = PACKAGES[key]
    required = required_by_default if required_override is None else required_override
    probe = Probe(
        distribution=distribution,
        module=module_name,
        required=required,
        metadata_version=_version(distribution),
        recovery=recovery,
    )
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        probe.status = "missing" if isinstance(exc, ModuleNotFoundError) else "error"
        message = str(exc).strip().splitlines()[0] if str(exc).strip() else "no message"
        probe.detail = f"{type(exc).__name__}: {message}"
        return probe

    probe.status = "ok"
    imported_version = getattr(module, "__version__", None)
    if imported_version is not None:
        probe.import_version = str(imported_version)
    elif probe.metadata_version is not None:
        probe.import_version = probe.metadata_version
    else:
        probe.import_version = "<not exposed>"
    return probe


def _backend_info(requested: str) -> dict[str, Any]:
    result: dict[str, Any] = {"requested": requested, "status": "unknown", "detail": ""}
    if requested == "numpy":
        probe = _import_probe("numpy", required_override=True)
        result.update(status="ok" if probe.status == "ok" else "missing", detail=probe.detail or "NumPy imports")
        return result

    torch_probe = _import_probe("torch", required_override=True)
    result["torch"] = asdict(torch_probe)
    if torch_probe.status != "ok":
        result.update(status="missing", detail="PyTorch is not importable")
        return result

    try:
        torch = importlib.import_module("torch")
        result["cuda_available"] = bool(torch.cuda.is_available())
        mps = getattr(torch.backends, "mps", None)
        result["mps_available"] = bool(mps is not None and mps.is_available())
        result["torch_device"] = str(torch.get_default_device()) if hasattr(torch, "get_default_device") else "<not exposed>"
        result["status"] = "ok"
        result["detail"] = "PyTorch imports; requested accelerator availability is reported separately"
    except Exception as exc:
        result.update(status="error", detail=f"{type(exc).__name__}: {exc}")
    return result


def _viewer_info(probes: dict[str, Probe]) -> dict[str, Any]:
    result: dict[str, Any] = {"headless": not bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))}
    mpl = probes.get("matplotlib")
    if mpl and mpl.status == "ok":
        try:
            module = importlib.import_module("matplotlib")
            result["matplotlib_backend"] = str(module.get_backend())
            if result["headless"]:
                backend = str(module.get_backend()).lower()
                result["headless_action"] = (
                    "MPLBACKEND=Agg is suitable for file-based 2-D output"
                    if backend not in {"agg", "pdf", "svg", "ps", "cairo"}
                    else "non-interactive Matplotlib backend detected"
                )
        except Exception as exc:
            result["matplotlib_detail"] = f"{type(exc).__name__}: {exc}"
    else:
        result["matplotlib_backend"] = "unavailable"
    result["viewer_import"] = probes.get("gempy_viewer", Probe("", "", False)).status
    result["pyvista_import"] = probes.get("pyvista", Probe("", "", False)).status
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run read-only GemPy core, optional-dependency, backend, and headless diagnostics."
    )
    parser.add_argument(
        "--backend",
        choices=("numpy", "pytorch"),
        default=None,
        help="Require and probe a specific compute backend (default: report core and optional modules).",
    )
    parser.add_argument(
        "--require",
        action="append",
        choices=tuple(PACKAGES),
        metavar="MODULE",
        help="Require an additional public module; repeat for multiple modules.",
    )
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Return non-zero when any optional module in the standard matrix is missing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human-readable report.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    probes: dict[str, Probe] = {}
    # Core modules are always checked. Optional imports are checked as a
    # matrix so a missing feature is visible without making it a core failure.
    for key in PACKAGES:
        probes[key] = _import_probe(key)

    required_keys = set(args.require or ())
    required_keys.update({"gempy", "gempy_engine", "numpy"})
    for key in required_keys:
        if key not in probes:
            probes[key] = _import_probe(key, required_override=True)
        else:
            probes[key].required = True

    backend = _backend_info(args.backend) if args.backend else None
    viewer = _viewer_info(probes)
    issues: list[dict[str, str]] = []
    for key, probe in probes.items():
        if probe.status != "ok" and (probe.required or args.strict_optional):
            issues.append(
                {
                    "kind": "required" if probe.required else "optional",
                    "module": probe.module,
                    "detail": probe.detail,
                    "action": probe.recovery,
                }
            )
    if backend and backend.get("status") != "ok":
        issues.append(
            {
                "kind": "backend",
                "module": str(args.backend),
                "detail": str(backend.get("detail", "backend unavailable")),
                "action": "Use --backend numpy or install the matching backend dependencies.",
            }
        )

    report: dict[str, Any] = {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "supported_minimum": "3.10",
            "status": "ok" if sys.version_info >= (3, 10) else "error",
        },
        "probes": {key: asdict(value) for key, value in probes.items()},
        "backend": backend,
        "viewer": viewer,
        "issues": issues,
        "exit_status": 1 if issues or sys.version_info < (3, 10) else 0,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GemPy environment check (read-only)")
        py = report["python"]
        print(f"Python {py['version']} [{py['status']}]; minimum {py['supported_minimum']}")
        print("\nPackage probes:")
        for key, probe in probes.items():
            metadata_version = probe.metadata_version or "MISSING"
            imported_version = probe.import_version or "-"
            marker = "required" if probe.required else "optional"
            print(f"  {key:18} {probe.status:7} {marker:8} metadata={metadata_version} import={imported_version}")
            if probe.status != "ok" and probe.detail:
                print(f"    detail: {probe.detail}")
                print(f"    action: {probe.recovery}")
        if backend:
            print(f"\nBackend ({args.backend}): {backend['status']} — {backend.get('detail', '')}")
            for field in ("cuda_available", "mps_available", "torch_device"):
                if field in backend:
                    print(f"  {field}: {backend[field]}")
        print("\nViewer/headless:")
        for key, value in viewer.items():
            print(f"  {key}: {value}")
        print("\nSummary:")
        if issues:
            print("  ACTION REQUIRED")
            for issue in issues:
                print(f"  - {issue['kind']} {issue['module']}: {issue['detail']}")
                print(f"    recovery: {issue['action']}")
        else:
            print("  core requirements passed; absent optional modules are usable only if their features are not selected")
        print("  Note: this script never installs packages or uses the network; run `python -m pip check` separately.")

    return int(report["exit_status"])


if __name__ == "__main__":
    raise SystemExit(main())
