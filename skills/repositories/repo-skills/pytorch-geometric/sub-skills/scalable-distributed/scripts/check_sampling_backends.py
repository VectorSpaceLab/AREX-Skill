#!/usr/bin/env python3
"""Report PyTorch Geometric sampling backend availability as actionable JSON.

The script is intentionally safe: it does not allocate CUDA tensors, start
services, download data, compile extensions, or write files. It only imports
packages and reports what a future agent should check before large-graph,
remote-backend, or distributed PyG work.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class ImportStatus:
    importable: bool
    version: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "importable": self.importable,
            "version": self.version,
            "error": self.error,
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check safe PyTorch Geometric scaling prerequisites and optional "
            "sampling backends, then print actionable JSON."
        )
    )
    parser.add_argument(
        "--require-neighbor-backend",
        action="store_true",
        help="Exit nonzero when neither pyg-lib nor torch-sparse is importable.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    return parser.parse_args(argv)


def import_status(module_name: str) -> ImportStatus:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exact failures are environment-specific.
        return ImportStatus(importable=False, error=f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", None)
    if version is not None:
        version = str(version)
    return ImportStatus(importable=True, version=version)


def get_torch_report(status: ImportStatus) -> dict[str, Any]:
    report: dict[str, Any] = status.as_dict()
    if not status.importable:
        report.update(
            {
                "cuda_available": False,
                "cuda_version": None,
                "action": "Install torch before checking PyG sampling or distributed backends.",
            }
        )
        return report

    import torch

    cuda_available = bool(torch.cuda.is_available())
    report.update(
        {
            "cuda_available": cuda_available,
            "cuda_version": getattr(torch.version, "cuda", None),
            "action": (
                "CUDA is visible to torch; still verify extension wheel CUDA tags before GPU training."
                if cuda_available
                else "Torch is importable but CUDA is unavailable or this is a CPU-only build."
            ),
        }
    )
    return report


def get_torch_geometric_report(status: ImportStatus) -> dict[str, Any]:
    report: dict[str, Any] = status.as_dict()
    if not status.importable:
        report["action"] = "Install torch_geometric after installing a compatible torch build."
        return report

    try:
        from torch_geometric.loader import LinkNeighborLoader, NeighborLoader
        from torch_geometric.distributed import (
            DistLinkNeighborLoader,
            DistNeighborLoader,
            LocalFeatureStore,
            LocalGraphStore,
            Partitioner,
        )

        report.update(
            {
                "core_loader_api": {
                    "NeighborLoader": NeighborLoader.__name__,
                    "LinkNeighborLoader": LinkNeighborLoader.__name__,
                },
                "distributed_api": {
                    "Partitioner": Partitioner.__name__,
                    "LocalFeatureStore": LocalFeatureStore.__name__,
                    "LocalGraphStore": LocalGraphStore.__name__,
                    "DistNeighborLoader": DistNeighborLoader.__name__,
                    "DistLinkNeighborLoader": DistLinkNeighborLoader.__name__,
                },
                "action": "PyG core scaling APIs import successfully.",
            }
        )
    except Exception as exc:  # pragma: no cover - depends on partial installs.
        report.update(
            {
                "api_error": f"{type(exc).__name__}: {exc}",
                "action": "PyG imports, but scaling APIs did not import cleanly; check package integrity and optional dependencies.",
            }
        )
    return report


def build_report() -> dict[str, Any]:
    torch_status = import_status("torch")
    pyg_status = import_status("torch_geometric")
    optional_modules = {
        "pyg-lib": import_status("pyg_lib"),
        "torch-sparse": import_status("torch_sparse"),
        "torch-scatter": import_status("torch_scatter"),
    }
    neighbor_backend_available = any(
        optional_modules[name].importable for name in ("pyg-lib", "torch-sparse")
    )

    actions: list[str] = []
    if not torch_status.importable:
        actions.append("Install torch first; PyG and extension checks depend on it.")
    if not pyg_status.importable:
        actions.append("Install torch_geometric matching the active torch version.")
    if torch_status.importable and pyg_status.importable and not neighbor_backend_available:
        actions.append(
            "Install a compatible pyg-lib or torch-sparse wheel before iterating NeighborLoader, LinkNeighborLoader, or distributed neighbor samplers."
        )
    if optional_modules["torch-scatter"].importable is False:
        actions.append(
            "If model layers or older PyG paths require scatter kernels, install torch-scatter matching torch and CUDA/CPU tags."
        )
    if not actions:
        actions.append("Core imports and at least one neighbor sampling backend are available.")

    return {
        "ok": bool(torch_status.importable and pyg_status.importable),
        "python": {
            "version": platform.python_version(),
            "executable_basename": sys.executable.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
            "platform": platform.platform(),
        },
        "torch": get_torch_report(torch_status),
        "torch_geometric": get_torch_geometric_report(pyg_status),
        "optional_extensions": {
            name: status.as_dict() for name, status in optional_modules.items()
        },
        "neighbor_sampling_backend_available": neighbor_backend_available,
        "safe_behavior": {
            "cuda_allocation": False,
            "network": False,
            "downloads": False,
            "writes_files": False,
        },
        "actions": actions,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report()
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))

    if args.require_neighbor_backend and not report["neighbor_sampling_backend_available"]:
        return 2
    if not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
