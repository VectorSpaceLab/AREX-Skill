#!/usr/bin/env python3
"""Deterministic smoke checks for TorchMetrics vision and detection metrics."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def to_python(value: Any) -> Any:
    import torch

    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.numel() == 1:
            return value.item()
        return value.tolist()
    if isinstance(value, dict):
        return {key: to_python(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_python(val) for val in value]
    return value


def select_device(requested: str):
    import torch

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested, but torch.cuda.is_available() is False.")
        return torch.device("cuda")
    return torch.device("cpu")


def run_image_smoke(device) -> dict[str, Any]:
    import torch
    from torchmetrics.image import (
        MultiScaleStructuralSimilarityIndexMeasure,
        PeakSignalNoiseRatio,
        StructuralSimilarityIndexMeasure,
    )

    preds_small = torch.linspace(0.0, 1.0, steps=64 * 64, device=device, dtype=torch.float32).reshape(1, 1, 64, 64)
    target_small = (preds_small * 0.9).clamp(0.0, 1.0)
    preds_large = torch.linspace(0.0, 1.0, steps=192 * 192, device=device, dtype=torch.float32).reshape(1, 1, 192, 192)
    target_large = (preds_large * 0.9).clamp(0.0, 1.0)

    psnr = PeakSignalNoiseRatio(data_range=1.0).to(device)
    ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(device)
    ms_ssim = MultiScaleStructuralSimilarityIndexMeasure(data_range=1.0).to(device)

    psnr_value = psnr(preds_small, target_small)
    ssim_value = ssim(preds_small, target_small)
    ms_ssim_value = ms_ssim(preds_large, target_large)

    if not torch.isfinite(psnr_value):
        raise RuntimeError(f"PSNR smoke failed with value {psnr_value}")
    if not torch.isfinite(ssim_value):
        raise RuntimeError(f"SSIM smoke failed with value {ssim_value}")
    if not torch.isfinite(ms_ssim_value):
        raise RuntimeError(f"MS-SSIM smoke failed with value {ms_ssim_value}")

    return {
        "psnr": psnr_value,
        "ssim": ssim_value,
        "ms_ssim": ms_ssim_value,
    }


def run_segmentation_smoke(device) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F
    from torchmetrics.segmentation import DiceScore, HausdorffDistance, MeanIoU

    index_target = torch.tensor([[[0, 1], [2, 1]]], device=device, dtype=torch.long)
    target_one_hot = F.one_hot(index_target, num_classes=3).movedim(-1, 1).to(torch.bool)

    dice = DiceScore(num_classes=3, include_background=False, average="none", input_format="one-hot").to(device)
    miou = MeanIoU(num_classes=3, include_background=False, per_class=True, input_format="index").to(device)
    hausdorff = HausdorffDistance(
        num_classes=3,
        include_background=False,
        input_format="index",
        spacing=[1.0, 1.5],
        directed=True,
    ).to(device)

    dice_value = dice(target_one_hot, target_one_hot)
    miou_value = miou(index_target, index_target)
    hausdorff_value = hausdorff(index_target, index_target)

    if dice_value.shape != torch.Size([2]):
        raise RuntimeError(f"Dice smoke returned the wrong shape: {dice_value.shape}")
    if not torch.allclose(dice_value, torch.ones_like(dice_value)):
        raise RuntimeError(f"Dice smoke expected ones but got {dice_value}")
    if miou_value.shape != torch.Size([2]):
        raise RuntimeError(f"MeanIoU smoke returned the wrong shape: {miou_value.shape}")
    if not torch.allclose(miou_value, torch.ones_like(miou_value)):
        raise RuntimeError(f"MeanIoU smoke expected ones but got {miou_value}")
    if not torch.isclose(hausdorff_value, torch.zeros_like(hausdorff_value)).all():
        raise RuntimeError(f"Hausdorff smoke expected zero but got {hausdorff_value}")

    return {
        "dice": dice_value,
        "mean_iou": miou_value,
        "hausdorff_distance": hausdorff_value,
    }


def run_detection_smoke(device, backend: str) -> dict[str, Any]:
    import torch
    from torchmetrics.detection import IntersectionOverUnion, MeanAveragePrecision

    boxes = torch.tensor([[1.0, 1.0, 3.0, 3.0]], device=device, dtype=torch.float32)
    labels = torch.tensor([0], device=device, dtype=torch.long)
    scores = torch.tensor([0.9], device=device, dtype=torch.float32)
    mask = torch.tensor(
        [[[0, 0, 0, 0],
          [0, 1, 1, 0],
          [0, 1, 1, 0],
          [0, 0, 0, 0]]],
        device=device,
        dtype=torch.bool,
    )

    preds = [dict(boxes=boxes, scores=scores, labels=labels, masks=mask)]
    target = [dict(boxes=boxes.clone(), labels=labels.clone(), masks=mask.clone())]

    iou = IntersectionOverUnion(box_format="xyxy", class_metrics=True).to(device)
    iou_value = iou(preds, target)
    if not torch.isclose(iou_value["iou"], torch.tensor(1.0, device=device), atol=1e-6):
        raise RuntimeError(f"IoU smoke expected 1.0 but got {iou_value}")
    if not torch.isclose(iou_value["iou/cl_0"], torch.tensor(1.0, device=device), atol=1e-6):
        raise RuntimeError(f"Class-wise IoU smoke expected 1.0 but got {iou_value}")

    backend_candidates = [backend]
    if backend == "pycocotools":
        backend_candidates.append("faster_coco_eval")
    elif backend == "faster_coco_eval":
        backend_candidates.append("pycocotools")

    map_result: dict[str, Any] = {"status": "skipped", "reason": "no supported mAP backend available"}
    last_error: ModuleNotFoundError | None = None
    for candidate in backend_candidates:
        try:
            map_metric = MeanAveragePrecision(
                box_format="xyxy",
                iou_type=("bbox", "segm"),
                backend=candidate,
            ).to(device)
            map_value = map_metric(preds, target)
            for key in ("bbox_map", "segm_map"):
                if key not in map_value:
                    raise RuntimeError(f"MeanAveragePrecision smoke missing key {key}: {map_value}")
                if not torch.isfinite(map_value[key]):
                    raise RuntimeError(f"MeanAveragePrecision smoke failed for key {key}: {map_value[key]}")
                if map_value[key] < 0.99:
                    raise RuntimeError(
                        f"MeanAveragePrecision smoke expected near-perfect score for {key}: {map_value[key]}"
                    )
            classes = map_value.get("classes")
            if classes is not None and classes.numel() != 1:
                raise RuntimeError(f"MeanAveragePrecision smoke expected one class but got {classes}")
            map_result = {"status": "passed", "backend": candidate, "value": map_value}
            break
        except ModuleNotFoundError as exc:
            last_error = exc
            continue

    if map_result["status"] == "skipped" and last_error is not None:
        map_result["reason"] = str(last_error)

    return {
        "iou": iou_value,
        "map": map_result,
    }


def run_panoptic_smoke(device) -> dict[str, Any]:
    import torch
    from torchmetrics.detection import PanopticQuality

    preds = torch.tensor([[[[0, 1], [0, 1]], [[1, 0], [1, 0]]]], device=device, dtype=torch.long)
    metric = PanopticQuality(things={0}, stuffs={1}).to(device)
    value = metric(preds, preds.clone())
    if not torch.isfinite(value):
        raise RuntimeError(f"PanopticQuality smoke failed with value {value}")
    return {"panoptic_quality": value}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu", help="Run the smoke on this device.")
    parser.add_argument(
        "--backend",
        choices=("pycocotools", "faster_coco_eval"),
        default="pycocotools",
        help="COCO backend to use for MeanAveragePrecision.",
    )
    parser.add_argument(
        "--include-panoptic",
        action="store_true",
        help="Also run a tiny PanopticQuality smoke.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        import torchmetrics
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        device = select_device(args.device)
        summary: dict[str, Any] = {
            "device": str(device),
            "backend": args.backend,
            "image": to_python(run_image_smoke(device)),
            "segmentation": to_python(run_segmentation_smoke(device)),
            "detection": to_python(run_detection_smoke(device, args.backend)),
        }
        if args.include_panoptic:
            summary["panoptic"] = to_python(run_panoptic_smoke(device))
    except Exception as exc:  # pragma: no cover - user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    summary["torchmetrics_version"] = getattr(torchmetrics, "__version__", "unknown")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
