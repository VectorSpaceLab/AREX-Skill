#!/usr/bin/env python3
"""Smoke-check an AdelaiDet installation.

Run from the generated skill directory after installing AdelaiDet and Detectron2.
Use --cuda-ops for workflows that require the compiled CUDA extension.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from typing import Any, Callable


def record(results: dict[str, Any], name: str, fn: Callable[[], Any]) -> None:
    try:
        results[name] = {"ok": True, "value": fn()}
    except Exception as exc:  # pragma: no cover - diagnostic tool
        results[name] = {
            "ok": False,
            "error": repr(exc),
            "traceback": traceback.format_exc(limit=8),
        }


def torch_probe() -> dict[str, Any]:
    import torch

    info: dict[str, Any] = {
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available():
        info["device0"] = torch.cuda.get_device_name(0)
        info["capability0"] = list(torch.cuda.get_device_capability(0))
    return info


def config_probe() -> dict[str, Any]:
    from adet.config import get_cfg

    cfg = get_cfg()
    return {
        "FCOS": hasattr(cfg.MODEL, "FCOS"),
        "BATEXT": hasattr(cfg.MODEL, "BATEXT"),
        "BLENDMASK": hasattr(cfg.MODEL, "BLENDMASK"),
        "CONDINST": hasattr(cfg.MODEL, "CONDINST"),
        "SOLOV2": hasattr(cfg.MODEL, "SOLOV2"),
        "FCPOSE": hasattr(cfg.MODEL, "FCPOSE"),
        "fcos_num_classes": cfg.MODEL.FCOS.NUM_CLASSES,
    }


def registry_probe() -> dict[str, Any]:
    import adet.modeling  # noqa: F401 - registration side effects
    from detectron2.modeling import BACKBONE_REGISTRY, META_ARCH_REGISTRY
    from detectron2.modeling.roi_heads import ROI_HEADS_REGISTRY

    return {
        "meta_arch": [
            name
            for name in ["OneStageDetector", "BlendMask", "SOLOv2"]
            if name in META_ARCH_REGISTRY
        ],
        "backbone": [
            name
            for name in ["build_fcos_resnet_fpn_backbone", "build_vovnet_fpn_backbone"]
            if name in BACKBONE_REGISTRY
        ],
        "roi_heads": [name for name in ["TextHead"] if name in ROI_HEADS_REGISTRY],
    }


def extension_probe() -> list[str]:
    ext = importlib.import_module("adet._C")
    return sorted(name for name in dir(ext) if not name.startswith("_"))


def cuda_op_probe() -> dict[str, Any]:
    import torch
    from adet import _C
    from adet.layers import BezierAlign, DefROIAlign

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available; omit --cuda-ops for import-only checks")

    x = torch.arange(0, 16, dtype=torch.float32, device="cuda").view(1, 1, 4, 4)
    bezier_rois = torch.tensor(
        [[0, 0, 0, 1, 0, 2, 0, 3, 0, 0, 3, 1, 3, 2, 3, 3, 3]],
        dtype=torch.float32,
        device="cuda",
    )
    bezier = BezierAlign((2, 2), spatial_scale=1.0, sampling_ratio=1, aligned=True)(
        x, bezier_rois
    )

    def_rois = torch.tensor([[0, 0, 0, 3, 3]], dtype=torch.float32, device="cuda")
    offsets = torch.zeros((1, 2, 2, 2), dtype=torch.float32, device="cuda")
    def_roi = DefROIAlign(
        (2, 2), spatial_scale=1.0, sampling_ratio=1, trans_std=0.1, aligned=True
    )(x, def_rois, offsets)

    boxes = torch.tensor(
        [[0.0, 0.0, 10.0, 10.0], [1.0, 1.0, 9.0, 9.0], [20.0, 20.0, 30.0, 30.0]],
        device="cuda",
    )
    scores = torch.tensor([0.9, 0.8, 0.7], device="cuda")
    labels = torch.tensor([1.0, 1.0, 2.0], device="cuda")
    keep = _C.ml_nms(boxes, scores, labels, 0.5)

    return {
        "bezier_shape": list(bezier.shape),
        "bezier_sum": float(bezier.detach().cpu().sum()),
        "def_roi_shape": list(def_roi.shape),
        "def_roi_sum": float(def_roi.detach().cpu().sum()),
        "ml_nms_keep": keep.cpu().tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check AdelaiDet installation")
    parser.add_argument("--cuda-ops", action="store_true", help="Run tiny CUDA custom-op checks")
    parser.add_argument("--json", action="store_true", help="Print compact JSON only")
    args = parser.parse_args()

    results: dict[str, Any] = {}
    record(results, "torch", torch_probe)
    record(results, "detectron2", lambda: {"version": importlib.import_module("detectron2").__version__})
    record(results, "adet", lambda: {"version": getattr(importlib.import_module("adet"), "__version__", None)})
    record(results, "config", config_probe)
    record(results, "registries", registry_probe)
    record(results, "extension", extension_probe)
    if args.cuda_ops:
        record(results, "cuda_ops", cuda_op_probe)

    if args.json:
        print(json.dumps(results, sort_keys=True))
    else:
        print(json.dumps(results, indent=2, sort_keys=True))

    failed = [name for name, item in results.items() if not item.get("ok")]
    if failed:
        print(f"FAILED checks: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
