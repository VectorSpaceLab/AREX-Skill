# Vision Detection Workflows

These workflows show the smallest valid patterns for the most common vision and detection metrics in TorchMetrics.

## 1) Image quality quick check

Use explicit `data_range` for PSNR and SSIM-style metrics.

```python
import torch
from torchmetrics.image import (
    PeakSignalNoiseRatio,
    StructuralSimilarityIndexMeasure,
    MultiScaleStructuralSimilarityIndexMeasure,
)

preds = torch.linspace(0.0, 1.0, steps=64 * 64).reshape(1, 1, 64, 64)
target = (preds * 0.9).clamp(0.0, 1.0)

psnr = PeakSignalNoiseRatio(data_range=1.0)
ssim = StructuralSimilarityIndexMeasure(data_range=1.0)
ms_ssim = MultiScaleStructuralSimilarityIndexMeasure(data_range=1.0)

print(psnr(preds, target))
print(ssim(preds, target))
print(ms_ssim(preds, target))
```

Practical notes:

- Keep the tensors on the same device and with the same dtype.
- For SSIM and MS-SSIM, use a spatial size large enough for the default kernel and scale pyramid.
- For `PSNR`, pass `data_range` explicitly instead of trying to infer it from a batch.

## 2) Segmentation workflow

### One-hot / mixed DiceScore

```python
import torch
import torch.nn.functional as F
from torchmetrics.segmentation import DiceScore

index_target = torch.tensor([[[0, 1], [2, 1]]])
preds_one_hot = F.one_hot(index_target, num_classes=3).movedim(-1, 1).to(torch.bool)

dice = DiceScore(
    num_classes=3,
    include_background=False,
    average="none",
    aggregation_level="samplewise",
    input_format="mixed",
)
score = dice(preds_one_hot, index_target)
print(score)
```

### Index MeanIoU and HausdorffDistance

```python
import torch
from torchmetrics.segmentation import HausdorffDistance, MeanIoU

index_target = torch.tensor([[[0, 1], [2, 1]]])

miou = MeanIoU(num_classes=3, include_background=False, per_class=True, input_format="index")
hd = HausdorffDistance(
    num_classes=3,
    include_background=False,
    input_format="index",
    spacing=[1.0, 1.5],
    directed=True,
)

print(miou(index_target, index_target))
print(hd(index_target, index_target))
```

Practical notes:

- `input_format="mixed"` is useful when one tensor is already one-hot and the other is index-based.
- `include_background=False` drops class 0 from the result, so expected output lengths shrink by one.
- `MeanIoU` returns `-1` for classes absent from both prediction and target in per-class mode.
- `HausdorffDistance` can accept `spacing` and `directed`; identical masks should give `0`.

## 3) Detection and instance segmentation workflow

### mAP with both bbox and segm

```python
import torch
from torchmetrics.detection import MeanAveragePrecision

boxes = torch.tensor([[1.0, 1.0, 3.0, 3.0]])
mask = torch.tensor(
    [[[0, 0, 0, 0],
      [0, 1, 1, 0],
      [0, 1, 1, 0],
      [0, 0, 0, 0]]],
    dtype=torch.bool,
)

preds = [dict(boxes=boxes, scores=torch.tensor([0.9]), labels=torch.tensor([0]), masks=mask)]
target = [dict(boxes=boxes.clone(), labels=torch.tensor([0]), masks=mask.clone())]

metric = MeanAveragePrecision(box_format="xyxy", iou_type=("bbox", "segm"), backend="pycocotools")
print(metric(preds, target))
```

### IoU family without scores

```python
import torch
from torchmetrics.detection import IntersectionOverUnion

preds = [dict(boxes=torch.tensor([[1.0, 1.0, 3.0, 3.0]]), labels=torch.tensor([0]))]
target = [dict(boxes=torch.tensor([[1.0, 1.0, 3.0, 3.0]]), labels=torch.tensor([0]))]

iou = IntersectionOverUnion(box_format="xyxy", class_metrics=True)
print(iou(preds, target))
```

Practical notes:

- Use `MeanAveragePrecision` when you need scores and COCO-style metrics.
- Use the IoU family when you only need overlap checks and label-aware box matching.
- For mAP segmentation, `masks` must be boolean and aligned with `labels`.
- `pycocotools` and `faster_coco_eval` are backend choices, not model choices.

## 4) Panoptic workflow

```python
import torch
from torchmetrics.detection import PanopticQuality

preds = torch.tensor([[[[0, 1], [0, 1]], [[1, 0], [1, 0]]]])
target = preds.clone()

pq = PanopticQuality(things={0}, stuffs={1})
print(pq(preds, target))
```

Practical notes:

- The final dimension must be 2: category id and instance id.
- Keep `things` and `stuffs` disjoint.
- Use `allow_unknown_preds_category=True` only when you really want unknown predicted categories to be ignored.
- `ModifiedPanopticQuality` uses the same input layout, but a different stuff-class scoring rule.

## 5) Smoke script workflow

Run the bundled smoke helper when you want a quick check of the installed package.

```bash
python scripts/vision_detection_metric_smoke.py --device cpu
python scripts/vision_detection_metric_smoke.py --device cuda --include-panoptic
```

Use the smoke script only after the package is installed in the current environment; it does not download weights or data.
