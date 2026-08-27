#!/usr/bin/env python3
"""Read-only dependency/backend check for Nesa demo workflows.

This script does not import the Nesa source checkout. It reports whether the
current Python environment has the packages commonly needed by the generated
Nesa skill routes and whether PyTorch sees an accelerator.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any

PACKAGE_CHECKS = {
    "backend-core": [
        ("msgspec", "msgspec"),
        ("pydantic-settings", "pydantic_settings"),
        ("python-dotenv", "dotenv"),
        ("nats-py", "nats"),
        ("httpx", "httpx"),
        ("requests", "requests"),
        ("tqdm", "tqdm"),
        ("pyyaml", "yaml"),
    ],
    "local-model": [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("safetensors", "safetensors"),
    ],
    "web-ui": [
        ("gradio", "gradio"),
        ("accelerate", "accelerate"),
        ("psutil", "psutil"),
        ("markdown", "markdown"),
        ("numba", "numba"),
    ],
}


def check_import(distribution: str, module: str) -> dict[str, Any]:
    row: dict[str, Any] = {"distribution": distribution, "module": module}
    try:
        row["version"] = metadata.version(distribution)
    except metadata.PackageNotFoundError:
        row["version"] = None
    try:
        importlib.import_module(module)
        row["import"] = "ok"
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        row["import"] = "failed"
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def torch_backend_summary() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"torch_import": "failed", "error": f"{type(exc).__name__}: {exc}"}

    summary: dict[str, Any] = {
        "torch_import": "ok",
        "torch_version": getattr(torch, "__version__", None),
        "cuda_available": bool(getattr(torch, "cuda", None) and torch.cuda.is_available()),
    }
    if summary["cuda_available"]:
        summary["cuda_device_count"] = torch.cuda.device_count()
        summary["cuda_device_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    try:
        summary["cpu_tensor_smoke"] = (torch.tensor([1, 2, 3]) + 1).tolist()
    except Exception as exc:  # noqa: BLE001
        summary["cpu_tensor_smoke_error"] = f"{type(exc).__name__}: {exc}"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Check packages needed by Nesa demo workflows.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--group",
        choices=sorted(PACKAGE_CHECKS),
        action="append",
        help="Limit checks to one or more dependency groups.",
    )
    args = parser.parse_args()

    selected = args.group or ["backend-core", "local-model"]
    result: dict[str, Any] = {
        "python": sys.version,
        "executable": sys.executable,
        "groups": {},
        "torch_backend": torch_backend_summary(),
    }
    for group in selected:
        result["groups"][group] = [check_import(dist, mod) for dist, mod in PACKAGE_CHECKS[group]]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python'].split()[0]}")
        for group, rows in result["groups"].items():
            print(f"\n[{group}]")
            for row in rows:
                status = row["import"]
                version = row.get("version") or "not-installed"
                extra = f" ({row.get('error')})" if row.get("error") else ""
                print(f"- {row['module']}: {status}; distribution {row['distribution']}={version}{extra}")
        print("\n[torch-backend]")
        for key, value in result["torch_backend"].items():
            print(f"- {key}: {value}")

    failed = any(row["import"] != "ok" for group in result["groups"].values() for row in group)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
