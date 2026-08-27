#!/usr/bin/env python3
"""Safe import/version/backend check for PyTorch Geometric Temporal.

The script performs no downloads, does not construct dataset loaders, and prints
only package/module facts rather than local filesystem paths.

Examples:
    python scripts/check_environment.py
    python scripts/check_environment.py --json
    python scripts/check_environment.py --backend cuda --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def try_import(module: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(module)
        return True, None
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report concise import failure.
        return False, f"{type(exc).__name__}: {exc}"


def collect(backend: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": True,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "distributions": {},
        "imports": {},
        "backend": {},
        "warnings": [],
    }

    for dist in [
        "torch-geometric-temporal",
        "torch_geometric_temporal",
        "torch",
        "torch-geometric",
        "torch_geometric",
        "dask",
        "pandas",
        "tables",
    ]:
        version = distribution_version(dist)
        if version is not None:
            result["distributions"][dist] = version

    for module in [
        "torch",
        "torch_geometric",
        "torch_geometric_temporal",
        "torch_geometric_temporal.signal",
        "torch_geometric_temporal.dataset",
        "torch_geometric_temporal.nn.recurrent",
        "torch_geometric_temporal.nn.attention",
        "torch_geometric_temporal.nn.hetero",
        "torch_geometric_temporal.signal.index_dataset",
    ]:
        ok, error = try_import(module)
        result["imports"][module] = {"ok": ok}
        if error:
            result["imports"][module]["error"] = error
            result["ok"] = False

    if result["imports"].get("torch_geometric_temporal", {}).get("ok"):
        import torch_geometric_temporal as pgt  # type: ignore

        result["pgt_version_constant"] = getattr(pgt, "__version__", None)
        dist_version = result["distributions"].get("torch_geometric_temporal") or result["distributions"].get(
            "torch-geometric-temporal"
        )
        if dist_version and result["pgt_version_constant"] and dist_version != result["pgt_version_constant"]:
            result["warnings"].append(
                "distribution metadata version differs from torch_geometric_temporal.__version__"
            )

    if result["imports"].get("torch", {}).get("ok"):
        import torch  # type: ignore

        result["backend"]["torch_version"] = getattr(torch, "__version__", None)
        result["backend"]["cuda_available"] = bool(torch.cuda.is_available())
        if backend == "cpu":
            tensor = torch.zeros(1)
            result["backend"]["cpu_tensor_ok"] = bool(tensor.numel() == 1)
        elif backend == "cuda":
            if not torch.cuda.is_available():
                result["backend"]["cuda_tensor_ok"] = False
                result["ok"] = False
                result["warnings"].append("CUDA backend requested but torch.cuda.is_available() is false")
            else:
                tensor = torch.zeros(1, device="cuda")
                result["backend"]["cuda_tensor_ok"] = bool(tensor.numel() == 1)

    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PyTorch Geometric Temporal imports and optional backend availability.")
    parser.add_argument("--backend", choices=["cpu", "cuda", "none"], default="cpu", help="Backend smoke to run.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = collect(args.backend)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "ok" if result["ok"] else "failed"
        print(f"status: {status}")
        print(f"python: {result['python']}")
        for dist, version in sorted(result["distributions"].items()):
            print(f"{dist}: {version}")
        for module, info in sorted(result["imports"].items()):
            line = f"import {module}: {'ok' if info['ok'] else 'failed'}"
            if "error" in info:
                line += f" ({info['error']})"
            print(line)
        for key, value in sorted(result["backend"].items()):
            print(f"{key}: {value}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
