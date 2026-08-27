#!/usr/bin/env python3
"""Inspect an OpenPCDet runtime without running dataset jobs or model training.

The script is intentionally self-contained for the generated repo skill. It can
be run against either an installed `pcdet` package or an OpenPCDet checkout
passed with `--repo`.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path
from typing import Any

CORE_MODULES = [
    "pcdet",
    "pcdet.config",
    "pcdet.models",
    "pcdet.datasets",
]

CUDA_EXTENSION_MODULES = [
    "pcdet.ops.iou3d_nms.iou3d_nms_cuda",
    "pcdet.ops.roiaware_pool3d.roiaware_pool3d_cuda",
    "pcdet.ops.roipoint_pool3d.roipoint_pool3d_cuda",
    "pcdet.ops.pointnet2.pointnet2_stack.pointnet2_stack_cuda",
    "pcdet.ops.pointnet2.pointnet2_batch.pointnet2_batch_cuda",
    "pcdet.ops.bev_pool.bev_pool_ext",
    "pcdet.ops.ingroup_inds.ingroup_inds_cuda",
]

OPTIONAL_MODULES = [
    "spconv",
    "cumm",
    "kornia",
    "av2",
    "open3d",
    "mayavi",
]

DIST_NAMES = [
    "pcdet",
    "torch",
    "torchvision",
    "spconv-cu120",
    "spconv-cu121",
    "spconv-cu124",
    "cumm-cu120",
    "cumm-cu121",
    "cumm-cu124",
    "kornia",
    "numpy",
    "numba",
    "llvmlite",
    "SharedArray",
    "opencv-python",
]


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"module": module_name, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"module": module_name, "ok": True, "version": getattr(module, "__version__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect OpenPCDet import/runtime readiness")
    parser.add_argument("--repo", type=Path, default=None, help="Optional OpenPCDet checkout to prepend to sys.path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--require-cuda-ops",
        action="store_true",
        help="Return non-zero when any compiled OpenPCDet CUDA extension import fails",
    )
    args = parser.parse_args()

    if args.repo is not None:
        repo = args.repo.resolve()
        if not (repo / "pcdet").is_dir():
            raise SystemExit(f"--repo does not look like an OpenPCDet checkout: {args.repo}")
        sys.path.insert(0, str(repo))
        tools_dir = repo / "tools"
        if tools_dir.is_dir():
            sys.path.insert(0, str(tools_dir))

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable_basename": Path(sys.executable).name,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "distributions": {name: dist_version(name) for name in DIST_NAMES},
        "imports": {},
        "torch": {},
    }

    try:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "compiled_cuda": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "device_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if torch.cuda.is_available()
            else [],
        }
    except Exception as exc:  # noqa: BLE001
        report["torch"] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}

    for group, modules in [
        ("core", CORE_MODULES),
        ("cuda_extensions", CUDA_EXTENSION_MODULES),
        ("optional", OPTIONAL_MODULES),
    ]:
        report["imports"][group] = [import_status(module_name) for module_name in modules]

    failed_cuda_ops = [x for x in report["imports"]["cuda_extensions"] if not x["ok"]]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OpenPCDet runtime inspection")
        print(f"Python: {report['python']}")
        torch_report = report["torch"]
        print(
            "Torch: version={version} compiled_cuda={compiled_cuda} cuda_available={cuda_available} device_count={device_count}".format(
                version=torch_report.get("version"),
                compiled_cuda=torch_report.get("compiled_cuda"),
                cuda_available=torch_report.get("cuda_available"),
                device_count=torch_report.get("device_count"),
            )
        )
        for group, statuses in report["imports"].items():
            print(f"\n[{group}]")
            for status in statuses:
                if status["ok"]:
                    print(f"OK   {status['module']} {status.get('version') or ''}".rstrip())
                else:
                    print(f"FAIL {status['module']}: {status['error_type']}: {status['error']}")

    if args.require_cuda_ops and failed_cuda_ops:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
