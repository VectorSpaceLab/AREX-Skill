#!/usr/bin/env python3
"""Check an environment for Object-Detection-Metrics helper/API use.

This diagnostic is safe by default: it does not use the network, open GUI
windows, write images, or mutate the user's environment. It can check only the
current Python and optional dependencies, or also verify source-style imports
from a user-provided checkout/copy via --repo-root or --lib-dir.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Object-Detection-Metrics runtime prerequisites.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--repo-root", type=Path, help="Checkout/copy containing a lib/ directory.")
    source.add_argument("--lib-dir", type=Path, help="Path directly to a copied lib directory.")
    parser.add_argument(
        "--require-api-deps",
        action="store_true",
        help="Require numpy, matplotlib, and cv2 imports for source API use.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of text.")
    return parser.parse_args()


def lib_dir_from_args(args: argparse.Namespace) -> Optional[Path]:
    if args.lib_dir is not None:
        return args.lib_dir.expanduser().resolve()
    if args.repo_root is not None:
        return (args.repo_root.expanduser().resolve() / "lib")
    return None


def check_import(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # intentionally broad for import-time shared library failures
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"name": name, "ok": True, "version": version}


def check_lib_dir(lib_dir: Path) -> Dict[str, Any]:
    report: Dict[str, Any] = {"path": str(lib_dir), "exists": lib_dir.exists(), "ok": False, "missing_files": []}
    if not lib_dir.exists() or not lib_dir.is_dir():
        report["error"] = "lib directory does not exist or is not a directory"
        return report
    required = ["BoundingBox.py", "BoundingBoxes.py", "Evaluator.py", "utils.py"]
    missing = [name for name in required if not (lib_dir / name).exists()]
    report["missing_files"] = missing
    if missing:
        report["error"] = "expected source files are missing"
        return report

    os.environ.setdefault("MPLBACKEND", "Agg")
    sys.path.insert(0, str(lib_dir))
    try:
        from BoundingBox import BoundingBox  # type: ignore
        from BoundingBoxes import BoundingBoxes  # type: ignore
        from Evaluator import Evaluator  # type: ignore
        from utils import BBFormat, BBType, CoordinatesType, MethodAveragePrecision  # type: ignore
    except Exception as exc:  # includes ImportError from cv2/matplotlib
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report

    try:
        boxes = BoundingBoxes()
        boxes.addBoundingBox(
            BoundingBox(
                "img-1",
                "person",
                0,
                0,
                10,
                10,
                CoordinatesType.Absolute,
                bbType=BBType.GroundTruth,
                format=BBFormat.XYX2Y2,
            )
        )
        boxes.addBoundingBox(
            BoundingBox(
                "img-1",
                "person",
                0,
                0,
                10,
                10,
                CoordinatesType.Absolute,
                bbType=BBType.Detected,
                classConfidence=0.9,
                format=BBFormat.XYX2Y2,
            )
        )
        result = Evaluator().GetPascalVOCMetrics(
            boxes,
            IOUThreshold=0.5,
            method=MethodAveragePrecision.EveryPointInterpolation,
        )[0]
        report.update(
            {
                "ok": True,
                "smoke": {
                    "class": result["class"],
                    "AP": float(result["AP"]),
                    "total positives": int(result["total positives"]),
                    "total TP": int(result["total TP"]),
                    "total FP": int(result["total FP"]),
                },
            }
        )
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    return report


def main() -> int:
    args = parse_args()
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "api_dependency_checks": [],
        "source_api_check": None,
        "ok": True,
        "notes": [
            "Folder evaluation helper is standard-library-only.",
            "Source API use requires a checkout/copy with lib/ on sys.path plus numpy, matplotlib, and cv2.",
        ],
    }

    if args.require_api_deps:
        deps: List[Dict[str, Any]] = [check_import(name) for name in ("numpy", "matplotlib", "cv2")]
        report["api_dependency_checks"] = deps
        if not all(item["ok"] for item in deps):
            report["ok"] = False

    lib_dir = lib_dir_from_args(args)
    if lib_dir is not None:
        source_report = check_lib_dir(lib_dir)
        report["source_api_check"] = source_report
        if not source_report.get("ok"):
            report["ok"] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Folder helper: OK (standard library only)")
        if args.require_api_deps:
            print("API dependency imports:")
            for item in report["api_dependency_checks"]:
                if item["ok"]:
                    suffix = f" {item['version']}" if item.get("version") else ""
                    print(f"  OK {item['name']}{suffix}")
                else:
                    print(f"  FAIL {item['name']}: {item['error']}")
        if report["source_api_check"] is not None:
            source = report["source_api_check"]
            if source.get("ok"):
                smoke = source["smoke"]
                print(
                    "Source API: OK "
                    f"class={smoke['class']} AP={smoke['AP']:.6f} "
                    f"TP={smoke['total TP']} FP={smoke['total FP']}"
                )
            else:
                print(f"Source API: FAIL {source.get('error', 'unknown error')}")
        print("PASS check_env" if report["ok"] else "FAIL check_env")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
