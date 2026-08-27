# Data-tools troubleshooting

## COCO validator fails

### Missing top-level keys

A MMYOLO COCO-style detection file needs `images`, `annotations`, and `categories` arrays. If a converter outputs only predictions, image info, or a list of annotations, it is not a train/eval annotation file. Re-export or wrap it into the COCO structure before config integration.

### Duplicate ids

Duplicate `images[*].id`, `annotations[*].id`, or `categories[*].id` values make references ambiguous. Reassign ids deterministically and re-check that every annotation points to the intended image and category.

### Annotation references unknown image or category

This usually means a split operation copied only some images/categories or a converter used a different class-id base. Fix the source JSON instead of trying to patch `metainfo` around it.

Checklist:

- Does every `annotation.image_id` exist in `images`?
- Does every `annotation.category_id` exist in `categories`?
- Did a YOLO converter use category ids starting at `0` while a LabelMe class map starts at `1`?
- Did a train/val/test split remove unused categories or images incorrectly?

### Invalid bbox

COCO bboxes are `[x_min, y_min, width, height]` in pixels. Common mistakes:

- Supplying `[x1, y1, x2, y2]` as if it were COCO.
- Leaving YOLO normalized values in the COCO JSON.
- Producing zero or negative width/height.
- Letting normalized YOLO boxes extend outside `[0, 1]` before conversion.
- Forgetting that image dimensions are width/height but NumPy image shapes are height/width.

Use `--allow-out-of-bounds` only when the next converter intentionally clips boxes and that behavior is documented.

### Image files are not found

If `--image-root` fails:

- Confirm `file_name` in the JSON is relative to the intended image prefix.
- Confirm `data_prefix=dict(img='...')` points at the same directory used by validation.
- Avoid absolute `file_name` values for portable MMYOLO configs.
- Check case sensitivity and extensions (`.jpg`, `.jpeg`, `.png`, etc.).

## YOLO txt conversion fails

### Row has the wrong number of fields

Each label row must have exactly five fields:

```text
class_id x_center y_center width height
```

Do not include confidence scores, object names, or segmentation points in this converter's input.

### Normalized coordinates are invalid

All center coordinates and dimensions must be floats in `[0, 1]`, with positive width/height. The derived corners must also remain inside the image:

```text
x_center - width/2 >= 0
x_center + width/2 <= 1
y_center - height/2 >= 0
y_center + height/2 <= 1
```

If the dataset intentionally contains clipped boxes, clip and audit them before conversion rather than hiding the issue.

### Class id is out of range

YOLO class ids are zero-based indexes into `classes.txt`. If `classes.txt` has one class, only `0` is valid in label files. The output COCO category id may still be `0` or `1` depending on `--category-id-start`, but the input label id remains zero-based.

### Dimensions cannot be read

The converter can read common image dimensions directly for real images. For tiny fixtures, generated files, or unsupported formats, pass `--image-width` and `--image-height`. Do not guess dimensions for real data; wrong dimensions produce wrong COCO boxes.

### Missing label file

By default this is an error because missing labels can mean a broken export. Use `--allow-missing-labels` only when unlabeled negative images are intentional. Prefer empty `.txt` files for explicit negative images.

## MMYOLO config/data integration fails

### Metainfo key casing assertion

MMYOLO checks dataloader `metainfo` keys before train/test. Use lowercase keys:

```python
metainfo = dict(classes=('cat', ), palette=[(220, 20, 60)])
```

Do not use `CLASSES`, `PALETTE`, `Classes`, or `Palette` in custom dataloader metainfo.

### Palette length mismatch

The visualization palette should have at least one color per class. If `classes=('cat', 'dog')`, provide two colors or a palette accepted by the visualization stack.

### Evaluator uses the wrong annotation file

Dataloader `ann_file` is often relative to `data_root`; evaluator `ann_file` frequently needs the resolved path string. Keep all three aligned:

```python
val_dataloader = dict(dataset=dict(data_root=data_root, ann_file='annotations/test.json'))
val_evaluator = dict(ann_file=data_root + 'annotations/test.json')
test_evaluator = val_evaluator
```

If metrics are computed on the wrong split, inspect evaluator paths before debugging the model.

### Category names and model head disagree

Symptoms include wrong labels in visualization, impossible metrics, or head-shape mismatch warnings. Check:

- `metainfo.classes` length.
- Model head `num_classes` in the active config.
- Converter class file ordering.
- COCO category names and ids.

Changing dataset classes is not only a data-tools task; route the model/head edit to config-customization.

## Dataset wrapper/import errors

### COCO wrapper dependencies

COCO dataset construction depends on the OpenMMLab detection stack and COCO annotation support. If import/build fails, verify the package installation, then validate the JSON separately with the bundled script to distinguish environment failures from data failures.

### VOC paths

For VOC, keep `data_root` at the shared VOC devkit root and select the year through `data_prefix=dict(sub_data_root='VOC2007/')` or similar. A common mistake is putting the year in both `data_root` and `sub_data_root`.

### DOTA dependencies

DOTA/rotated datasets require optional rotated-detection dependencies. If they are missing, the dataset wrapper raises an import error. Install the required rotated-detection stack or switch to a non-rotated dataset workflow; do not treat the import error as a COCO-format problem.

## Visual browsing/statistics issues

### No display available

For visual dataset tools, use a headless/save-only mode when available and write outputs to an explicit work directory. Do not run interactive browsing in a non-interactive job unless the user explicitly wants it.

### Too many images or slow startup

Use a small COCO subset, a split, or browser image-count controls. Large COCO JSON files and full transform pipelines can take significant time just to initialize.

### Plots look empty

Check whether filtering removed empty images, whether class names match `metainfo`, and whether area thresholds exclude all boxes. COCO metrics showing `-1` for small or medium objects can be normal when the dataset has no objects at that scale.

## Anchor optimization issues

### Wrong model family

Do not optimize anchors for an anchor-free config. If the head uses point generators or does not expose anchor `base_sizes`, route the request to config-customization/model-api instead of inventing anchors.

### CUDA default on a CPU machine

Some anchor workflows default to a CUDA device. Set the device explicitly for CPU-only environments and expect slower clustering on large datasets.

### Different anchors on repeated runs

Clustering has randomness. Use a seed when the utility supports one or record the selected result and config snapshot. Minor variations are expected; large changes suggest the dataset or filters changed.

### Empty or tiny dataset

Anchor optimization needs enough valid boxes. First run COCO validation and dataset statistics; if most images have no boxes or boxes are filtered by size, fix the dataset before optimizing anchors.

## Downloader and split mistakes

- Downloader actions are network operations and can delete archives when requested. Confirm before use.
- Split/subset tools write new annotation files and may copy images. Use a new output directory and keep the original JSON immutable.
- After splitting, validate every generated split and update config dataloaders/evaluators together.
