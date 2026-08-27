# Dataset and Evaluation Troubleshooting

## Fast Diagnosis Table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` for images or annotations | Wrong `data_root`, `ann_file`, or `data_prefix` join | Resolve the full joined path manually; keep `ann_file` relative to `data_root` unless intentionally absolute. |
| COCO API errors while loading JSON | Missing top-level keys, invalid ids, bad bbox/segmentation fields | Validate `images`, `annotations`, `categories`, id references, positive bbox sizes, and polygon lengths. |
| AP is zero but loss/training ran | Class names/order or `category_id` mapping mismatch | Match `metainfo.classes` to annotation `categories.name` in order; ensure every annotation category id exists. |
| Wrong label names or colors in browsing/inference | Missing or stale `metainfo`/`palette` | Set `metainfo=dict(classes=(...), palette=[...])` consistently for train/val/test. |
| `NumClassCheckHook` or head shape error | Dataset class count changed but model head did not | Update every `num_classes` field, including cascade/list heads, bbox heads, mask heads, and task-specific heads. |
| Validation filters out unexpected samples | Train filtering copied to val/test | Use `test_mode=True` for val/test and avoid train-only `filter_cfg` unless intentional. |
| `KeyError` or missing key inside pipeline | Transform output does not match next transform/model expectations | Check `LoadAnnotations`, custom transforms, and `PackDetInputs`; route custom transform implementation to `customization-extension`. |
| `ModuleNotFoundError: pycocotools` | COCO metrics or mask handling dependency missing | Install `pycocotools` or platform equivalent before COCO evaluation. |
| Cityscapes metric import failure | `cityscapesscripts` missing | Install `cityscapesscripts` before conversion/evaluation. |
| `ModuleNotFoundError: mmcv._ext` | `mmcv-lite` installed instead of full `mmcv` | Install a full MMCV build compatible with the Torch/CUDA/CPU environment. |
| `format_only=True` gives no AP | Format-only mode only exports predictions | Set `format_only=False` and provide ground-truth annotations to compute metrics. |

## COCO Schema Checks

Use these invariants before blaming model code:

```python
image_ids = {item['id'] for item in coco['images']}
category_ids = {item['id'] for item in coco['categories']}
assert all(ann['image_id'] in image_ids for ann in coco['annotations'])
assert all(ann['category_id'] in category_ids for ann in coco['annotations'])
assert all(ann['bbox'][2] > 0 and ann['bbox'][3] > 0 for ann in coco['annotations'])
```

Also check:

- `images[*].file_name` is relative to `data_prefix['img']` unless intentionally absolute.
- `area` is consistent with the bbox or mask convention expected by the evaluator.
- `iscrowd` is present, usually `0` for normal instances.
- Annotation ids are unique.
- If masks are present, polygons have at least six coordinates and an even number of values.

## Class and Category Mismatch

When changing class count, update all of these together:

1. Annotation `categories` entries and intended order.
2. Config `metainfo.classes` for `train_dataloader`, `val_dataloader`, and `test_dataloader`.
3. Optional `metainfo.palette` with one color per class if visualization matters.
4. Model head `num_classes` in every bbox/mask/segmentation head.
5. Evaluator `ann_file` so metrics use the same category universe.

Common trap: COCO `category_id` can be non-contiguous, but model labels are contiguous zero-based indices after dataset mapping. Do not set `bbox_label` in middle-format annotations to raw COCO ids.

## Data Root Mistakes

Debug by expanding examples:

```python
full_ann = data_root + ann_file
full_img = data_root + data_prefix['img'] + first_image_file_name
```

If `data_root='data/coco/'`, `ann_file='annotations/instances_val2017.json'`, and `data_prefix=dict(img='val2017/')`, the resolved image should look like `data/coco/val2017/<file_name>`. Avoid putting `data/coco/` in both `data_root` and `ann_file` unless using absolute paths deliberately.

## Transform Key Mismatch

Typical required flow:

- `LoadImageFromFile` adds image arrays and image metadata.
- `LoadAnnotations(with_bbox=True, with_mask=True)` adds ground-truth boxes, labels, masks, and ignore flags.
- Geometric transforms must update image shape and all geometric annotations together.
- `PackDetInputs` converts fields into model-ready inputs and data samples.

If browsing raw annotations works but training fails, inspect transforms after the first augmentation. If a custom transform is involved, route implementation and registry fixes to `customization-extension`.

## Metric Output Confusion

- `bbox_mAP` is the primary COCO detection AP over IoU 0.50:0.95.
- `bbox_mAP_50` is easier and often much higher.
- `segm_mAP` requires valid masks and mask predictions; bbox-only detectors will not produce it.
- `proposal_fast` evaluates proposal recall quickly and is not detector AP.
- `classwise=True` prints per-class AP and is best for diagnosing a subset of broken categories.
- `format_only=True` writes result files for submission and skips metric computation.

## Image-Only Manifest Limits

A JSON created from image folders with empty `annotations` can be useful for:

- Building a test dataloader for inference.
- Formatting outputs for later submission.
- Starting an annotation project with stable image ids and categories.

It cannot:

- Train a supervised detector.
- Compute bbox/mask AP.
- Prove class balance or annotation quality.

If the user has image folders named by class but no boxes, explain that image-level class labels are insufficient for object detection training without bounding boxes or masks.
