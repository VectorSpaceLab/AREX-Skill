#!/usr/bin/env python3
"""Check that VoxelMorph's current PyTorch API is importable and smoke-usable.

This script uses only tiny synthetic tensors. It does not download data, run real
training, read checkpoints, or write files unless the caller redirects stdout.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Sequence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run import, version, signature, and tiny CPU/GPU smoke checks for VoxelMorph.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--device", default="cpu", help="Torch device: cpu, cuda, or auto.")
    parser.add_argument("--skip-model-smoke", action="store_true", help="Only check imports and signatures.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser.parse_args(argv)


def _choose_device(torch, requested: str):
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is false")
    return device


def run(args: argparse.Namespace) -> dict:
    import neurite
    import torch
    import voxelmorph as vxm

    device = _choose_device(torch, args.device)
    report: dict = {
        "status": "pass",
        "voxelmorph_version": getattr(vxm, "__version__", None),
        "neurite_version": getattr(neurite, "__version__", None),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "device": str(device),
        "has_legacy_networks_attr": bool(hasattr(vxm, "networks")),
        "signatures": {
            "VxmPairwise": str(inspect.signature(vxm.nn.models.VxmPairwise)),
            "VxmPairwise.forward": str(inspect.signature(vxm.nn.models.VxmPairwise.forward)),
            "spatial_transform": str(inspect.signature(vxm.spatial_transform)),
            "load_volfile": str(inspect.signature(vxm.py.utils.load_volfile)),
            "scan_to_scan": str(inspect.signature(vxm.py.generators.scan_to_scan)),
        },
        "smokes": [],
    }

    if not args.skip_model_smoke:
        torch.manual_seed(5)
        spatial = (16, 16)
        source = torch.rand(1, 1, *spatial, device=device)
        target = torch.rand(1, 1, *spatial, device=device)
        model = vxm.nn.models.VxmPairwise(
            ndim=2,
            source_channels=1,
            target_channels=1,
            nb_features=(4, 4, 4),
            integration_steps=0,
            device=str(device),
        ).to(device)
        field, warped = model(source, target, return_warped_source=True)
        assert field.shape == (1, 2, *spatial)
        assert warped.shape == source.shape
        report["smokes"].append({"name": "VxmPairwise tiny forward", "status": "pass"})

        disp = vxm.affine_to_disp(vxm.params_to_affine(2, translation=(1, 0), device=device), shape=spatial)
        warped2 = vxm.spatial_transform(source, disp, non_spatial_dims=(0, 1))
        assert warped2.shape == source.shape
        report["smokes"].append({"name": "affine_to_disp + spatial_transform", "status": "pass"})

    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:  # noqa: BLE001 - keep CLI failure concise.
        print(f"FAIL check_voxelmorph_env: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "PASS check_voxelmorph_env",
            f"voxelmorph={report['voxelmorph_version']}",
            f"neurite={report['neurite_version']}",
            f"torch={report['torch_version']}",
            f"device={report['device']}",
            f"model_smoke={'skipped' if args.skip_model_smoke else 'passed'}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
