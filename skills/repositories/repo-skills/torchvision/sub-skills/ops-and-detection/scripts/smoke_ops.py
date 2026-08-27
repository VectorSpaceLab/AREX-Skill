#!/usr/bin/env python3
"""Tiny offline smoke check for torchvision.ops."""

from __future__ import annotations

import json
import sys
import traceback


MISSING_OP_MARKERS = (
    "torchvision::nms",
    "Couldn't load custom C++ ops",
    "custom C++ ops",
    "does not exist",
    "not available for",
)


def is_missing_ops_error(message: str) -> bool:
    return any(marker in message for marker in MISSING_OP_MARKERS)


def main() -> int:
    try:
        import torch
        import torchvision
        from torchvision import extension, ops
    except Exception as exc:  # pragma: no cover - diagnostic path
        message = str(exc)
        status = "missing-ops" if is_missing_ops_error(message) else "failed"
        print(json.dumps({"status": status, "stage": "import", "error": repr(exc)}, indent=2))
        if status == "missing-ops":
            return 2
        traceback.print_exc()
        return 1

    result: dict[str, object] = {
        "status": "ok",
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "has_ops": bool(extension._has_ops()),
    }

    try:
        boxes_xywh = torch.tensor(
            [
                [0.0, 0.0, 10.0, 10.0],
                [1.0, 1.0, 10.0, 10.0],
                [20.0, 20.0, 5.0, 5.0],
            ],
            dtype=torch.float32,
        )
        boxes = ops.box_convert(boxes_xywh, in_fmt="xywh", out_fmt="xyxy")
        if not torch.all(boxes[:, 2:] >= boxes[:, :2]):
            raise RuntimeError("box conversion produced invalid xyxy coordinates")

        scores = torch.tensor([0.9, 0.8, 0.7], dtype=torch.float32)
        labels = torch.tensor([1, 1, 2], dtype=torch.int64)
        iou = ops.box_iou(boxes, boxes)
        keep = ops.batched_nms(boxes, scores, labels, iou_threshold=0.5)

        feature = torch.arange(1 * 1 * 8 * 8, dtype=torch.float32).reshape(1, 1, 8, 8)
        rois = [torch.tensor([[1.0, 1.0, 6.0, 6.0]], dtype=torch.float32)]
        pooled = ops.roi_align(feature, rois, output_size=(2, 2), spatial_scale=1.0, sampling_ratio=-1)

        result.update(
            {
                "boxes_shape": list(boxes.shape),
                "iou_shape": list(iou.shape),
                "nms_keep": keep.tolist(),
                "roi_align_shape": list(pooled.shape),
            }
        )
        print(json.dumps(result, indent=2))
        return 0
    except (RuntimeError, NotImplementedError) as exc:
        message = str(exc)
        if is_missing_ops_error(message):
            result.update({"status": "missing-ops", "error": message})
            print(json.dumps(result, indent=2))
            return 2
        result.update({"status": "failed", "error": message})
        print(json.dumps(result, indent=2))
        traceback.print_exc()
        return 1
    except Exception as exc:  # pragma: no cover - diagnostic path
        result.update({"status": "failed", "error": repr(exc)})
        print(json.dumps(result, indent=2))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
