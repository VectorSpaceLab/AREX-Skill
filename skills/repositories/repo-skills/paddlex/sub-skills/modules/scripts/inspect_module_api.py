#!/usr/bin/env python3
"""Safe inspector for PaddleX module-mode APIs and engine branches.

This helper only prints already-installed package facts. It does not train,
export, download, or invoke repository-native examples.
"""

from __future__ import annotations

import argparse
import inspect
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


ENGINE_MODES = [
    "check_dataset",
    "train",
    "evaluate",
    "export",
    "pdparams2safetensors",
    "predict",
]


def _signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<unavailable>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect PaddleX module APIs, engine modes, and entrypoint facts."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a short report.",
    )
    args = parser.parse_args(argv)

    try:
        from paddlex import create_model
        from paddlex.modules import (
            build_dataset_checker,
            build_evaluator,
            build_exportor,
            build_trainer,
            build_weight_converter,
        )
    except ModuleNotFoundError as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")

    try:
        paddlex_version = version("paddlex")
    except PackageNotFoundError:
        paddlex_version = "unknown"

    report = {
        "package": {
            "name": "paddlex",
            "version": paddlex_version,
        },
        "signatures": {
            "create_model": _signature_text(create_model),
            "build_dataset_checker": _signature_text(build_dataset_checker),
            "build_evaluator": _signature_text(build_evaluator),
            "build_exportor": _signature_text(build_exportor),
            "build_trainer": _signature_text(build_trainer),
            "build_weight_converter": _signature_text(build_weight_converter),
        },
        "engine_modes": ENGINE_MODES,
        "entrypoints": {
            "module_engine": "installed paddlex.engine.Engine().run() via bundled helper",
            "public_cli": "paddlex (pipeline / serving / install / paddle2onnx)",
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"paddlex {report['package']['version']}")
    for name, sig in report["signatures"].items():
        print(f"{name}{sig}")
    print("engine_modes:")
    for mode in ENGINE_MODES:
        print(f"  - {mode}")
    print("entrypoints:")
    for key, value in report["entrypoints"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
