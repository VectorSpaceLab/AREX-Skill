#!/usr/bin/env python3
"""Safe import and version smoke check for SageMaker Python SDK v3.

This helper performs only local imports and optional CUDA inspection. It does
not submit SageMaker jobs, create endpoints, or make other cloud calls.

The script is intended for use with an installed SageMaker v3 environment.
It can be run from any working directory.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_REGION = "us-west-2"

MODULES = [
    "sagemaker",
    "sagemaker.core",
    "sagemaker.train",
    "sagemaker.serve",
    "sagemaker.mlops",
]

OPTIONAL_MODULES = [
    "sagemaker.ai_registry.dataset",
    "sagemaker.train.evaluate",
    "sagemaker.mlops.feature_store",
]

DISTRIBUTIONS = [
    "sagemaker",
    "sagemaker-core",
    "sagemaker-train",
    "sagemaker-serve",
    "sagemaker-mlops",
    "mlflow",
    "torch",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        default=None,
        help=(
            "AWS region to set for the import probe. If omitted, the script uses "
            "AWS_REGION/AWS_DEFAULT_REGION when present and falls back to us-west-2."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--no-cuda",
        action="store_true",
        help="Skip the optional torch CUDA smoke even if torch is installed.",
    )
    return parser.parse_args()


def configure_region(region: str | None) -> str:
    chosen = region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or DEFAULT_REGION
    os.environ["AWS_REGION"] = chosen
    os.environ["AWS_DEFAULT_REGION"] = chosen
    return chosen


def import_modules(module_names: List[str]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for name in module_names:
        module = importlib.import_module(name)
        results[name] = getattr(module, "__file__", None)
    return results


def get_repo_version() -> str | None:
    for parent in Path(__file__).resolve().parents:
        repo_version_file = parent / "VERSION"
        if repo_version_file.exists():
            value = repo_version_file.read_text(encoding="utf-8").strip()
            return value or None
    return None


def get_distribution_versions(names: List[str]) -> Dict[str, str | None]:
    versions: Dict[str, str | None] = {}
    repo_version = get_repo_version()
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = repo_version if name == "sagemaker" else None
    return versions


def probe_cuda() -> Dict[str, Any]:
    info: Dict[str, Any] = {"available": False}
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # pragma: no cover - import-time fallback
        info["error"] = f"torch import failed: {exc}"
        return info

    try:
        cuda_available = bool(torch.cuda.is_available())
        info["available"] = cuda_available
        info["device_count"] = int(torch.cuda.device_count()) if cuda_available else 0
        if cuda_available:
            tensor = torch.tensor([1.0], device="cuda")
            info["tensor_smoke"] = float(tensor.cpu().item())
    except Exception as exc:  # pragma: no cover - hardware/runtime fallback
        info["error"] = str(exc)
    return info


def main() -> int:
    args = parse_args()
    region = configure_region(args.region)

    payload: Dict[str, Any] = {
        "region": region,
        "imports": {},
        "optional_imports": {},
        "versions": get_distribution_versions(DISTRIBUTIONS),
        "cuda": {"skipped": args.no_cuda},
    }

    failures: List[str] = []
    try:
        payload["imports"] = import_modules(MODULES)
    except Exception as exc:
        failures.append(f"required import failed: {exc}")

    for module_name in OPTIONAL_MODULES:
        try:
            payload["optional_imports"][module_name] = getattr(importlib.import_module(module_name), "__file__", None)
        except Exception as exc:  # pragma: no cover - optional import fallback
            payload["optional_imports"][module_name] = f"ERROR: {exc}"

    if not args.no_cuda:
        payload["cuda"] = probe_cuda()

    payload["status"] = "ok" if not failures else "error"
    payload["failures"] = failures

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"region={region}")
        print("required imports:")
        for name, path in payload["imports"].items():
            print(f"  - {name}: {path}")
        print("optional imports:")
        for name, path in payload["optional_imports"].items():
            print(f"  - {name}: {path}")
        print("versions:")
        for name, version in payload["versions"].items():
            print(f"  - {name}: {version}")
        print(f"cuda: {payload['cuda']}")
        if failures:
            print("failures:")
            for failure in failures:
                print(f"  - {failure}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
