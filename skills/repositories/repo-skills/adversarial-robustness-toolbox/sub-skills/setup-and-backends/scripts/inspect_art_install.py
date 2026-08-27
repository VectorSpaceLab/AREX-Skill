#!/usr/bin/env python3
"""Safe ART install/backend diagnostic.

This helper imports ART and selected optional backend packages, then reports
versions and basic CPU/GPU visibility. It never downloads data, runs repository
examples, runs tests, prints package file paths, or mutates the environment.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import sys
from dataclasses import dataclass
from typing import Any, Callable

# Keep TensorFlow import diagnostics concise when this helper is used for setup.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

Probe = Callable[[Any], dict[str, Any]]


@dataclass(frozen=True)
class Check:
    alias: str
    module: str
    distribution: str | None
    purpose: str
    probe: Probe | None = None


def _module_version(module: Any, distribution: str | None) -> str | None:
    for attr in ("__version__", "VERSION", "version"):
        value = getattr(module, attr, None)
        if isinstance(value, str):
            return value
        if callable(value):
            try:
                called = value()
            except Exception:  # pragma: no cover - defensive only
                called = None
            if isinstance(called, str):
                return called
    if distribution:
        try:
            return metadata.version(distribution)
        except metadata.PackageNotFoundError:
            return None
    return None


def _probe_art(module: Any) -> dict[str, Any]:
    return {"distribution": "adversarial-robustness-toolbox", "import_name": "art", "version": module.__version__}


def _probe_torch(module: Any) -> dict[str, Any]:
    cuda_available = bool(module.cuda.is_available()) if hasattr(module, "cuda") else False
    device_count = int(module.cuda.device_count()) if cuda_available else 0
    return {
        "cuda_available": cuda_available,
        "cuda_device_count": device_count,
        "cpu_device_hint": "For CPU-only ART PyTorch estimators, pass device_type='cpu'.",
    }


def _probe_tensorflow(module: Any) -> dict[str, Any]:
    gpus = module.config.list_physical_devices("GPU")
    return {"gpu_device_count": len(gpus), "gpu_devices": [getattr(device, "name", str(device)) for device in gpus]}


CHECKS: dict[str, Check] = {
    "art": Check("art", "art", "adversarial-robustness-toolbox", "ART core package", _probe_art),
    "numpy": Check("numpy", "numpy", "numpy", "Core array dependency"),
    "scipy": Check("scipy", "scipy", "scipy", "Core scientific dependency"),
    "sklearn": Check("sklearn", "sklearn", "scikit-learn", "Core scikit-learn dependency"),
    "torch": Check("torch", "torch", "torch", "PyTorch backend", _probe_torch),
    "torchvision": Check("torchvision", "torchvision", "torchvision", "PyTorch image helper"),
    "tensorflow": Check("tensorflow", "tensorflow", "tensorflow", "TensorFlow backend", _probe_tensorflow),
    "keras": Check("keras", "keras", "keras", "Keras backend"),
    "xgboost": Check("xgboost", "xgboost", "xgboost", "XGBoost optional backend"),
    "lightgbm": Check("lightgbm", "lightgbm", "lightgbm", "LightGBM optional backend"),
    "catboost": Check("catboost", "catboost", "catboost", "CatBoost optional backend"),
    "gpy": Check("gpy", "GPy", "GPy", "GPy optional backend"),
    "opencv": Check("opencv", "cv2", "opencv-python", "OpenCV image helper"),
    "kornia": Check("kornia", "kornia", "kornia", "Kornia PyTorch image helper"),
    "tensorboardx": Check("tensorboardx", "tensorboardX", "tensorboardX", "ART SummaryWriter dependency"),
    "numba": Check("numba", "numba", "numba", "Optional acceleration/helper package"),
    "statsmodels": Check("statsmodels", "statsmodels", "statsmodels", "Optional statistics helper package"),
}

DEFAULT_ORDER = list(CHECKS)
GROUPS: dict[str, list[str]] = {
    "all": DEFAULT_ORDER,
    "core": ["art", "numpy", "scipy", "sklearn"],
    "pytorch": ["torch", "torchvision"],
    "tensorflow-stack": ["tensorflow", "keras"],
    "trees": ["xgboost", "lightgbm", "catboost"],
    "gpy-stack": ["gpy"],
    "image": ["opencv", "kornia"],
    "logging": ["tensorboardx"],
    "helpers": ["numba", "statsmodels"],
}


def _expand_include(spec: str) -> list[str]:
    selected: list[str] = []
    for raw in spec.split(","):
        token = raw.strip().lower()
        if not token:
            continue
        if token in GROUPS:
            selected.extend(GROUPS[token])
        elif token in CHECKS:
            selected.append(token)
        else:
            raise SystemExit(f"Unknown check or group: {raw!r}. Use --list to see valid names.")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in selected:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def _inspect(check: Check) -> dict[str, Any]:
    result: dict[str, Any] = {
        "alias": check.alias,
        "module": check.module,
        "distribution": check.distribution,
        "purpose": check.purpose,
    }
    try:
        module = importlib.import_module(check.module)
    except ModuleNotFoundError as exc:
        if exc.name == check.module or (exc.name and check.module.startswith(exc.name)):
            result.update({"status": "missing", "error_type": type(exc).__name__, "message": str(exc)})
        else:
            result.update({"status": "error", "error_type": type(exc).__name__, "message": str(exc)})
        return result
    except Exception as exc:  # pragma: no cover - import failures are environment-specific
        result.update({"status": "error", "error_type": type(exc).__name__, "message": str(exc)})
        return result

    result.update({"status": "ok", "version": _module_version(module, check.distribution)})
    if check.probe is not None:
        try:
            result.update(check.probe(module))
        except Exception as exc:  # pragma: no cover - probe failures are environment-specific
            result.update({"probe_status": "error", "probe_error_type": type(exc).__name__, "probe_message": str(exc)})
    return result


def _build_report(selected: list[str]) -> dict[str, Any]:
    results = [_inspect(CHECKS[name]) for name in selected]
    return {
        "tool": "inspect_art_install",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "selected": selected,
        "results": results,
        "summary": {
            "ok": sum(1 for item in results if item["status"] == "ok"),
            "missing": sum(1 for item in results if item["status"] == "missing"),
            "error": sum(1 for item in results if item["status"] == "error"),
        },
    }


def _print_text(report: dict[str, Any]) -> None:
    print("ART install diagnostic")
    print(f"Python: {report['python_implementation']} {report['python_version']}")
    print(f"Platform: {report['platform']}")
    print("Checks:")
    for item in report["results"]:
        version = item.get("version") or "-"
        print(f"  {item['status']:<7} {item['alias']:<13} {version:<18} {item['purpose']}")
        if item["status"] != "ok":
            print(f"           {item.get('error_type')}: {item.get('message')}")
        if item["alias"] == "torch" and item["status"] == "ok":
            print(
                "           "
                f"cuda_available={item.get('cuda_available')} "
                f"cuda_device_count={item.get('cuda_device_count')}"
            )
            print(f"           {item.get('cpu_device_hint')}")
        if item["alias"] == "tensorflow" and item["status"] == "ok":
            print(f"           gpu_device_count={item.get('gpu_device_count')}")
        if item.get("probe_status") == "error":
            print(f"           probe {item.get('probe_error_type')}: {item.get('probe_message')}")
    summary = report["summary"]
    print(f"Summary: ok={summary['ok']} missing={summary['missing']} error={summary['error']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect ART core and selected optional backend imports.")
    parser.add_argument(
        "--include",
        default="all",
        help="Comma-separated checks/groups. Groups: " + ", ".join(sorted(GROUPS)) + ". Default: all.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any selected check is missing or errors.")
    parser.add_argument("--list", action="store_true", help="List available checks and groups, then exit.")
    args = parser.parse_args(argv)

    if args.list:
        print("Checks:")
        for name, check in CHECKS.items():
            print(f"  {name:<13} module={check.module:<12} distribution={check.distribution or '-'}")
        print("Groups:")
        for name, members in GROUPS.items():
            print(f"  {name:<18} {','.join(members)}")
        return 0

    selected = _expand_include(args.include)
    report = _build_report(selected)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)

    if args.strict and (report["summary"]["missing"] or report["summary"]["error"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
