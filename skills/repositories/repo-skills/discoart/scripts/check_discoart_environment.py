#!/usr/bin/env python3
"""Safely check a DiscoArt runtime without running diffusion.

Examples:
  python scripts/check_discoart_environment.py
  python scripts/check_discoart_environment.py --check-cuda
  python scripts/check_discoart_environment.py --check-cuda --allocate-cuda --json

The script imports DiscoArt with remote model lookup disabled, loads the packaged
configuration, and optionally probes torch CUDA visibility. It never calls
`discoart.create()`, downloads models, opens ports, or writes output images.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from importlib import metadata
from typing import Any, Dict


@contextlib.contextmanager
def _disable_urlopen_for_import():
    """Avoid DiscoArt import-time network checks in offline diagnostics."""

    try:
        import urllib.request as request
    except Exception:
        yield
        return

    original_urlopen = request.urlopen

    def blocked_urlopen(*args: Any, **kwargs: Any):  # pragma: no cover - tiny guard
        raise TimeoutError("network disabled by check_discoart_environment.py")

    request.urlopen = blocked_urlopen
    try:
        yield
    finally:
        request.urlopen = original_urlopen


def _metadata_version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _check_imports() -> Dict[str, Any]:
    os.environ.setdefault("DISCOART_DISABLE_REMOTE_MODELS", "1")
    os.environ.setdefault("DISCOART_DISABLE_IPYTHON", "1")

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "packages": {},
        "imports": {},
        "config": {},
        "warnings": [],
        "errors": [],
    }

    for dist in [
        "discoart",
        "docarray",
        "jina",
        "torch",
        "torchvision",
        "open-clip-torch",
        "openai-clip",
        "lpips",
        "guided-diffusion-sdk",
        "resize-right-sdk",
        "setuptools",
    ]:
        report["packages"][dist] = _metadata_version(dist)

    try:
        with _disable_urlopen_for_import():
            import discoart
        report["imports"]["discoart"] = "ok"
        report["discoart_version"] = getattr(discoart, "__version__", None)
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["imports"]["discoart"] = "failed"
        report["errors"].append(f"import discoart failed: {type(exc).__name__}: {exc}")
        return report

    try:
        from discoart.config import default_args, load_config

        cfg = load_config({"steps": 1, "n_batches": 1, "width_height": [64, 64]})
        report["config"] = {
            "default_key_count": len(default_args),
            "sample_steps": cfg.get("steps"),
            "sample_n_batches": cfg.get("n_batches"),
            "sample_width_height": cfg.get("width_height"),
            "sample_name_docarray_prefix": str(cfg.get("name_docarray", ""))[:40],
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["errors"].append(f"config smoke failed: {type(exc).__name__}: {exc}")

    if report["packages"].get("setuptools"):
        try:
            import pkg_resources  # noqa: F401
            report["imports"]["pkg_resources"] = "ok"
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["imports"]["pkg_resources"] = "failed"
            report["warnings"].append(
                "DiscoArt imports pkg_resources; pin setuptools<81 if this import is missing."
            )
            report["errors"].append(f"pkg_resources failed: {type(exc).__name__}: {exc}")

    return report


def _check_cuda(allocate: bool) -> Dict[str, Any]:
    cuda: Dict[str, Any] = {"checked": True}
    try:
        import torch

        cuda["torch_version"] = getattr(torch, "__version__", None)
        cuda["torch_cuda_runtime"] = getattr(torch.version, "cuda", None)
        cuda["available"] = bool(torch.cuda.is_available())
        cuda["device_count"] = int(torch.cuda.device_count())
        if cuda["available"]:
            cuda["device0_name"] = torch.cuda.get_device_name(0)
            cuda["device0_capability"] = list(torch.cuda.get_device_capability(0))
            if allocate:
                tensor = torch.empty((1,), device="cuda")
                cuda["allocation"] = f"ok:{tensor.device}:{tensor.numel()}"
        elif allocate:
            cuda["allocation"] = "skipped:no-cuda"
    except Exception as exc:  # pragma: no cover - diagnostic path
        cuda["available"] = False
        cuda["error"] = f"{type(exc).__name__}: {exc}"
    return cuda


def _print_text(report: Dict[str, Any]) -> None:
    print("DiscoArt environment check")
    print(f"Python: {report.get('python')}")
    print(f"DiscoArt import: {report.get('imports', {}).get('discoart')}")
    print(f"DiscoArt version: {report.get('discoart_version')}")
    print("\nPackage versions:")
    for name, version in sorted(report.get("packages", {}).items()):
        print(f"  {name}: {version or 'not installed'}")
    if report.get("config"):
        print("\nConfig smoke:")
        for key, value in report["config"].items():
            print(f"  {key}: {value}")
    if "cuda" in report:
        print("\nCUDA smoke:")
        for key, value in report["cuda"].items():
            print(f"  {key}: {value}")
    if report.get("warnings"):
        print("\nWarnings:")
        for item in report["warnings"]:
            print(f"  - {item}")
    if report.get("errors"):
        print("\nErrors:")
        for item in report["errors"]:
            print(f"  - {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely check a DiscoArt runtime without running diffusion.")
    parser.add_argument("--check-cuda", action="store_true", help="Probe torch CUDA availability.")
    parser.add_argument(
        "--allocate-cuda",
        action="store_true",
        help="Allocate a one-element CUDA tensor. Implies --check-cuda.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    report = _check_imports()
    if args.check_cuda or args.allocate_cuda:
        report["cuda"] = _check_cuda(allocate=args.allocate_cuda)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_text(report)

    return 0 if not report.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
