# Structures and Outputs

Detectron2 model outputs are nested dictionaries containing tensors and structure classes. Inspect fields defensively before visualizing or serializing.

## Builtin Inference Output Dictionary

Builtin models in eval mode return `list[dict]`, one dictionary per image. `DefaultPredictor` unwraps the single-image list and returns one dictionary directly.

Common keys:

| Key | Value | Meaning |
| --- | --- | --- |
| `instances` | `Instances` | Instance detection/segmentation/keypoint predictions. |
| `sem_seg` | `Tensor[num_classes, H, W]` | Per-class semantic logits or probabilities; visualize `argmax(dim=0)`. |
| `panoptic_seg` | `(Tensor[H, W], list[dict] | None)` | Panoptic ids plus segment metadata. |
| `proposals` | `Instances` | Proposal boxes and objectness logits, usually for debugging/proposal models. |

## Instances

`Instances(image_size, **fields)` stores per-instance fields for one image. `image_size` is `(height, width)`. All fields must have the same length.

Useful methods and behavior:

- `instances.has("field")`: check whether a field exists.
- `instances.get("field")` or `instances.field`: read a field; missing attribute access raises `AttributeError`.
- `instances.get_fields()`: returns the mutable field dictionary.
- `instances.to("cpu")`: moves fields that implement `.to(...)` and returns a new `Instances`.
- `instances[mask_or_indices]`: filters every field consistently.
- `len(instances)`: number of instances; empty `Instances` with no fields does not support `len()`.
- `Instances.cat([...])`: concatenates compatible instance lists.

Typical prediction fields:

| Field | Type | Notes |
| --- | --- | --- |
| `pred_boxes` | `Boxes` or tensor-like boxes | `Visualizer` accepts `Boxes` or an `Nx4` array/tensor in XYXY order. |
| `scores` | `Tensor[N]` | Confidence scores after thresholding/NMS. |
| `pred_classes` | `Tensor[N]` | Contiguous class ids; names come from metadata `thing_classes`. |
| `pred_masks` | `Tensor[N,H,W]` or bool-like masks | Used by `Visualizer`; move to CPU first. |
| `pred_keypoints` | `Tensor[N,K,3]` | Keypoint x, y, confidence triples. |
| `proposal_boxes` | `Boxes` | Proposal/debug outputs. |
| `objectness_logits` | `Tensor[N]` | Proposal/debug scores. |

Robust inspection pattern:

```python
instances = outputs.get("instances")
if instances is not None:
    instances = instances.to("cpu")
    fields = instances.get_fields()
    if instances.has("scores"):
        keep = instances.scores >= 0.5
        instances = instances[keep]
    if not instances.has("pred_boxes") and not instances.has("pred_masks"):
        raise ValueError("Need pred_boxes or pred_masks before instance visualization")
```

## Boxes and BoxMode

`Boxes(tensor)` wraps an `Nx4` float tensor in absolute `XYXY_ABS` order: `(x0, y0, x1, y1)`.

Common operations:

- `boxes.tensor`: underlying `float32` tensor.
- `boxes.to(device)`: returns a new `Boxes` on the device.
- `boxes.area()`: area per box.
- `boxes.clip((height, width))`: clamps coordinates in-place.
- `boxes.nonempty(threshold=0.0)`: boolean mask for boxes with positive width/height.
- `boxes[i]`, `boxes[mask]`: indexed subset.
- `Boxes.cat([...])`: concatenate boxes.

Use `BoxMode.convert` for COCO-style boxes and rotated boxes:

```python
from detectron2.structures import BoxMode

xyxy = BoxMode.convert([x, y, width, height], BoxMode.XYWH_ABS, BoxMode.XYXY_ABS)
xywh = BoxMode.convert(xyxy_array, BoxMode.XYXY_ABS, BoxMode.XYWH_ABS)
```

Relative modes (`XYXY_REL`, `XYWH_REL`) are not implemented for conversion in this version.

## Masks

`BitMasks(tensor)` stores boolean masks as `N,H,W`. It supports indexing, `.to(...)`, `nonempty()`, `get_bounding_boxes()`, and `BitMasks.from_polygon_masks(...)`.

`PolygonMasks(polygons)` stores polygon lists for each instance and can compute bounding boxes. COCO polygon coordinates are flat `[x0, y0, x1, y1, ...]` arrays; each polygon needs at least three points.

`Visualizer.draw_instance_predictions` accepts `pred_masks` and converts each mask to a generic drawable mask. Ensure masks are on CPU before visualization.

## ImageList

`ImageList.from_tensors(tensors, size_divisibility=0, pad_value=0.0, padding_constraints=None)` pads tensors with the same non-spatial shape to a single batched tensor and records original image sizes.

Use it for partial model execution or custom batching:

```python
from detectron2.structures import ImageList

images = ImageList.from_tensors([image1_chw, image2_chw], size_divisibility=32)
assert images.tensor.shape[0] == 2
assert images.image_sizes[0] == (height1, width1)
```

Each original image can be recovered with `images[i]`, cropped to its recorded size.

## Visualizer Requirements

`Visualizer(img_rgb, metadata=None, scale=1.0, instance_mode=ColorMode.IMAGE, font_size_scale=1.0)` expects an RGB image in `H,W,3` order.

High-level methods:

- `draw_instance_predictions(instances)`: uses `pred_boxes`, `pred_classes`, `scores`, `pred_masks` or `pred_masks_rle`, and `pred_keypoints` when present.
- `draw_sem_seg(sem_seg)`: expects `H,W` integer labels, often `outputs["sem_seg"].argmax(dim=0)`.
- `draw_panoptic_seg_predictions(panoptic_seg, segments_info)`: expects `H,W` ids and segment dictionaries.
- `draw_dataset_dict(record)`: draws dataset annotations; route dataset schema questions to the data-datasets sub-skill.
- `VisImage.save(path)` writes an image; `VisImage.get_image()` returns RGB `uint8` output.

`ColorMode` choices:

- `ColorMode.IMAGE`: random-ish colors with translucent overlays.
- `ColorMode.SEGMENTATION`: class-color driven overlays when metadata has `thing_colors`.
- `ColorMode.IMAGE_BW`: grays out unmasked regions for mask predictions; useful only when masks exist.

Metadata affects labels and colors. For instance visualization, metadata should provide `thing_classes` and optionally `thing_colors`. Without class names, labels degrade to integer ids.

## Prediction JSON Checks

COCO-style instance prediction JSON is typically a list of objects with:

- `image_id`: string or integer image identifier.
- `category_id`: dataset category id, not necessarily contiguous model class id.
- `bbox`: four numeric values in COCO `XYWH_ABS` order.
- `score`: numeric confidence, usually in `[0, 1]`.
- Optional `segmentation`: polygon list, uncompressed RLE, or compressed RLE.

Before drawing JSON predictions, validate schema and metadata assumptions with `scripts/visualize_json_schema_check.py`. If converting JSON rows to `Instances`, convert boxes from `XYWH_ABS` to `XYXY_ABS`, map dataset category ids to contiguous ids using dataset metadata, set `scores`, `pred_boxes`, `pred_classes`, and optionally `pred_masks`.
