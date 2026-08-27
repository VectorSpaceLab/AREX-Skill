#!/usr/bin/env python3
"""Safe DGL environment diagnostic for repo-skill users.

This script imports DGL, checks backend/package versions, probes GraphBolt and
DGL sparse availability, and runs tiny CPU-only smoke checks. It performs no
network access, downloads, training, source-build steps, or destructive writes.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
import tempfile
from pathlib import Path


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe DGL import/backend diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text report.")
    parser.add_argument("--skip-smoke", action="store_true", help="Only import modules and report versions.")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "packages": {
            "dgl": package_version("dgl"),
            "torch": package_version("torch"),
            "torchdata": package_version("torchdata"),
            "numpy": package_version("numpy"),
        },
        "env": {
            "DGLBACKEND": os.environ.get("DGLBACKEND"),
            "DGL_LIBRARY_PATH_set": bool(os.environ.get("DGL_LIBRARY_PATH")),
        },
        "checks": [],
        "errors": [],
        "warnings": [],
    }

    checks: list[str] = report["checks"]  # type: ignore[assignment]
    errors: list[str] = report["errors"]  # type: ignore[assignment]
    warnings: list[str] = report["warnings"]  # type: ignore[assignment]

    try:
        import dgl

        checks.append(f"import dgl ok: {getattr(dgl, '__version__', 'unknown')}")
        report["dgl_backend"] = getattr(getattr(dgl, "backend", None), "backend_name", None)
    except Exception as exc:  # noqa: BLE001 - diagnostic should capture exact import failure.
        errors.append(f"import dgl failed: {type(exc).__name__}: {exc}")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_report(report)
        return 1

    try:
        torch = importlib.import_module("torch")
        checks.append(f"import torch ok: {getattr(torch, '__version__', 'unknown')}")
        report["torch_cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"torch import failed: {type(exc).__name__}: {exc}")

    try:
        gb = importlib.import_module("dgl.graphbolt")
        checks.append(f"import dgl.graphbolt ok: ItemSet={hasattr(gb, 'ItemSet')}")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"dgl.graphbolt import failed: {type(exc).__name__}: {exc}")

    try:
        dglsp = importlib.import_module("dgl.sparse")
        checks.append(f"import dgl.sparse ok: spmatrix={hasattr(dglsp, 'spmatrix')}")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"dgl.sparse import failed: {type(exc).__name__}: {exc}")

    if not args.skip_smoke:
        try:
            import torch
            import dgl

            src = torch.tensor([0, 1, 2])
            dst = torch.tensor([1, 2, 0])
            graph = dgl.graph((src, dst), num_nodes=3)
            graph.ndata["feat"] = torch.ones(3, 2)
            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "tiny_graph.bin"
                dgl.save_graphs(str(path), [graph], {"label": torch.tensor([1])})
                loaded, labels = dgl.load_graphs(str(path))
            assert len(loaded) == 1
            assert loaded[0].num_edges() == 3
            assert labels["label"].tolist() == [1]
            checks.append("graph construction and save/load smoke ok")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"graph smoke failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)
    return 0 if not errors else 1


def print_report(report: dict[str, object]) -> None:
    print("DGL environment diagnostic")
    print(f"Python: {report['python']}")
    print("Packages:")
    for name, version in (report.get("packages") or {}).items():
        print(f"  {name}: {version or 'not installed'}")
    if report.get("dgl_backend"):
        print(f"DGL backend: {report['dgl_backend']}")
    if "torch_cuda_available" in report:
        print(f"Torch CUDA available: {report['torch_cuda_available']}")
    print("Checks:")
    for item in report.get("checks", []):
        print(f"  PASS {item}")
    for item in report.get("warnings", []):
        print(f"  WARN {item}")
    for item in report.get("errors", []):
        print(f"  FAIL {item}")


if __name__ == "__main__":
    raise SystemExit(main())
