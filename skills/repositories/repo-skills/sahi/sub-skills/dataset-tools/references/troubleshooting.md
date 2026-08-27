# Dataset Tools Troubleshooting

Use this guide for COCO loading, slicing, YOLO export, evaluation/error analysis,
and FiftyOne visualization failures.

## Quick triage

1. Validate the JSON top-level keys: `images`, `annotations`, and `categories`.
2. Confirm every `images[*].file_name` resolves under the `image_dir` supplied to
   SAHI.
3. Confirm every annotation/result `image_id` and `category_id` exists in the
   dataset.
4. Inspect `Coco.stats`, especially `num_images`, `num_annotations`,
   `num_categories`, and `num_negative_images`.
5. If evaluation or visualization fails, check optional dependencies before
   changing the dataset.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError: 'images'`, `'annotations'`, or `'categories'` | COCO JSON is missing required top-level keys or the task passed a result JSON where a dataset JSON was expected. | Use a dataset dict with `images`, `annotations`, `categories`. Use a list of prediction dicts only for result JSON. |
| `KeyError` for `category_id` during load | An annotation references a category ID not present after remapping. | Verify category IDs before loading; if using `remapping_dict`, include every source category ID that may appear in annotations. |
| Duplicate image warning and fewer images than expected | Multiple `images` rows share the same `id`. | Deduplicate or renumber image IDs before loading. |
| Image-read failure during slicing | `image_dir / file_name` does not exist, or `file_name` contains an unexpected nested path. | Use the correct image directory; rewrite `file_name` values to paths relative to that directory. |
| Negative images disappear | `ignore_negative_samples=True` was used during export, slicing, prediction array creation, or YOLO export. | Reload/re-export with `ignore_negative_samples=False` when empty images/tiles are required. |
| Category names and IDs look swapped or inconsistent | Dataset categories are not aligned with target training/evaluation convention. | Create a deliberate `desired_name2id` mapping and call `coco.update_categories(...)` before splitting/export. For YOLO, prefer zero-based contiguous IDs. |
| YOLO labels use unexpected class numbers | SAHI writes `annotation.category_id` directly into label txt rows. | Remap COCO category IDs before `export_as_yolo()` or `sahi coco yolo`. |
| Bboxes are negative or extend beyond image bounds | Source annotations/results are not clipped to image dimensions. | Load with `clip_bboxes_to_img_dims=True`, call `get_coco_with_clipped_bboxes()`, and clean predictions with `remove_invalid_coco_results(...)`. Fully outside boxes are dropped by clipping. |
| Sliced dataset has too few annotations | `min_area_ratio` filtered small fragments, or boxes barely intersect slices. | Lower `min_area_ratio` for small-object work; verify slice size/overlap. |
| Sliced dataset has many empty tiles | Negative tiles are preserved by default. | If the task wants only positive tiles, set `ignore_negative_samples=True`; otherwise keep them for negative training examples. |
| `ModuleNotFoundError: pycocotools` during evaluate/analyse | Optional evaluation dependency is absent. | Install/verify `pycocotools` only when metrics are required. If not available, run fallback JSON validation and report metrics as unavailable. |
| `ModuleNotFoundError: matplotlib` during analyse | Error-analysis plotting dependency is absent. | Install/verify `matplotlib` for plots or skip `sahi coco analyse` and keep JSON validation/evaluation only. |
| FiftyOne import or app launch fails | Optional FiftyOne dependency is absent, the environment is headless, or the app port/UI is unavailable. | Treat FiftyOne as optional. Use `sahi coco fiftyone` only in an interactive environment; otherwise validate COCO/result JSON and use static evaluation outputs. |
| FiftyOne command appears to hang | The command keeps the app session alive by design. | Close the UI/session or interrupt the process after inspection. Do not use it as a non-interactive smoke check. |
| YOLO export fails on symlink permissions | SAHI creates image symlinks by default; some systems require elevated privileges or disallow symlinks. | Pass `disable_symlink=True` in Python or `--disable_symlink` in CLI to copy images instead. |
| YOLO export skips an image | Image file has no suffix, has a text-like suffix, contains an invalid bbox, or is a negative sample with `ignore_negative_samples=True`. | Ensure image file names have image extensions, clip/validate boxes, and set negative-sample handling deliberately. |
| Fire CLI rejects an option name | The command exposes Python parameter names. | Use `--output_dir` for `sahi coco slice`, `--iou_thresh` for `sahi coco fiftyone`, and `--no_extraplots` to suppress analysis extras. |

## Fallback validation when `pycocotools` is unavailable

When COCO metrics are requested but `pycocotools` is missing, do not fabricate
mAP/mAR. Provide a validation-only fallback:

```python
from sahi.utils.coco import Coco, remove_invalid_coco_results

coco = Coco.from_coco_dict_or_path(
    "annotations.json",
    image_dir="images",
    ignore_negative_samples=False,
    clip_bboxes_to_img_dims=True,
)
fixed_results = remove_invalid_coco_results("predictions.json", coco.json)

image_ids = {image["id"] for image in coco.json["images"]}
category_ids = {category["id"] for category in coco.json["categories"]}
for pred in fixed_results:
    assert pred["image_id"] in image_ids
    assert pred["category_id"] in category_ids
    assert pred["bbox"][2] > 0 and pred["bbox"][3] > 0
    assert 0 <= pred.get("score", 0) <= 1
```

Report this as structural validation, not COCO evaluation.

## Difficult case: class-remapped split with negative samples

Use this sequence when a dataset must be class-remapped, split, and exported
without losing negative images:

1. Load with `ignore_negative_samples=False` and `clip_bboxes_to_img_dims=True`.
2. Record `stats["num_negative_images"]` and category counts.
3. Call `coco.update_categories({"target_name": 0, ...})` to filter/remap.
4. Re-check that annotation category IDs are in the desired ID set.
5. Split with `split_coco_as_train_val(train_split_rate=..., numpy_seed=...)`.
6. Save train/val JSON explicitly and verify negative images are still present
   if required.
7. Export YOLO with `disable_symlink=True` if permissions are uncertain.

## Safe smoke check

Run the bundled smoke script when changing dataset-tool guidance or diagnosing a
minimal SAHI install:

```bash
python ../scripts/coco_fixture_smoke.py
```

From this `references/` directory, the relative path above points to the helper
script. The script uses temporary files only and does not require pycocotools,
FiftyOne, model weights, network access, or training.
