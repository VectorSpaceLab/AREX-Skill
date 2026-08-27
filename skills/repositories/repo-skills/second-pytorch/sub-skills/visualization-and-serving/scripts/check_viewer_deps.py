#!/usr/bin/env python3
"""Report web-viewer dependency availability without starting a service.

This diagnostic is intentionally read-only and safe to run from any working
 directory. It does not import the historical Flask application, load a
 dataset/checkpoint, contact a browser, or launch a server.

Examples:
  python check_viewer_deps.py --help
  python check_viewer_deps.py
  python check_viewer_deps.py --json

A missing optional or legacy component is reported in the result and does not
make the diagnostic itself fail. A non-zero exit is reserved for an internal
checker error.
"""

import argparse
import importlib
import json
import sys
import warnings
from typing import Any, Dict, List, Optional


Result = Dict[str, Any]


def _version(module_name: str) -> Optional[str]:
    """Return a module version without making version lookup a requirement."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            module = importlib.import_module(module_name)
            value = getattr(module, "__version__", None)
        return str(value) if value is not None else None
    except Exception:
        return None


def _check_import(name: str, module_name: str, symbol: str | None = None) -> Result:
    """Check one module or module attribute and capture a short failure."""
    try:
        # Some installed ML packages emit deprecation warnings during import;
        # the report records availability, while keeping JSON output clean.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            module = importlib.import_module(module_name)
        if symbol is not None:
            getattr(module, symbol)
        return {
            "name": name,
            "module": module_name,
            "symbol": symbol,
            "available": True,
            "version": _version(module_name),
            "error": None,
        }
    except Exception as exc:  # import diagnostics should not emit a traceback
        return {
            "name": name,
            "module": module_name,
            "symbol": symbol,
            "available": False,
            "version": None,
            "error": f"{type(exc).__name__}: {str(exc).splitlines()[0][:240]}",
        }


def collect() -> Dict[str, Any]:
    """Collect web, detector, and legacy-symbol checks without side effects."""
    checks: List[Result] = [
        _check_import("flask", "flask"),
        _check_import("flask-cors", "flask_cors", "CORS"),
        _check_import("scikit-image", "skimage"),
        _check_import("scikit-image.io", "skimage.io", "imread"),
        _check_import("fire CLI", "fire"),
        _check_import("PyTorch", "torch"),
        _check_import("spconv", "spconv"),
        _check_import("spconv.SubMConv3d", "spconv", "SubMConv3d"),
        _check_import("spconv.SparseConv3d", "spconv", "SparseConv3d"),
        _check_import("spconv.SparseSequential", "spconv", "SparseSequential"),
        _check_import("spconv.SparseConvTensor", "spconv", "SparseConvTensor"),
        _check_import("spconv.SparseModule", "spconv", "SparseModule"),
        _check_import("legacy VoxelGeneratorV2", "spconv.utils", "VoxelGeneratorV2"),
        _check_import(
            "legacy non_max_suppression",
            "spconv.utils",
            "non_max_suppression",
        ),
    ]
    web_names = {"flask", "flask-cors", "scikit-image", "scikit-image.io", "fire CLI"}
    detector_names = {
        "PyTorch",
        "spconv",
        "spconv.SubMConv3d",
        "spconv.SparseConv3d",
        "spconv.SparseSequential",
        "spconv.SparseConvTensor",
        "spconv.SparseModule",
    }
    legacy_names = {"legacy VoxelGeneratorV2", "legacy non_max_suppression"}
    for item in checks:
        if item["name"] in web_names:
            item["group"] = "web-runtime"
            item["optional_for"] = "web viewer import"
        elif item["name"] in detector_names:
            item["group"] = "detector-runtime"
            item["optional_for"] = "checkpoint build/inference"
        else:
            item["group"] = "legacy-detector-symbols"
            item["optional_for"] = "historical detector compatibility"

    return {
        "schema": "second-pytorch.viewer-dependency-check.v1",
        "service_started": False,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "available": sum(1 for item in checks if item["available"]),
            "missing": sum(1 for item in checks if not item["available"]),
            "legacy_symbols_available": all(
                item["available"] for item in checks if item["name"] in legacy_names
            ),
        },
        "interpretation": [
            "Missing components are diagnostic findings, not checker failures.",
            "A passing import check does not prove detector execution.",
            "Modern spconv symbols do not establish compatibility with legacy symbols.",
        ],
    }


def _text_report(report: Dict[str, Any]) -> str:
    lines = [
        "Viewer dependency report (no service started)",
        "=" * 44,
    ]
    for item in report["checks"]:
        state = "OK" if item["available"] else "MISSING"
        target = item["module"]
        if item["symbol"]:
            target += "." + item["symbol"]
        detail = ""
        if item["version"]:
            detail = f" (version {item['version']})"
        if item["error"]:
            detail = f" - {item['error']}"
        lines.append(f"[{state:7}] {item['name']}: {target}{detail}")
    summary = report["summary"]
    lines.extend(
        [
            "",
            f"Available: {summary['available']}/{summary['total']}; "
            f"missing: {summary['missing']}",
            "Legacy detector symbols available: "
            + str(summary["legacy_symbols_available"]),
            "A dependency report is not detector or server verification.",
        ]
    )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Flask/CORS, scikit-image, PyTorch, spconv, and legacy "
            "viewer symbols without launching a service."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the stable machine-readable report instead of text",
    )
    args = parser.parse_args(argv)
    try:
        report = collect()
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(_text_report(report))
        return 0
    except Exception as exc:  # keep unexpected checker defects explicit
        print(f"checker error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
