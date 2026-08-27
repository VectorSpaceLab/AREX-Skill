#!/usr/bin/env python3
"""Check optional dependencies for Keras Attention visualization examples.

The core `Attention` layer does not need these extras. Use this script before
attempting attention-map visualizations that rely on keract, matplotlib, pydot,
or Graphviz model diagrams. The script performs import/tool checks only; it does
not run long training or download datasets.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check optional example dependencies for keras-attention.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit 0 even when optional dependencies are missing; useful for reporting only.",
    )
    return parser.parse_args()


def check_import(module: str, display: str | None = None) -> CheckResult:
    display = display or module
    try:
        imported = importlib.import_module(module)
        version = getattr(imported, "__version__", "version unknown")
        return CheckResult(display, True, f"imported {module} ({version})")
    except Exception as exc:  # noqa: BLE001 - report arbitrary import failures clearly.
        return CheckResult(display, False, f"failed to import {module}: {exc}")


def check_graphviz_dot() -> CheckResult:
    dot = shutil.which("dot")
    if not dot:
        return CheckResult("Graphviz dot", False, "dot executable not found on PATH")
    try:
        proc = subprocess.run([dot, "-V"], capture_output=True, text=True, timeout=10, check=False)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Graphviz dot", False, f"dot -V failed: {exc}")
    combined = (proc.stdout + proc.stderr).strip()
    return CheckResult("Graphviz dot", proc.returncode == 0, combined or f"dot returned {proc.returncode}")


def check_plot_model_import() -> CheckResult:
    try:
        from tensorflow.python.keras.utils.vis_utils import plot_model  # noqa: PLC0415

        return CheckResult("tensorflow plot_model", callable(plot_model), "tensorflow.python.keras.utils.vis_utils.plot_model imported")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("tensorflow plot_model", False, f"failed to import plot_model: {exc}")


def main() -> int:
    args = parse_args()
    results = [
        check_import("tensorflow"),
        check_import("keras", "standalone keras import"),
        check_import("keract"),
        check_import("matplotlib"),
        check_import("pydot"),
        check_plot_model_import(),
        check_graphviz_dot(),
    ]

    backend = os.environ.get("MPLBACKEND")
    if backend:
        results.append(CheckResult("MPLBACKEND", True, f"MPLBACKEND={backend}"))
    else:
        results.append(CheckResult("MPLBACKEND", True, "not set; set MPLBACKEND=Agg for headless plotting"))

    all_ok = all(result.ok for result in results if result.name != "MPLBACKEND")
    payload = {"status": "passed" if all_ok else "missing", "results": [asdict(result) for result in results]}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Optional example dependency check: {payload['status']}")
        for result in results:
            mark = "PASS" if result.ok else "FAIL"
            print(f"[{mark}] {result.name}: {result.detail}")

    if all_ok or args.allow_missing:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
