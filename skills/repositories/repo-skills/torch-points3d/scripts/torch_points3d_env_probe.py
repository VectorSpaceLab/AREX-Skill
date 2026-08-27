#!/usr/bin/env python3
"""Safe Torch Points3D environment probe.

This helper is adapted from Torch Points3D environment diagnostics. It reports
package/import/backend availability without printing local install paths,
downloading data, writing files, or allocating GPUs.

Examples:
  python scripts/torch_points3d_env_probe.py
  python scripts/torch_points3d_env_probe.py --json --require-package --require-pyg
  python scripts/torch_points3d_env_probe.py --require-sparse-backend
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from importlib import metadata
from typing import Any, Dict, Iterable, Optional, Tuple


def dist_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def import_status(module: str) -> Tuple[bool, Optional[str]]:
    try:
        importlib.import_module(module)
        return True, None
    except Exception as exc:  # noqa: BLE001 - diagnostic should capture any import failure.
        return False, f"{type(exc).__name__}: {exc}"


def probe(deep: bool = False) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "distributions": {
            "torch-points3d": dist_version("torch-points3d"),
            "torch": dist_version("torch"),
            "torchvision": dist_version("torchvision"),
            "torch-geometric": dist_version("torch-geometric"),
            "torch-scatter": dist_version("torch-scatter"),
            "torch-sparse": dist_version("torch-sparse"),
            "torch-cluster": dist_version("torch-cluster"),
            "torch-points-kernels": dist_version("torch-points-kernels"),
            "hydra-core": dist_version("hydra-core"),
            "omegaconf": dist_version("omegaconf"),
            "numpy": dist_version("numpy"),
            "protobuf": dist_version("protobuf"),
        },
        "imports": {},
        "torch": {},
        "optional_backends": {},
        "deep_imports": {},
    }

    for module in [
        "torch",
        "torch_points3d",
        "torch_geometric",
        "torch_scatter",
        "torch_sparse",
        "torch_cluster",
        "torch_points_kernels",
        "hydra",
        "omegaconf",
    ]:
        ok, error = import_status(module)
        result["imports"][module] = {"ok": ok, "error": error}

    torch_ok, _ = import_status("torch")
    if torch_ok:
        import torch

        result["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_compiled": getattr(torch.version, "cuda", None),
            "cudnn_version": torch.backends.cudnn.version() if hasattr(torch.backends, "cudnn") else None,
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        }

    for module in ["MinkowskiEngine", "torchsparse", "pycuda"]:
        ok, error = import_status(module)
        result["optional_backends"][module] = {"ok": ok, "error": error}

    if deep:
        for module in [
            "torch_points3d.applications.pointnet2",
            "torch_points3d.applications.kpconv",
            "torch_points3d.applications.rsconv",
            "torch_points3d.applications.sparseconv3d",
            "torch_points3d.datasets.dataset_factory",
            "torch_points3d.core.data_transform",
            "torch_points3d.trainer",
        ]:
            ok, error = import_status(module)
            result["deep_imports"][module] = {"ok": ok, "error": error}

    return result


def missing_required(result: Dict[str, Any], args: argparse.Namespace) -> Iterable[str]:
    if args.require_package and not result["imports"].get("torch_points3d", {}).get("ok"):
        yield "torch_points3d package import failed"
    if args.require_pyg:
        for module in ["torch_geometric", "torch_scatter", "torch_sparse", "torch_cluster"]:
            if not result["imports"].get(module, {}).get("ok"):
                yield f"required PyG dependency import failed: {module}"
    if args.require_sparse_backend:
        sparse_ok = any(result["optional_backends"][m]["ok"] for m in ["MinkowskiEngine", "torchsparse"])
        if not sparse_ok:
            yield "neither MinkowskiEngine nor torchsparse imports; sparse Torch Points3D models are unavailable"


def print_text(result: Dict[str, Any]) -> None:
    print("Torch Points3D environment probe")
    print(f"Python: {result['python']['version']} ({result['python']['implementation']})")
    print("Distributions:")
    for name, version in result["distributions"].items():
        print(f"  {name}: {version or 'not installed'}")
    print("Imports:")
    for name, status in result["imports"].items():
        suffix = "ok" if status["ok"] else f"missing/error ({status['error']})"
        print(f"  {name}: {suffix}")
    if result["torch"]:
        print("Torch backend:")
        for key, value in result["torch"].items():
            print(f"  {key}: {value}")
    print("Optional backends:")
    for name, status in result["optional_backends"].items():
        suffix = "ok" if status["ok"] else f"missing/error ({status['error']})"
        print(f"  {name}: {suffix}")
    if result["deep_imports"]:
        print("Deep Torch Points3D imports:")
        for name, status in result["deep_imports"].items():
            suffix = "ok" if status["ok"] else f"missing/error ({status['error']})"
            print(f"  {name}: {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Torch Points3D imports, versions, and optional backends safely.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--deep", action="store_true", help="Also import application APIs, dataset factory, transforms, and Trainer.")
    parser.add_argument("--require-package", action="store_true", help="Exit non-zero if torch_points3d cannot import.")
    parser.add_argument("--require-pyg", action="store_true", help="Exit non-zero if core PyG extension packages cannot import.")
    parser.add_argument("--require-sparse-backend", action="store_true", help="Exit non-zero unless MinkowskiEngine or torchsparse imports.")
    args = parser.parse_args()

    result = probe(deep=args.deep)
    problems = list(missing_required(result, args))
    result["problems"] = problems

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
        if problems:
            print("Required checks failed:")
            for problem in problems:
                print(f"  - {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
