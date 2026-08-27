# Data Formats

## YOLO annotation row schema

The repo uses one annotation row per image. Keep the file plain text with no header.
Blank lines are ignored by the dataset loader, but comment lines are not supported.

```text
image_path xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id ...
```

- `image_path` points to the image file.
- Each box is a comma-separated tuple: `xmin,ymin,xmax,ymax,class_id`.
- Coordinates may be written as integers or decimals, but they must describe valid boxes.
- `class_id` is a zero-based integer index into the chosen class-name file.
- Rows with no boxes are not useful for training and should be rejected by the validator.

Example:

```text
images/000001.jpg 48,240,195,371,11 8,12,352,498,14
```

If the annotation rows use relative image paths, validate them with `--image-root` so the checker knows which directory to search.

## Class-name files

Class files are one class per line.
`core.utils.read_class_names` assigns the first line id `0`, the second line id `1`, and so on.

Repository defaults:

- `data/classes/coco.names` contains 80 COCO classes.
- `data/classes/voc.names` contains 20 Pascal VOC classes.

Rules to keep in mind:

- Do not add blank lines.
- Do not reorder class names unless you also rewrite every annotation row.
- If you switch class files, update `cfg.YOLO.CLASSES` and make sure every `class_id` in the annotation rows matches the new order.

## Anchor files

`cfg.YOLO.ANCHORS` points to the anchor text file used by `core.utils.get_anchors`.
The bundled parser reads one line, splits on commas, and reshapes the values into `(3, 3, 2)`.
That means the file must contain exactly 18 numeric values.

Repository defaults:

- `data/anchors/basline_anchors.txt` is the main default anchor file.
- `data/anchors/coco_anchors.txt` is the COCO-style alternative.

Rules to keep in mind:

- Keep the file as a single data line.
- Keep the values numeric and positive.
- Preserve the order of the 3 anchors per scale.

## Config fields that matter here

| Field | Meaning | Data-preparation note |
|---|---|---|
| `cfg.YOLO.CLASSES` | Path to the class-name file | Must match the ids used in annotation rows. |
| `cfg.YOLO.ANCHORS` | Path to the anchor file | Must parse to 18 values and reshape to `(3, 3, 2)`. |
| `cfg.YOLO.ANCHOR_PER_SCALE` | Anchors per detection scale | This repo uses `3`. |
| `cfg.YOLO.STRIDES` | Detection strides | This repo uses `[8, 16, 32]`. |
| `cfg.TRAIN.ANNOT_PATH` | Training annotation list | Usually `./data/dataset/voc_train.txt`. |
| `cfg.TEST.ANNOT_PATH` | Test annotation list | Usually `./data/dataset/voc_test.txt`. |
| `cfg.TRAIN.INPUT_SIZE` | Multi-scale training sizes | The parser picks one size at random per batch. |
| `cfg.TEST.INPUT_SIZE` | Fixed test size | Used when building test batches. |
| `cfg.TRAIN.DATA_AUG` | Training augmentation toggle | True by default. |
| `cfg.TEST.DATA_AUG` | Test augmentation toggle | False by default. |

## Dataset parser caveats

`core.dataset.Dataset` is strict in a few important ways:

- `load_annotations` skips blank lines and shuffles the remaining rows.
- `parse_annotation` raises a `KeyError` when the image path does not exist.
- Box text is parsed with `int(float(x))`, so malformed numeric text can turn into hard-to-debug label issues.
- Zero-area boxes are dropped when `x2 <= x1` or `y2 <= y1`.
- Coordinates outside the image are clipped after preprocessing, but the validator still treats them as authoring problems.
- `max_bbox_per_scale` is `150`, so very crowded rows still need valid geometry.
- `core.utils.draw_bbox` defaults to `cfg.YOLO.CLASSES`, so helper scripts should run from a context where relative paths resolve correctly.

## Practical rule

If a label file, class file, or anchor file changed, validate it before you start training or exporting models.
Use the bundled script instead of trusting the dataset loader to surface every mistake.
