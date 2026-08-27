# COCO CLI and API

This reference summarizes SAHI's dataset-facing COCO utilities. It assumes the
base SAHI package is importable. `pycocotools` and FiftyOne are optional: do not
assume they are installed unless the current task verifies them.

## Core imports

```python
from sahi.utils.coco import (
    Coco,
    CocoCategory,
    CocoImage,
    CocoAnnotation,
    CocoPrediction,
    export_coco_as_yolo,
    remove_invalid_coco_results,
)
from sahi.slicing import slice_coco
from sahi.utils.file import save_json
```

## Core objects

| Object | Use it for | Key notes |
|---|---|---|
| `CocoCategory(id, name, supercategory=None)` | Dataset category rows. | `supercategory` defaults to `name`; `Coco.add_category()` expects `CocoCategory`. |
| `CocoImage(file_name, height, width, id=None)` | One image plus its annotations and predictions. | `file_name` is resolved against `Coco.image_dir` by loaders/exporters unless already a file path. Use `add_annotation()` and `add_prediction()`. |
| `CocoAnnotation(...)` | Ground-truth annotation. | Construct from `bbox=[x, y, width, height]` or polygon `segmentation`. The `.json` property includes `bbox`, `segmentation`, `category_id`, `image_id`, `iscrowd`, and `area`. |
| `CocoPrediction(...)` | Prediction entry in COCO result format. | Same geometry as `CocoAnnotation` plus `score`; `Coco.prediction_array` exports a list suitable for COCO-result consumers. |
| `Coco(...)` | Dataset container and high-level operations. | Holds `categories` and `images`; `.json`, `.prediction_array`, and `.stats` are the main exports. |

Common constructor options for `Coco`:

- `image_dir`: base directory for images; required for merge workflows and YOLO
  export when image file names are relative.
- `ignore_negative_samples`: when `True`, JSON/export helpers skip images that
  have no annotations or predictions. Keep it `False` when negative samples are
  part of the training/evaluation contract.
- `remapping_dict`: maps source category IDs to target IDs while loading.
- `clip_bboxes_to_img_dims`: clips overflowing boxes to image boundaries when
  loading or when calling `get_coco_with_clipped_bboxes()`.
- `image_id_setting`: `auto` reassigns image IDs during export; `manual` requires
  every `CocoImage.id` to be set.

## Create and export a tiny COCO dataset

```python
coco = Coco(image_dir="images", ignore_negative_samples=False)
coco.add_category(CocoCategory(id=0, name="vehicle"))

image = CocoImage(file_name="frame001.jpg", height=720, width=1280)
image.add_annotation(
    CocoAnnotation(bbox=[100, 120, 40, 30], category_id=0, category_name="vehicle")
)
image.add_prediction(
    CocoPrediction(bbox=[102, 121, 38, 29], category_id=0, category_name="vehicle", score=0.91)
)
coco.add_image(image)

save_json(coco.json, "annotations.json")
save_json(coco.prediction_array, "predictions.json")
```

## Loading and validation-oriented inspection

```python
coco = Coco.from_coco_dict_or_path(
    "annotations.json",
    image_dir="images",
    ignore_negative_samples=False,
    clip_bboxes_to_img_dims=True,
)
print(coco.stats)
```

Loading accepts either a dict or a JSON path. COCO `images`, `annotations`, and
`categories` keys are expected. RLE segmentations are skipped with a warning;
polygon segmentations and bboxes are supported. Duplicate `image_id` values are
ignored after the first occurrence.

## Dataset operations

| Operation | API | Result and caveats |
|---|---|---|
| Remap/filter categories | `coco.update_categories(desired_name2id)` or `update_categories(desired_name2id, coco_dict)` | Categories absent from `desired_name2id` are removed from annotations. The output category list follows `desired_name2id`; use this to make YOLO class IDs zero-based before export. |
| Merge datasets | `coco_a.merge(coco_b, desired_name2id=None)` | Both `Coco` objects need `image_dir`. With no mapping, categories are combined by name; with a mapping, annotation IDs and image IDs are regenerated in export. Review `file_name` values for portability after merging. |
| Train/val split | `coco.split_coco_as_train_val(train_split_rate=0.85, numpy_seed=0)` | Returns `{"train_coco": Coco, "val_coco": Coco}`. Save each `.json` explicitly. The seed is passed to Python's standard `random.shuffle`. |
| Subsample | `coco.get_subsampled_coco(subsample_ratio=10, category_id=None)` | `category_id=-1` targets negative images; otherwise a category ID selects images containing that category. |
| Upsample | `coco.get_upsampled_coco(upsample_ratio=10, category_id=None)` | Repeats images. With a category ID, the first pass preserves all images and later passes repeat selected images. |
| Area filter | `coco.get_area_filtered_coco(min=50, max_val=10000, intervals_per_category=None)` | Drops any image containing an annotation outside the allowed interval. Per-category intervals are keyed by category name. |
| Clip boxes | `coco.get_coco_with_clipped_bboxes()` | Keeps images, clips intersecting boxes to image bounds, and drops boxes fully outside the image. |
| Clean result JSON | `remove_invalid_coco_results(results, dataset)` | Removes empty/negative/extreme prediction boxes; use before optional pycocotools evaluation when model output may contain invalid boxes. |

## Slicing COCO datasets

API:

```python
sliced_dict, sliced_json_path = slice_coco(
    coco_annotation_file_path="annotations.json",
    image_dir="images",
    output_coco_annotation_file_name="annotations_sliced",
    output_dir="sliced",
    ignore_negative_samples=False,
    slice_height=512,
    slice_width=512,
    overlap_height_ratio=0.2,
    overlap_width_ratio=0.2,
    min_area_ratio=0.1,
    out_ext=".jpg",
)
```

Important details:

- `output_coco_annotation_file_name` is required by the Python function. When it
  and `output_dir` are provided, the saved JSON is
  `<output_dir>/<output_coco_annotation_file_name>_coco.json`.
- Each sliced image file name includes the original stem, image index, and slice
  coordinates. Annotations are shifted into slice coordinates and filtered when
  the retained area/original area ratio is below `min_area_ratio`.
- Keep `ignore_negative_samples=False` when empty tiles are useful negative
  training examples.

CLI:

```bash
sahi coco slice \
  --image_dir images \
  --dataset_json_path annotations.json \
  --slice_size 512 \
  --overlap_ratio 0.2 \
  --output_dir runs/slice_coco \
  --min_area_ratio 0.1
```

The CLI is implemented with Fire and exposes Python parameter names. If a
third-party snippet uses a different alias, prefer the parameter names above.

## YOLO export

Single COCO object with auto split:

```python
coco = Coco.from_coco_dict_or_path("annotations.json", image_dir="images")
coco.update_categories({"vehicle": 0, "person": 1})
coco.export_as_yolo("yolo_out", train_split_rate=0.9, numpy_seed=0, disable_symlink=True)
```

Pre-split objects:

```python
data_yml_path = export_coco_as_yolo(
    output_dir="yolo_out",
    train_coco=train_coco,
    val_coco=val_coco,
    disable_symlink=True,
)
```

CLI:

```bash
sahi coco yolo \
  --image_dir images \
  --dataset_json_path annotations.json \
  --train_split 0.9 \
  --project runs/coco2yolo \
  --name exp \
  --disable_symlink
```

YOLO export writes normalized `class x_center y_center width height` rows. SAHI
uses the COCO annotation `category_id` as the class value, so remap to the target
class-index convention first.

## Evaluation and error analysis

These workflows require optional packages. `sahi coco evaluate` requires
`pycocotools`. `sahi coco analyse` requires `pycocotools` and `matplotlib`.

```bash
sahi coco evaluate \
  --dataset_json_path annotations.json \
  --result_json_path predictions.json \
  --out_dir eval \
  --type bbox \
  --classwise \
  --max_detections 500 \
  --iou_thrs='[0.5,0.75]'
```

The evaluator writes `eval.json` under `out_dir` or beside the result file when
`out_dir` is omitted.

```bash
sahi coco analyse \
  --dataset_json_path annotations.json \
  --result_json_path predictions.json \
  --out_dir analysis \
  --type bbox \
  --areas='[1024,9216,10000000000]'
```

Error analysis writes classwise and overall plots under `<out_dir>/<type>/`.
Extra plots are enabled by default; pass `--no_extraplots` to suppress them.

## FiftyOne visualization

FiftyOne is optional and expects an interactive app session.

```bash
sahi coco fiftyone \
  --image_dir images \
  --dataset_json_path annotations.json \
  --iou_thresh 0.5 \
  predictions_a.json predictions_b.json
```

The command loads COCO labels, optionally adds one or more COCO result JSON
files, launches a FiftyOne app, and sorts by false positives for the first result
set. Use the FiftyOne workflow only when an interactive UI/port is acceptable;
for non-interactive checks, prefer COCO JSON validation plus optional evaluation.
