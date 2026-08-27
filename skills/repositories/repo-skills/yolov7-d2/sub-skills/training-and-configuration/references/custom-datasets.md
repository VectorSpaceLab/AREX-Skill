# Custom COCO Dataset Setup

YOLOv7-d2 documentation recommends converting custom datasets to COCO format, then registering the train/validation splits with Detectron2 and matching config dataset names.

## Required COCO pieces

A minimal detection JSON needs:

- `images`: entries with `id`, `file_name`, `height`, `width`.
- `annotations`: entries with `id`, `image_id`, `category_id`, `bbox` in COCO XYWH format. Segmentation tasks also need `segmentation` and valid mask format.
- `categories`: entries with `id` and `name`.

Run the validator before training:

```bash
python scripts/validate_coco_detection_json.py --json path/to/instances_train.json --images path/to/images
```

## Registration pattern

Use Detectron2's COCO registration in the user's project code:

```python
from detectron2.data.datasets import register_coco_instances

register_coco_instances(
    "my_train",
    {},
    "path/to/instances_train.json",
    "path/to/train_images",
)
register_coco_instances(
    "my_val",
    {},
    "path/to/instances_val.json",
    "path/to/val_images",
)
```

Then set config dataset names:

```yaml
DATASETS:
  TRAIN: ("my_train",)
  TEST: ("my_val",)
MODEL:
  YOLO:
    CLASSES: 3
```

For class labels used by visualization, set `DATASETS.CLASS_NAMES` when the config family expects it.

## Anchors

For anchor-based YOLO-family configs, recompute anchors when the custom data has very different object sizes. Use:

```bash
python scripts/compute_anchors_from_coco.py path/to/instances_train.json --clusters 9 --seed 0
```

The helper reads COCO boxes directly and prints anchors sorted by area. It intentionally avoids the source VOC branch because the source helper contains typos and deprecated NumPy usage.

## Safety checklist

- Dataset names in config exactly match registered names.
- Category ids are unique and annotations reference existing image/category ids.
- Image files exist relative to the image root.
- `MODEL.YOLO.CLASSES` equals the number of foreground classes.
- `INPUT.MASK_FORMAT` and `MODEL.MASK_ON` are correct for segmentation tasks.
- Batch size and LR are adjusted for the actual number of GPUs.
