#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version as pkg_version
from typing import Any

SURFACES = [
    "spikingjelly.activation_based",
    "spikingjelly.datasets",
    "spikingjelly.timing_based",
    "spikingjelly.visualizing",
]
OPTIONAL_MODULES = ["cupy", "triton", "nir", "nirtorch", "transformers"]


def probe_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"imported": False, "error": f"{type(exc).__name__}: {exc}"}

    info: dict[str, Any] = {"imported": True}
    module_file = getattr(module, "__file__", None)
    if module_file:
        info["file"] = module_file

    if name == "spikingjelly":
        try:
            info["version"] = pkg_version("spikingjelly")
        except PackageNotFoundError:
            info["version"] = None
    elif name == "torch":
        info["version"] = getattr(module, "__version__", None)
        cuda_available = bool(module.cuda.is_available())
        info["cuda_available"] = cuda_available
        if cuda_available:
            info["cuda_device_count"] = module.cuda.device_count()
            info["cuda_device_names"] = [
                module.cuda.get_device_name(i) for i in range(module.cuda.device_count())
            ]
    else:
        info["version"] = getattr(module, "__version__", None)

    return info


def build_report() -> dict[str, Any]:
    report = {
        "spikingjelly": probe_module("spikingjelly"),
        "torch": probe_module("torch"),
    }
    report["submodules"] = {name: probe_module(name) for name in SURFACES}
    report["optional"] = {name: probe_module(name) for name in OPTIONAL_MODULES}
    return report


def pretty_print(report: dict[str, Any]) -> str:
    lines: list[str] = []

    def emit(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                child = f"{prefix}.{key}" if prefix else key
                emit(child, item)
        else:
            lines.append(f"{prefix}: {value}")

    emit("", report)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize the installed SpikingJelly environment."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON instead of a human-readable summary",
    )
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(pretty_print(report))


if __name__ == "__main__":
    main()
