#!/usr/bin/env python3
"""Check that an installed GluonTS environment matches the main skill routes.

This helper is intentionally checkout-independent: it imports the installed
`gluonts` package and selected optional modules, reports package/backend facts,
and exits non-zero only when required imports for the selected checks fail.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


CORE_IMPORTS = [
    "gluonts",
    "gluonts.dataset.pandas",
    "gluonts.dataset.split",
    "gluonts.transform",
    "gluonts.time_feature",
    "gluonts.model.forecast",
    "gluonts.model.predictor",
    "gluonts.evaluation",
    "gluonts.ev.metrics",
]

TORCH_IMPORTS = ["gluonts.torch", "torch", "lightning", "pytorch_lightning"]
SHELL_IMPORTS = ["gluonts.shell", "flask", "waitress"]

OPTIONAL_EXTRAS = {
    "arrow": ["pyarrow"],
    "prophet": ["prophet"],
    "statsforecast": ["statsforecast"],
    "hierarchicalforecast": ["hierarchicalforecast"],
    "rotbaum": ["xgboost", "sklearn"],
    "r": ["rpy2"],
    "shell": SHELL_IMPORTS,
    "torch": TORCH_IMPORTS,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import-check GluonTS core APIs and selected optional extras. "
            "No network, training, server startup, or repository checkout is needed."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--check-torch",
        action="store_true",
        help="Require gluonts.torch, torch, lightning, and pytorch_lightning imports.",
    )
    parser.add_argument(
        "--check-shell",
        action="store_true",
        help="Require gluonts.shell plus Flask/Waitress imports.",
    )
    parser.add_argument(
        "--optional-extra",
        choices=sorted(OPTIONAL_EXTRAS),
        action="append",
        default=[],
        help="Report/require imports for an optional extra. May be repeated.",
    )
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="If torch imports, report CUDA availability and allocate one tiny tensor when CUDA is available.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    return parser.parse_args()


def package_version(dist_name: str) -> str | None:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return None


def try_import(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "module": getattr(mod, "__name__", name)}
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report import failure.
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_cuda_smoke() -> dict[str, Any]:
    result: dict[str, Any] = {"requested": True}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"requested": True, "ok": False, "error": f"torch import failed: {exc}"}

    result.update(
        {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
    )
    if torch.cuda.is_available():
        try:
            tensor = torch.empty((1,), device="cuda")
            result.update(
                {
                    "ok": True,
                    "device_name": torch.cuda.get_device_name(0),
                    "device_capability": list(torch.cuda.get_device_capability(0)),
                    "tensor_device": str(tensor.device),
                }
            )
        except Exception as exc:  # noqa: BLE001
            result.update({"ok": False, "error": f"CUDA allocation failed: {exc}"})
    else:
        result.update({"ok": True, "note": "CUDA not available; GPU is optional for this skill."})
    return result


def main() -> int:
    args = parse_args()
    required = list(CORE_IMPORTS)
    if args.check_torch:
        required.extend(TORCH_IMPORTS)
    if args.check_shell:
        required.extend(SHELL_IMPORTS)
    for extra in args.optional_extra:
        required.extend(OPTIONAL_EXTRAS[extra])

    seen: set[str] = set()
    imports = []
    for name in required:
        if name not in seen:
            imports.append(try_import(name))
            seen.add(name)

    report: dict[str, Any] = {
        "status": "ok" if all(item["ok"] for item in imports) else "failed",
        "versions": {
            "gluonts": package_version("gluonts"),
            "torch": package_version("torch"),
            "lightning": package_version("lightning"),
            "pytorch-lightning": package_version("pytorch-lightning"),
        },
        "imports": imports,
        "optional_notes": {
            "mxnet": "Legacy MXNet workflows are not part of the verified required scope.",
            "external_adapters": "Prophet/R/statsforecast/hierarchicalforecast/rotbaum need their documented extras before use.",
        },
    }
    if args.cuda_smoke:
        report["cuda"] = run_cuda_smoke()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"GluonTS version: {report['versions']['gluonts']}")
        for item in imports:
            if item["ok"]:
                print(f"OK import {item['name']}")
            else:
                print(f"FAIL import {item['name']}: {item['error']}")
        if args.cuda_smoke:
            print("CUDA:", json.dumps(report["cuda"], sort_keys=True))

    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
