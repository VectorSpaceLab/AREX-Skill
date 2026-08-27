# Data Formats and Output Layouts

Use this reference when a task needs exact COCO JSON fields, COCO result JSON,
sliced output layout, YOLO export layout, evaluation outputs, or FiftyOne
inputs. Keep paths in examples relative to the user's dataset root.

## COCO detection dataset layout

A typical layout is:

```text
dataset_root/
  images/
    frame001.jpg
    nested/frame002.png
  annotations.json
```

`annotations.json` is a dictionary with these top-level keys:

```json
{
  "images": [
    {"id": 1, "file_name": "frame001.jpg", "height": 720, "width": 1280}
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 0,
      "bbox": [100, 120, 40, 30],
      "segmentation": [],
      "iscrowd": 0,
      "area": 1200
    }
  ],
  "categories": [
    {"id": 0, "name": "vehicle", "supercategory": "vehicle"}
  ]
}
```

Field expectations:

- `images[*].id` must be unique. Duplicate image IDs are ignored after the first
  occurrence by SAHI's loader.
- `images[*].file_name` should resolve under the `image_dir` passed to SAHI.
  Nested relative names such as `nested/frame002.png` are valid if the file
  exists at that relative location.
- `annotations[*].image_id` must refer to an image ID.
- `annotations[*].category_id` must refer to a category ID.
- `bbox` is COCO `xywh`: `[x_min, y_min, width, height]`, not `[x1, y1, x2, y2]`.
- `segmentation` may be an empty list for bbox-only data. Polygon segmentations
  are supported; RLE segmentations are skipped by the SAHI `CocoAnnotation`
  loader.
- `info` and `licenses` are not required for SAHI loading. The COCO evaluation
  script adds an empty `info` field internally when needed.

## Negative samples

A negative sample is an image row with no matching annotation rows. Preserve
negative samples when they are important for training or error analysis:

```python
coco = Coco.from_coco_dict_or_path(
    "annotations.json",
    image_dir="images",
    ignore_negative_samples=False,
)
```

`ignore_negative_samples=True` affects exported `.json`, prediction arrays, and
YOLO export by skipping images with no annotations or predictions.

## COCO result JSON

COCO result files are lists of prediction dictionaries. The minimal evaluation
shape is:

```json
[
  {"image_id": 1, "category_id": 0, "bbox": [102, 121, 38, 29], "score": 0.91}
]
```

SAHI's `CocoPrediction` and `.prediction_array` also include fields such as
`id`, `category_name`, `segmentation`, `iscrowd`, and `area`. COCO evaluation
uses `image_id`, `category_id`, `bbox`, and `score`; extra fields are tolerated
by SAHI utilities but downstream tools may ignore them.

Before evaluation, validate that:

- every result `image_id` is present in the dataset `images` list;
- every result `category_id` is present in the dataset `categories` list;
- every `score` is numeric and normally in `[0, 1]`;
- bbox values are non-negative and inside the corresponding image dimensions;
- bbox width and height are positive.

Use `remove_invalid_coco_results(results, dataset)` as a first cleanup step, then
run stricter task-specific assertions if metrics matter.

## Sliced COCO output

Python API output:

```text
sliced/
  annotations_sliced_coco.json
  frame001_0_0_0_512_512.jpg
  frame001_0_410_0_922_512.jpg
  ...
```

CLI output with `sahi coco slice --output_dir runs/slice_coco`:

```text
runs/slice_coco/
  annotations_512_02.json
  annotations_images_512_02/
    frame001_0_0_0_512_512.jpg
    frame001_0_410_0_922_512.jpg
    ...
```

Output details:

- Slice file names encode source image stem, source image index, and
  `[left, top, right, bottom]` slice coordinates.
- Sliced annotations are clipped to the slice and shifted into slice-local
  coordinates.
- `min_area_ratio` filters fragments whose sliced area divided by original area
  is too small.
- Empty slices are kept unless `ignore_negative_samples=True`.
- The CLI exports image slices as `.jpg`; the Python API can set `out_ext`.

## Train/validation split output

`split_coco_as_train_val()` returns in-memory `Coco` objects; it does not write
files by itself.

```python
split = coco.split_coco_as_train_val(train_split_rate=0.85, numpy_seed=0)
save_json(split["train_coco"].json, "train.json")
save_json(split["val_coco"].json, "val.json")
```

`Coco.json` defaults to auto image IDs, so image and annotation IDs can be
renumbered during export. If the task requires preserving original image IDs,
construct the dataset with `image_id_setting="manual"` and ensure each
`CocoImage.id` is set.

## Class-remapped COCO with negative samples

For a difficult conversion/split task that must preserve negative images and
change class IDs:

```python
coco = Coco.from_coco_dict_or_path(
    "annotations.json",
    image_dir="images",
    ignore_negative_samples=False,
    clip_bboxes_to_img_dims=True,
)

# Keep only selected classes and force the target ID order.
coco.update_categories({"vehicle": 0, "person": 1})

split = coco.split_coco_as_train_val(train_split_rate=0.8, numpy_seed=0)
save_json(split["train_coco"].json, "train.json")
save_json(split["val_coco"].json, "val.json")
```

Check `stats["num_negative_images"]` before and after remap/split when negative
images are required.

## YOLO export layout

SAHI writes an Ultralytics-compatible layout:

```text
yolo_out/
  data.yml
  train/
    frame001.jpg
    frame001.txt
  val/
    frame002.jpg
    frame002.txt
```

Each label row is:

```text
<class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
```

SAHI uses `annotation.category_id` directly as `<class_id>`. If the target YOLO
consumer expects zero-based contiguous IDs, remap the COCO categories before
export. By default SAHI creates image symlinks; pass `disable_symlink=True` or
`--disable_symlink` to copy images instead when symlinks are not permitted.

## Evaluation and analysis outputs

`sahi coco evaluate` writes:

```text
eval/
  eval.json
```

`eval.json` contains metric keys such as `mAP`, `mAP50`, `mAP75`, small/medium
/large variants, and optional classwise values.

`sahi coco analyse` writes plot files under:

```text
analysis/
  bbox/
    ... classwise and overall plot images ...
```

If `out_dir` is omitted, analysis defaults to a `coco_error_analysis` directory
beside the result JSON. These workflows require optional dependencies; when
unavailable, run fallback JSON validation rather than claiming metrics.

## FiftyOne inputs and expectations

FiftyOne visualization expects:

```text
dataset_root/
  images/
    ... image files matching COCO file_name values ...
  annotations.json
  predictions_a.json   # optional COCO result JSON
  predictions_b.json   # optional COCO result JSON
```

The `sahi coco fiftyone` command loads the COCO labels, optionally attaches one
or more COCO result files, starts an interactive app, and keeps the process
alive. Use it only when a UI session and local app port are acceptable.
