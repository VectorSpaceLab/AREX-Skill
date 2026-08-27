# AMG API Reference

## Imports and Model Loading

```python
import cv2
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")
sam.to(device="cpu")
mask_generator = SamAutomaticMaskGenerator(sam)
masks = mask_generator.generate(image)
```

`generate(image)` expects an RGB `numpy.ndarray` in HWC layout, usually `uint8`. OpenCV reads BGR, so convert BGR to RGB before calling `generate`.

## Constructor

Installed signature:

```python
SamAutomaticMaskGenerator(
    model,
    points_per_side=32,
    points_per_batch=64,
    pred_iou_thresh=0.88,
    stability_score_thresh=0.95,
    crop_n_layers=0,
    min_mask_region_area=0,
    output_mode="binary_mask",
)
```

The full implementation also accepts `stability_score_offset=1.0`, `box_nms_thresh=0.7`, `crop_nms_thresh=0.7`, `crop_overlap_ratio=512 / 1500`, `crop_n_points_downscale_factor=1`, and `point_grids=None`.

## Main Settings

- `points_per_side`: samples a square grid over the image; total prompt points are `points_per_side ** 2` before crop expansion.
- `points_per_batch`: controls how many sampled points run together; higher values can be faster but use more memory.
- `pred_iou_thresh`: drops masks with low model-predicted quality.
- `stability_score_thresh`: drops masks that are unstable under mask-threshold perturbation.
- `stability_score_offset`: controls how strongly the stability check perturbs the mask threshold.
- `box_nms_thresh`: removes duplicate masks within a crop using box IoU.
- `crop_n_layers`: adds crop layers so small objects get more sampling; this greatly increases work and memory.
- `crop_nms_thresh`: removes duplicate masks across crop layers.
- `crop_overlap_ratio`: controls crop overlap; more overlap can reduce edge artifacts but increases duplicate work.
- `crop_n_points_downscale_factor`: reduces point density on deeper crop layers.
- `min_mask_region_area`: removes small holes/islands after generation; requires OpenCV when greater than zero.
- `output_mode`: use `binary_mask`, `uncompressed_rle`, or `coco_rle`; `coco_rle` requires `pycocotools`.

Exactly one of `points_per_side` or explicit `point_grids` must be provided. If using default construction, `points_per_side=32` satisfies that requirement.

## Output Records

`generate(image)` returns `list[dict]`, one record per mask:

```python
{
    "segmentation": mask_or_rle,
    "area": int,
    "bbox": [x, y, w, h],
    "predicted_iou": float,
    "point_coords": [[x, y]],
    "stability_score": float,
    "crop_box": [x, y, w, h],
}
```

`bbox` and `crop_box` use XYWH pixel coordinates. `point_coords` is the sampled point that produced the mask.

## Output Modes

- `binary_mask`: `segmentation` is an `H x W` boolean NumPy array. This is easy to write as PNG but can consume a lot of memory for large images or many masks.
- `uncompressed_rle`: `segmentation` is a dict with `size` and integer `counts` lists.
- `coco_rle`: `segmentation` is COCO-compatible compressed RLE with JSON-serializable `counts`; install `pycocotools` first.

## Minimal COCO RLE Example

```python
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
sam.to(device="cuda")
generator = SamAutomaticMaskGenerator(sam, output_mode="coco_rle")
records = generator.generate(image)
```

To decode a COCO RLE mask later:

```python
from pycocotools import mask as mask_utils
binary = mask_utils.decode(records[0]["segmentation"])
```
