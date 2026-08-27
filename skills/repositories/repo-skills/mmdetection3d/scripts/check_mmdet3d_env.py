#!/usr/bin/env python3
"""Check a MMDetection3D runtime without running models.

This helper imports public packages, reports versions, probes CUDA and optional
sparse backends, and optionally checks selected API signatures. It is safe by
default: it performs no downloads, training, inference, dataset conversion, or
writes beyond stdout.

Example:
  python check_mmdet3d_env.py --json
  python check_mmdet3d_env.py --require-cuda --check-apis
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any, Dict


def import_info(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def torch_info(require_cuda: bool) -> Dict[str, Any]:
    info = import_info("torch")
    if not info["ok"]:
        return info
    import torch  # type: ignore

    info.update(
        {
            "cuda_compiled": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    if require_cuda and not info["cuda_available"]:
        info["error"] = "CUDA was required but torch.cuda.is_available() is false"
    if require_cuda and info.get("cuda_available"):
        try:
            value = torch.tensor([1.0], device="cuda").cpu().item()
            info["cuda_tensor_smoke"] = value == 1.0
        except Exception as exc:  # pragma: no cover - hardware diagnostic path
            info["cuda_tensor_smoke"] = False
            info["error"] = f"CUDA tensor smoke failed: {type(exc).__name__}: {exc}"
    return info


def api_signatures() -> Dict[str, str]:
    from mmdet3d.apis import (  # type: ignore
        LidarDet3DInferencer,
        inference_detector,
        inference_mono_3d_detector,
        inference_multi_modality_detector,
        inference_segmentor,
        init_model,
    )
    from mmdet3d.structures import (  # type: ignore
        Box3DMode,
        CameraInstance3DBoxes,
        Coord3DMode,
        DepthInstance3DBoxes,
        LiDARInstance3DBoxes,
        points_cam2img,
    )

    objects = {
        "mmdet3d.apis.init_model": init_model,
        "mmdet3d.apis.inference_detector": inference_detector,
        "mmdet3d.apis.inference_mono_3d_detector": inference_mono_3d_detector,
        "mmdet3d.apis.inference_multi_modality_detector": inference_multi_modality_detector,
        "mmdet3d.apis.inference_segmentor": inference_segmentor,
        "mmdet3d.apis.LidarDet3DInferencer.__init__": LidarDet3DInferencer.__init__,
        "mmdet3d.structures.LiDARInstance3DBoxes": LiDARInstance3DBoxes,
        "mmdet3d.structures.CameraInstance3DBoxes": CameraInstance3DBoxes,
        "mmdet3d.structures.DepthInstance3DBoxes": DepthInstance3DBoxes,
        "mmdet3d.structures.points_cam2img": points_cam2img,
        "mmdet3d.structures.Box3DMode.convert": Box3DMode.convert,
        "mmdet3d.structures.Coord3DMode.convert_point": Coord3DMode.convert_point,
    }
    return {name: str(inspect.signature(obj)) for name, obj in objects.items()}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "packages": {
            name: import_info(name)
            for name in ["mmdet3d", "mmcv", "mmengine", "mmdet", "numpy", "numba", "open3d"]
        },
        "torch": torch_info(args.require_cuda),
        "optional_backends": {
            "spconv": import_info("spconv"),
            "MinkowskiEngine": import_info("MinkowskiEngine"),
            "torchsparse": import_info("torchsparse"),
        },
    }
    if args.check_apis:
        try:
            report["api_signatures"] = api_signatures()
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["api_signature_error"] = f"{type(exc).__name__}: {exc}"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MMDetection3D import/backend readiness without running models.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is not available to PyTorch.")
    parser.add_argument("--check-apis", action="store_true", help="Inspect key mmdet3d API signatures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = build_report(args)
    failures = []
    for pkg in ["mmdet3d", "mmcv", "mmengine", "mmdet"]:
        if not report["packages"][pkg]["ok"]:
            failures.append(f"missing {pkg}: {report['packages'][pkg].get('error')}")
    if report["torch"].get("error"):
        failures.append(report["torch"]["error"])
    if report.get("api_signature_error"):
        failures.append(report["api_signature_error"])

    report["status"] = "ok" if not failures else "failed"
    report["failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"python: {report['python']}")
        for name, info in report["packages"].items():
            print(f"{name}: {'ok' if info['ok'] else 'missing'} {info.get('version') or info.get('error') or ''}")
        torch = report["torch"]
        print(
            "torch: {state} version={version} cuda_compiled={cuda} cuda_available={available} devices={devices}".format(
                state="ok" if torch.get("ok") else "missing",
                version=torch.get("version"),
                cuda=torch.get("cuda_compiled"),
                available=torch.get("cuda_available"),
                devices=torch.get("cuda_device_count"),
            )
        )
        for name, info in report["optional_backends"].items():
            print(f"optional {name}: {'ok' if info['ok'] else 'missing'} {info.get('version') or info.get('error') or ''}")
        if failures:
            print("failures:")
            for failure in failures:
                print(f"- {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
