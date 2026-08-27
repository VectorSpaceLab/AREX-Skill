#!/usr/bin/env python3
"""Non-invasive report for the historical SECOND detector backend.

This helper deliberately does not import ``second``, model modules, NMS
kernels, Fire, or a training/evaluation entry point.  It only probes package
availability, versions, CUDA visibility, and legacy spconv symbol names.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


REQUIRED_LEGACY_SYMBOLS = (
    "spconv.SubMConv3d",
    "spconv.SparseConv3d",
    "spconv.SparseSequential",
    "spconv.SparseConvTensor",
    "spconv.SparseModule",
    "spconv.ops.nms",
    "spconv.utils.VoxelGeneratorV2",
    "spconv.utils.non_max_suppression",
    "spconv.utils.non_max_suppression_cpu",
    "spconv.utils.rotate_non_max_suppression_cpu",
    "spconv.utils.rbbox_iou",
    "spconv.utils.rbbox_intersection",
)


def _status(ok: bool, **details: Any) -> dict[str, Any]:
    return {"status": "ok" if ok else "missing", **details}


def _probe_torch() -> dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
        cuda_available = bool(torch.cuda.is_available())
        result: dict[str, Any] = {
            "status": "ok",
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_available": cuda_available,
            "cuda_device_count": int(torch.cuda.device_count())
            if cuda_available
            else 0,
        }
        # Do not allocate a CUDA tensor: this helper is a non-invasive
        # capability report, not a CUDA or detector execution smoke test.
        result["cuda_probe"] = "availability-and-device-count-only"
        return result
    except Exception as exc:
        return _status(False, error=f"{type(exc).__name__}: {exc}")


def _probe_simple_package(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        result: dict[str, Any] = {
            "status": "ok",
            "version": getattr(module, "__version__", "unknown"),
        }
        if name == "numba":
            try:
                cuda = importlib.import_module("numba.cuda")
                result["cuda_available"] = bool(cuda.is_available())
            except Exception as exc:  # pragma: no cover - host dependent
                result["cuda_available"] = "error"
                result["cuda_error"] = f"{type(exc).__name__}: {exc}"
        return result
    except Exception as exc:
        return _status(False, error=f"{type(exc).__name__}: {exc}")


def _probe_spconv() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        spconv = importlib.import_module("spconv")
        result["package"] = {
            "status": "ok",
            "version": getattr(spconv, "__version__", "unknown"),
        }
    except Exception as exc:
        result["package"] = _status(
            False, error=f"{type(exc).__name__}: {exc}"
        )
        result["legacy_symbols"] = {
            name: {
                "status": "missing",
                "present": False,
                "reason": "spconv import failed",
            }
            for name in REQUIRED_LEGACY_SYMBOLS
        }
        result["required_legacy_symbols_present"] = False
        return result

    modules: dict[str, Any] = {"spconv": spconv}
    module_status: dict[str, Any] = {
        "spconv": {"status": "ok"},
    }
    for module_name in ("spconv.ops", "spconv.utils"):
        try:
            modules[module_name] = importlib.import_module(module_name)
            module_status[module_name] = {"status": "ok"}
        except Exception as exc:
            module_status[module_name] = _status(
                False, error=f"{type(exc).__name__}: {exc}"
            )
    result["symbol_modules"] = module_status

    symbols: dict[str, Any] = {}
    for qualified_name in REQUIRED_LEGACY_SYMBOLS:
        module_name, short_name = qualified_name.rsplit(".", 1)
        module = modules.get(module_name)
        present = bool(module is not None and hasattr(module, short_name))
        symbols[qualified_name] = {
            "status": "present" if present else "missing",
            "present": present,
        }
        if module is None:
            symbols[qualified_name]["reason"] = f"{module_name} import failed"
    result["legacy_symbols"] = symbols
    result["required_legacy_symbols_present"] = all(
        item["present"] for item in symbols.values()
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe Torch/CUDA and legacy dependency symbols without importing "
            "SECOND detector modules."
        )
    )
    parser.add_argument(
        "--require-detector",
        action="store_true",
        help=(
            "return status 1 when any required legacy spconv symbol is absent; "
            "otherwise diagnostic failures remain status 0"
        ),
    )
    args = parser.parse_args(argv)

    report = {
        "probe": "second-pytorch-legacy-backend",
        "detector_import_attempted": False,
        "require_detector": bool(args.require_detector),
        "torch": _probe_torch(),
        "spconv": _probe_spconv(),
        "protobuf": _probe_simple_package("google.protobuf"),
        "numba": _probe_simple_package("numba"),
        "torchvision": _probe_simple_package("torchvision"),
    }
    report["required_legacy_symbols_present"] = bool(
        report["spconv"].get("required_legacy_symbols_present", False)
    )
    report["detector_gate"] = (
        "pass"
        if report["required_legacy_symbols_present"]
        else "blocked: required legacy spconv symbols are absent"
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    # Contract: this helper is diagnostic by default.  The only intentional
    # nonzero result is an explicit detector gate with missing legacy symbols.
    if args.require_detector and not report["required_legacy_symbols_present"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
