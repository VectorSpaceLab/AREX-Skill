# Data Preparation Troubleshooting

## `Image Count: 0`

Check that the loader selected the correct subset and actually calls `add_image()`. For folder-based datasets, verify the split directory exists and contains image files or image-id subdirectories.

Run:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_layout.py balloon /path/to/balloon_dataset
python sub-skills/data-preparation/scripts/validate_dataset_layout.py nucleus /path/to/nucleus_root --subset stage1_train
python sub-skills/data-preparation/scripts/validate_dataset_layout.py coco /path/to/coco_root --subset val --year 2014
```

## Empty masks or all-zero boxes

Likely causes:

- Polygon coordinates are missing or outside the image.
- VIA `regions` is a list but the loader expects a dict, or vice versa.
- Mask PNGs are empty or not under the expected `masks/` folder.
- Augmentation or crop removed every instance.
- `mask` shape is `[instances, H, W]` instead of `[H, W, instances]`.

Validate a few records manually. Then use `utils.extract_bboxes(mask)` to ensure positive box areas before training.

## `Source name cannot contain a dot`

`Dataset.add_class()` forbids dots because class lookup keys are built as `source.class_id`. Use names such as `balloon`, `nucleus`, or `customdataset`, not `my.dataset`.

## `KeyError` in `map_source_class_id`

The source/class id string does not exist in the prepared class map. Ensure the dataset calls `add_class(source, class_id, name)` before images and that class ids in `load_mask()` correspond to the classes you added.

## `Minimum dimension must be a multiple of 64`

`pad64` mode asserts `IMAGE_MIN_DIM % 64 == 0`. Use values like 512, 768, or 1024. For random crops, use `crop` only in training.

## VIA JSON parsed but masks are wrong

VIA versions differ:

```python
regions = annotation["regions"]
if isinstance(regions, dict):
    polygons = [r["shape_attributes"] for r in regions.values()]
else:
    polygons = [r["shape_attributes"] for r in regions]
```

Ignore records with no regions for training unless the task explicitly includes negative/background-only images.

## Nucleus validation split misses IDs

The sample hard-codes validation image ids. If a fork or partial dataset lacks those ids, the `val` subset can fail or become empty. Use explicit `stage1_train` for full loader checks, or adjust the validation id list in a project-specific dataset subclass.

## COCO annotations load but image files are missing

The sample maps `minival` and `valminusminival` annotations to images under `val<year>`. For 2014, make sure `val2014/` exists even when using minival annotations. For 2017, minival/valminusminival are not the normal splits.
