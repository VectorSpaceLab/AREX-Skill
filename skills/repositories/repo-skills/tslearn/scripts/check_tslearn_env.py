#!/usr/bin/env python3
"""Check that tslearn and its common optional dependencies import cleanly.

This helper is intentionally tiny and safe: it imports tslearn, prints public
package versions, and runs one or two very small numerical checks. Use
--repo-root when you want to point the script at a local checkout before
importing tslearn from that checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np


def maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = import_module(module_name)
    except Exception as exc:  # pragma: no cover - import dependent
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "module": getattr(module, "__name__", module_name),
        "file": getattr(module, "__file__", None),
        "version": getattr(module, "__version__", None),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional local tslearn checkout to add to sys.path before import.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable text.",
    )
    args = parser.parse_args()

    maybe_add_repo_root(args.repo_root)

    summary: dict[str, Any] = {"packages": {}, "modules": {}, "smoke": {}}

    try:
        import tslearn
        from tslearn.backend import instantiate_backend
        from tslearn.matrix_profile import MatrixProfile
        from tslearn.metrics import dtw
    except Exception as exc:
        print(f"ERROR: failed to import tslearn core modules: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    summary["packages"]["tslearn"] = package_version("tslearn")
    for name in ["numpy", "scipy", "scikit-learn", "numba", "joblib", "statsmodels", "pandas", "h5py", "stumpy", "keras", "torch"]:
        summary["packages"][name] = package_version(name)

    for module_name in [
        "tslearn",
        "tslearn.utils",
        "tslearn.preprocessing",
        "tslearn.piecewise",
        "tslearn.metrics",
        "tslearn.barycenters",
        "tslearn.clustering",
        "tslearn.neighbors",
        "tslearn.svm",
        "tslearn.forecasting",
        "tslearn.matrix_profile",
    ]:
        summary["modules"][module_name] = import_status(module_name)

    summary["smoke"]["tslearn_version"] = getattr(tslearn, "__version__", None)
    summary["smoke"]["backend_numpy"] = instantiate_backend("numpy").backend_string
    summary["smoke"]["dtw"] = float(dtw([[1.0], [2.0]], [[1.0], [2.0]]))
    summary["smoke"]["matrix_profile_numpy_shape"] = list(
        MatrixProfile(subsequence_length=2).fit_transform(np.array([[[1.0], [2.0], [3.0]]])).shape
    )

    torch_info = import_status("torch")
    summary["modules"]["torch"] = torch_info
    if torch_info["available"]:
        try:
            import torch
            summary["smoke"]["torch_cuda_available"] = bool(torch.cuda.is_available())
        except Exception as exc:  # pragma: no cover - import dependent
            summary["smoke"]["torch_cuda_error"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"tslearn: {summary['packages']['tslearn']}")
        print(f"core backend: {summary['smoke']['backend_numpy']}")
        print(f"dtw smoke: {summary['smoke']['dtw']}")
        print(f"matrix profile shape: {summary['smoke']['matrix_profile_numpy_shape']}")
        print("optional packages:")
        for name in ["pandas", "h5py", "stumpy", "keras", "torch"]:
            print(f"  - {name}: {summary['packages'][name] or 'missing'}")
        if torch_info["available"]:
            print(f"torch cuda available: {summary['smoke'].get('torch_cuda_available', False)}")
        print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
