# Dataset formats and MMYOLO config wiring

This reference distills the dataset evidence used by MMYOLO's COCO/VOC/DOTA wrappers, custom-dataset tutorials, and data tests into self-contained checks future agents can apply before training or evaluation.

## COCO detection JSON minimum

A detection annotation file should be a JSON object with these top-level arrays:

```json
{
  "images": [
    {"id": 0, "file_name": "image1.jpg", "width": 640, "height": 480}
  ],
  "categories": [
    {"id": 1, "name": "cat"}
  ],
  "annotations": [
    {"id": 1, "image_id": 0, "category_id": 1, "bbox": [100, 80, 200, 160], "area": 32000, "iscrowd": 0}
  ]
}
```

Required consistency checks:

- `images[*].id` values are unique and every annotation `image_id` exists.
- `categories[*].id` values are unique and every annotation `category_id` exists.
- `annotations[*].id` values are unique.
- `bbox` is absolute pixel `[x_min, y_min, width, height]`; it is **not** normalized and it is **not** `[x1, y1, x2, y2]`.
- `width` and `height` in both images and bboxes are positive. A zero-size bbox may be filtered or break downstream analysis.
- Bboxes should normally be inside the declared image width/height. If a converter clips boxes later, document that intentionally.
- `area` should match `width * height` for detection boxes when present. A mismatch is a warning; a non-positive area with a positive bbox usually indicates a bad converter.
- `iscrowd` is usually `0` for ordinary training boxes. `ignore` may appear in fixtures or crowd-human variants, but do not rely on it for a normal custom dataset unless the config and evaluator are designed for it.

Category ids may be 0-based or 1-based as long as they are unique and match all annotations. MMYOLO/COCO-style LabelMe examples use `class_with_id.txt` with ids starting at `1`; the YOLO txt converter pattern commonly maps YOLO class index `0` to COCO category id `0`. Pick one convention per dataset and keep it consistent with `metainfo.classes` ordering.

Run the bundled validator before config work:

```bash
python scripts/inspect_coco_annotations.py annotations/trainval.json --image-root images --require-annotations
```

## Common COCO file layout

A compact custom dataset layout that works with MMYOLO's COCO configs is:

```text
DATA_ROOT/
├── images/
│   ├── image1.jpg
│   └── image2.png
└── annotations/
    ├── trainval.json
    └── test.json
```

In COCO JSON, `file_name` should usually be relative to the configured image prefix. With the layout above, `file_name: "image1.jpg"` and `data_prefix=dict(img='images/')` point to the same image.

For large projects that already have `train/`, `val/`, and `test/` image directories, keep each JSON's `file_name` convention aligned with the matching `data_prefix` instead of mixing absolute paths and relative paths.

## YOLO txt layout and caveats

A basic YOLO-format input directory contains:

```text
YOLO_ROOT/
├── classes.txt
├── images/
│   ├── a.jpg
│   └── b.png
└── labels/
    ├── a.txt
    └── b.txt
```

Each non-empty label line is:

```text
class_id x_center y_center width height
```

- `class_id` is a zero-based integer index into `classes.txt`.
- Coordinates are normalized floats in `[0, 1]` relative to image width/height.
- `x_center`, `y_center`, `width`, and `height` describe the center-format box. Convert to COCO as `x_min=(x_center-width/2)*image_width`, `y_min=(y_center-height/2)*image_height`, `bbox_width=width*image_width`, `bbox_height=height*image_height`.
- A line such as `0 0.50 0.50 0.25 0.40` is valid only if the derived corners remain inside `[0, 1]`.
- Do not add a background row to `classes.txt`.
- Decide whether missing label files mean an error or a negative image. The bundled skeleton converter treats missing label files as errors unless `--allow-missing-labels` is set.

Use the bundled converter for small, auditable conversions:

```bash
python scripts/convert_yolo_txt_to_coco_skeleton.py YOLO_ROOT --out annotations/result.json --category-id-start 0
```

## LabelMe rectangles

MMYOLO's custom-dataset workflow can create or consume LabelMe JSON labels. The distilled contract is:

- One LabelMe JSON per image, usually named after the image stem.
- Detection conversion expects rectangle shapes for bounding boxes. Unsupported shape types must be handled intentionally; do not silently train on a partially converted dataset.
- The converter's class map is `class_with_id.txt`, one line per class in `id class_name` form, typically starting at `1`.
- Generated COCO annotations use `imageHeight`, `imageWidth`, `imagePath`, rectangle points, `category_id`, bbox, area, and a rectangle segmentation polygon.

After any LabelMe-to-COCO conversion, validate the COCO JSON and visually inspect a small sample before training.

## VOC layout

MMYOLO's `YOLOv5VOCDataset` wraps MMDetection's VOC dataset with the same batch-shape policy support used by the COCO wrapper. A typical VOC config uses:

```python
dataset=dict(
    type='YOLOv5VOCDataset',
    data_root='data/VOCdevkit/',
    ann_file='VOC2007/ImageSets/Main/trainval.txt',
    data_prefix=dict(sub_data_root='VOC2007/'))
```

For VOC 2007+2012 training, configs may use repeated or concatenated datasets with different `ann_file` and `sub_data_root` values. Keep `data_root` at the shared `VOCdevkit` directory and let `sub_data_root` select each year.

## DOTA layout

DOTA is used for rotated detection and needs additional dependencies such as rotated-detection dataset support and image-splitting dependencies. A raw DOTA-style root commonly contains:

```text
DOTA_ROOT/
├── train/
│   ├── images/
│   └── labelTxt-v1.0/
├── val/
│   ├── images/
│   └── labelTxt-v1.0/
└── test/
    └── images/
```

The split result used by rotated configs is commonly:

```text
SPLIT_DOTA_ROOT/
├── trainval/
│   ├── images/
│   └── annfiles/
└── test/
    ├── images/
    └── annfiles/
```

After splitting, point `data_root` at the split output. `YOLOv5DOTADataset` requires the rotated-detection package stack; if it is absent, dataset construction raises an import error instead of silently degrading.

## Cat and balloon examples

The cat object-detection quickstart uses a small COCO-style dataset:

```text
data/cat/
├── images/
├── labels/                  # LabelMe files when walking through annotation
├── annotations/
│   ├── annotations_all.json
│   ├── trainval.json
│   └── test.json
└── class_with_id.txt
```

The balloon examples are COCO-style instance-segmentation examples with `train`/`val` image directories and COCO JSON annotations. They are good templates for class/palette/evaluator wiring, but downloader commands are network-dependent and should be treated as references, not unattended runtime actions.

## MMYOLO config integration checklist

A custom COCO-style dataset needs coordinated config fields:

```python
data_root = 'data/custom/'
class_name = ('cat', )
num_classes = len(class_name)
metainfo = dict(classes=class_name, palette=[(220, 20, 60)])

train_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='annotations/trainval.json',
        data_prefix=dict(img='images/')))

val_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='annotations/test.json',
        data_prefix=dict(img='images/')))

test_dataloader = val_dataloader
val_evaluator = dict(ann_file=data_root + 'annotations/test.json')
test_evaluator = val_evaluator
```

Rules that prevent common failures:

- `metainfo` keys must be lowercase (`classes`, `palette`), because MMYOLO checks dataloader metainfo casing before train/test.
- `palette` length must be at least the number of classes used for visualization.
- `metainfo.classes` order should match the intended label order from the converter/class file. Category ids in COCO do not need to equal contiguous training labels, but ambiguity here causes confusing metrics and visualizations.
- For COCO metrics, evaluator `ann_file` must resolve to the actual annotation JSON. MMYOLO examples often concatenate `data_root + val_ann_file` while dataloaders use relative `ann_file` plus `data_root`.
- If changing class count, update the model head through the config-customization workflow as well as the dataset fields.
