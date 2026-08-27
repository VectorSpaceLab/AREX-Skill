#!/usr/bin/env python3
"""Check that an environment can use the PerceptualSimilarity/LPIPS package.

This script is read-only: it imports packages, inspects signatures, checks
optional backend state, and verifies that bundled skill examples are present.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.resources as resources
import inspect
import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def build_report(require_cuda: bool = False) -> dict:
    report: dict = {"ok": True, "errors": [], "warnings": []}

    try:
        import torch
        import torchvision
        import lpips
        from lpips.lpips import LPIPS
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["ok"] = False
        report["errors"].append(f"import failed: {type(exc).__name__}: {exc}")
        return report

    try:
        lpips_version = metadata.version("lpips")
    except metadata.PackageNotFoundError:
        lpips_version = None
        report["warnings"].append("lpips distribution metadata was not found")

    cuda_available = bool(torch.cuda.is_available())
    report.update(
        {
            "lpips_version": lpips_version,
            "lpips_module": getattr(lpips, "__file__", None),
            "torch_version": getattr(torch, "__version__", None),
            "torchvision_version": getattr(torchvision, "__version__", None),
            "cuda_available": cuda_available,
            "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
            "lpips_signature": str(inspect.signature(LPIPS)),
        }
    )

    if require_cuda and not cuda_available:
        report["ok"] = False
        report["errors"].append("CUDA was required but torch.cuda.is_available() is false")

    try:
        weights_path = resources.files("lpips").joinpath("weights", "v0.1", "alex.pth")
        report["packaged_weight_v0_1_alex"] = bool(weights_path.is_file())
    except Exception as exc:
        report["warnings"].append(f"could not inspect packaged LPIPS weights: {exc}")

    try:
        from skimage.metrics import structural_similarity as _modern_ssim  # noqa: F401
        report["modern_ssim_available"] = True
    except Exception as exc:
        report["modern_ssim_available"] = False
        report["warnings"].append(f"modern SSIM import failed: {exc}")

    try:
        from skimage.measure import compare_ssim as _legacy_ssim  # noqa: F401
        report["legacy_compare_ssim_available"] = True
    except Exception:
        report["legacy_compare_ssim_available"] = False
        report["warnings"].append("legacy skimage.measure.compare_ssim is unavailable; use bundled modern SSIM helpers")

    examples = SKILL_ROOT / "assets" / "examples"
    report["bundled_examples_present"] = all(
        (examples / name).exists() for name in ["ex_ref.png", "ex_p0.png", "ex_p1.png", "ex_dir0", "ex_dir1", "ex_dir_pair"]
    )
    if not report["bundled_examples_present"]:
        report["warnings"].append("one or more bundled example assets are missing")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check LPIPS package import, metadata, backend, and bundled assets.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional checkout path to prepend to sys.path before importing lpips.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is not visible through torch.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        sys.path.insert(0, str(args.repo_root.resolve()))

    report = build_report(require_cuda=args.require_cuda)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "ok" if report.get("ok") else "failed"
        print(f"LPIPS environment check: {status}")
        for key in [
            "lpips_version",
            "torch_version",
            "torchvision_version",
            "cuda_available",
            "cuda_device_count",
            "packaged_weight_v0_1_alex",
            "modern_ssim_available",
            "legacy_compare_ssim_available",
            "bundled_examples_present",
        ]:
            if key in report:
                print(f"- {key}: {report[key]}")
        for warning in report.get("warnings", []):
            print(f"warning: {warning}")
        for error in report.get("errors", []):
            print(f"error: {error}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
