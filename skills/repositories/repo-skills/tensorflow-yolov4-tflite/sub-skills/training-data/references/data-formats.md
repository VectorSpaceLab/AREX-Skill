# Data Formats and Configuration

## Converted annotation line format

The repository's default `Dataset(..., dataset_type="converted_coco")` expects
one image per line:

```text
/path/to/image.jpg xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id ...
```

Rules:

- The first whitespace-separated token is the image path.
- Every remaining token is one bounding box with five comma-separated integer
  fields.
- Coordinates are pixel-space corners: `xmin`, `ymin`, `xmax`, `ymax`.
- `class_id` is a zero-based index into the selected class file.
- Lines with no boxes are ignored by `Dataset.load_annotations` for
  `converted_coco`.

Tiny valid line:

```text
image.jpg 10,20,100,200,0
```

The source `data/dataset/*.txt` files show the format but contain source-author
absolute paths. Regenerate annotation files for the user's machine instead of
copying those paths.

## YOLO text format path

`Dataset(..., dataset_type="yolo")` expects the annotation file to contain image
paths. For each image path, it opens a sibling `.txt` file with YOLO-format boxes:

```text
class_id center_x center_y width height
```

Those values are interpreted as normalized fractions and converted to pixel
corner coordinates using the image width/height. Use this mode only when the
user has YOLO label files beside every image.

## Class files

Default class files live under the repository's `data/classes/` in a target
checkout:

- COCO: `coco.names`, 80 classes; class 0 is `person` and class 79 is
  `toothbrush` in the verified snapshot.
- VOC: `voc.names`, 20 classes.
- Small custom example: `yymnist.names`.

`core.config.cfg.YOLO.CLASSES` defaults to `./data/classes/coco.names`. If a
custom class file is used, class IDs in annotations and the model output class
count must match that file exactly.

## Anchors, strides, and XY scale

`core.config.cfg.YOLO` stores model-family defaults:

| Config key | Meaning |
|---|---|
| `ANCHORS` | YOLOv4 full anchors, reshaped to `(3, 3, 2)`. |
| `ANCHORS_V3` | YOLOv3 full anchors. |
| `ANCHORS_TINY` | Tiny model anchors, reshaped to `(2, 3, 2)`. |
| `STRIDES` | `[8, 16, 32]` for full models. |
| `STRIDES_TINY` | `[16, 32]` for tiny models. |
| `XYSCALE` | YOLOv4 full XY scale factors `[1.2, 1.1, 1.05]`. |
| `XYSCALE_TINY` | Tiny XY scale factors `[1.05, 1.05]`. |
| `ANCHOR_PER_SCALE` | `3`. |
| `IOU_LOSS_THRESH` | `0.5`. |

`utils.load_config(FLAGS)` selects these values from `FLAGS.model` and
`FLAGS.tiny`. Do not mix YOLOv3 anchors with YOLOv4 weights.

## Train/test config defaults

`core.config.cfg.TRAIN` defaults:

- `ANNOT_PATH`: `./data/dataset/val2017.txt`
- `BATCH_SIZE`: `2`
- `INPUT_SIZE`: `416`
- `DATA_AUG`: `True`
- `LR_INIT`: `1e-3`
- `LR_END`: `1e-6`
- `WARMUP_EPOCHS`: `2`
- `FISRT_STAGE_EPOCHS`: `20` (source spelling is `FISRT`, not `FIRST`)
- `SECOND_STAGE_EPOCHS`: `30`

`core.config.cfg.TEST` defaults:

- `ANNOT_PATH`: `./data/dataset/val2017.txt`
- `BATCH_SIZE`: `2`
- `INPUT_SIZE`: `416`
- `DATA_AUG`: `False`
- `DECTECTED_IMAGE_PATH`: `./data/detection/` (source spelling is `DECTECTED`)
- `SCORE_THRESHOLD`: `0.25`
- `IOU_THRESHOLD`: `0.5`

Treat these defaults as examples. For custom training/evaluation, update the
target checkout config deliberately and record the changes in the user's run
notes.
