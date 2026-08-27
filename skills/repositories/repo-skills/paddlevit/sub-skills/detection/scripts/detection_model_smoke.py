#!/usr/bin/env python3
"""Run a tiny, download-free Paddle detection contract smoke.

The models here are intentionally tiny synthetic stand-ins. They exercise the
shape conventions used by PaddleViT DETR and FPN/RPN-style detectors without
importing the source checkout, loading checkpoints, reading COCO, training, or
claiming benchmark equivalence. Use a source-root build for source compatibility.
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List


def _finite(paddle, tensor) -> bool:
    return bool(paddle.all(paddle.isfinite(tensor)).item())


def _xyxy_from_cxcywh(paddle, boxes):
    x, y, w, h = paddle.unbind(boxes, axis=-1)
    return paddle.stack([x - 0.5 * w, y - 0.5 * h, x + 0.5 * w, y + 0.5 * h], axis=-1)


def _run_detr(paddle, nn, functional, args) -> Dict[str, object]:
    class TinyDETR(nn.Layer):
        def __init__(self):
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2D(3, args.embed_dim, kernel_size=3, stride=4, padding=1),
                nn.ReLU(),
            )
            self.queries = nn.Embedding(args.queries, args.embed_dim)
            self.class_head = nn.Linear(args.embed_dim, args.num_classes + 1)
            self.box_head = nn.Sequential(nn.Linear(args.embed_dim, args.embed_dim), nn.ReLU(), nn.Linear(args.embed_dim, 4))

        def forward(self, image):
            feature = self.stem(image)
            context = paddle.mean(feature, axis=[2, 3], keepdim=True)
            query = self.queries.weight.unsqueeze(0).expand([image.shape[0], args.queries, args.embed_dim])
            query = query + context.reshape([image.shape[0], 1, args.embed_dim])
            return {"pred_logits": self.class_head(query), "pred_boxes": functional.sigmoid(self.box_head(query))}

    model = TinyDETR()
    model.eval()
    image = paddle.randn([args.batch_size, 3, args.height, args.width])
    output = model(image)
    logits, boxes = output["pred_logits"], output["pred_boxes"]
    expected_logits = [args.batch_size, args.queries, args.num_classes + 1]
    expected_boxes = [args.batch_size, args.queries, 4]
    if list(logits.shape) != expected_logits or list(boxes.shape) != expected_boxes:
        raise AssertionError(f"DETR contract mismatch: logits={logits.shape}, boxes={boxes.shape}")
    xyxy = _xyxy_from_cxcywh(paddle, boxes)
    scale = paddle.to_tensor([args.width, args.height, args.width, args.height], dtype="float32")
    absolute = xyxy * scale
    scores = paddle.max(functional.softmax(logits, axis=-1)[:, :, :-1], axis=-1)
    # A finite no-backward loss sanity check, not the source SetCriterion.
    synthetic_loss = paddle.mean(paddle.abs(boxes - 0.5)) + paddle.mean(-paddle.log(paddle.clip(scores, min=1e-6)))
    if not all(_finite(paddle, value) for value in (logits, boxes, absolute, synthetic_loss)):
        raise AssertionError("DETR synthetic output contains non-finite values")
    return {"model": "detr", "input": list(image.shape), "pred_logits": list(logits.shape), "pred_boxes": list(boxes.shape), "post_boxes": list(absolute.shape), "finite": True}


def _run_anchor_family(paddle, nn, functional, args, model_name: str) -> Dict[str, object]:
    class TinyPyramid(nn.Layer):
        def __init__(self):
            super().__init__()
            channels = [16, 24, 32, 40]
            layers = []
            in_channels = 3
            for channels_out in channels:
                layers.append(nn.Sequential(nn.Conv2D(in_channels, channels_out, 3, stride=2, padding=1), nn.ReLU()))
                in_channels = channels_out
            self.layers = nn.LayerList(layers)

        def forward(self, image):
            features = []
            current = image
            for layer in self.layers:
                current = layer(current)
                features.append(current)
            return features

    class TinyAnchorDetector(nn.Layer):
        def __init__(self):
            super().__init__()
            channels = [16, 24, 32, 40]
            self.cls = nn.LayerList([nn.Conv2D(c, 3 * args.num_classes, 3, padding=1) for c in channels])
            self.box = nn.LayerList([nn.Conv2D(c, 3 * 4, 3, padding=1) for c in channels])
            self.backbone = TinyPyramid()

        def forward(self, image):
            levels = self.backbone(image)
            scores, boxes = [], []
            for feature, cls_head, box_head in zip(levels, self.cls, self.box):
                batch, _, height, width = feature.shape
                cls_value = cls_head(feature).reshape([batch, 3, args.num_classes, height, width]).transpose([0, 3, 4, 1, 2])
                box_value = box_head(feature).reshape([batch, 3, 4, height, width]).transpose([0, 3, 4, 1, 2])
                scores.append(cls_value.reshape([batch, -1, args.num_classes]))
                boxes.append(box_value.reshape([batch, -1, 4]))
            return scores, boxes

    model = TinyAnchorDetector()
    model.eval()
    image = paddle.randn([args.batch_size, 3, args.height, args.width])
    score_levels, box_levels = model(image)
    if len(score_levels) != 4 or len(box_levels) != 4:
        raise AssertionError(f"{model_name} did not produce four pyramid levels")
    total = 0
    finite_values = []
    losses = []
    for scores, boxes in zip(score_levels, box_levels):
        if scores.shape[0] != args.batch_size or scores.shape[2] != args.num_classes or boxes.shape[2] != 4:
            raise AssertionError(f"{model_name} level shape mismatch: {scores.shape}, {boxes.shape}")
        total += int(scores.shape[1])
        finite_values.extend([scores, boxes])
        losses.append(paddle.mean(paddle.abs(boxes)) + paddle.mean(functional.sigmoid(scores)))
    if not all(_finite(paddle, value) for value in finite_values + losses):
        raise AssertionError(f"{model_name} synthetic pyramid output contains non-finite values")
    return {"model": model_name, "input": list(image.shape), "levels": [list(item.shape) for item in score_levels], "boxes": [list(item.shape) for item in box_levels], "anchors_before_nms": total, "finite": True}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Paddle detection shape smoke; no downloads, checkpoints, COCO, or training.")
    parser.add_argument("--model", choices=("detr", "swin", "pvtv2", "all"), default="all", help="synthetic contract to check (default: all)")
    parser.add_argument("--device", default="cpu", help="Paddle device, e.g. cpu, gpu:0, or auto (default: cpu)")
    parser.add_argument("--batch-size", type=int, default=1, help="synthetic batch size (default: 1)")
    parser.add_argument("--height", type=int, default=64, help="synthetic image height; use a multiple of 32 for FPN checks")
    parser.add_argument("--width", type=int, default=64, help="synthetic image width; use a multiple of 32 for FPN checks")
    parser.add_argument("--num-classes", type=int, default=3, help="synthetic foreground class count")
    parser.add_argument("--queries", type=int, default=5, help="synthetic DETR query count")
    parser.add_argument("--embed-dim", type=int, default=16, help="synthetic DETR embedding width")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if min(args.batch_size, args.height, args.width, args.num_classes, args.queries, args.embed_dim) <= 0:
        raise SystemExit("all size and count arguments must be positive")
    try:
        import paddle
        import paddle.nn as nn
        import paddle.nn.functional as functional
    except ImportError as exc:
        print(f"SKIP: Paddle is not importable: {exc}")
        return 2
    device = args.device
    if device == "auto":
        device = "gpu:0" if paddle.is_compiled_with_cuda() else "cpu"
    try:
        paddle.set_device(device)
    except Exception as exc:
        print(f"ERROR: cannot select Paddle device {device!r}: {exc}")
        return 1
    if args.height % 32 or args.width % 32:
        print("warning: height/width are not multiples of 32; source Swin/PVTv2 collate pads to divisibility 32")
    selected = ("detr", "swin", "pvtv2") if args.model == "all" else (args.model,)
    report: List[Dict[str, object]] = []
    with paddle.no_grad():
        for model_name in selected:
            if model_name == "detr":
                report.append(_run_detr(paddle, nn, functional, args))
            else:
                report.append(_run_anchor_family(paddle, nn, functional, args, model_name))
    result = {"ok": True, "device": paddle.get_device(), "checks": report, "note": "synthetic shape smoke; not source-model or benchmark verification"}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"OK: synthetic detection smoke on {result['device']}")
        for item in report:
            print(f"  {item['model']}: finite={item['finite']} input={item['input']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
