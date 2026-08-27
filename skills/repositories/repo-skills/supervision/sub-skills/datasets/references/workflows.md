# Dataset workflows

Use these patterns after confirming the source format in
[data formats](data-formats.md). Keep dataset operations separate from metrics,
model inference, and rich annotation styling; route those parts to sibling
sub-skills when needed.

## Install and import check

The base package is enough for dataset loading and conversion:

```bash
pip install supervision
```

In Python, prefer public top-level imports:

```python
import supervision as sv
```

If a workflow later evaluates predictions, install the metrics extra and route
metric-specific questions to [metrics](../../metrics/SKILL.md):

```bash
pip install "supervision[metrics]"
```

## Load a detection dataset

Choose the loader that matches the annotation files. For large datasets, pass
`show_progress=True` when the method supports it.

```python
import supervision as sv

# YOLO boxes, segmentation polygons, or OBBs.
yolo_ds = sv.DetectionDataset.from_yolo(
    images_directory_path="data/train/images",
    annotations_directory_path="data/train/labels",
    data_yaml_path="data/data.yaml",
    force_masks=False,
    is_obb=False,
    show_progress=True,
)

# COCO JSON.
coco_ds = sv.DetectionDataset.from_coco(
    images_directory_path="data/train/images",
    annotations_path="data/train/annotations.json",
    force_masks=False,
    show_progress=True,
    use_iscrowd=True,
)

# Pascal VOC XML.
voc_ds = sv.DetectionDataset.from_pascal_voc(
    images_directory_path="data/train/images",
    annotations_directory_path="data/train/annotations",
    force_masks=False,
    show_progress=True,
)

# LabelMe per-image JSON.
labelme_ds = sv.DetectionDataset.from_labelme(
    images_directory_path="data/train/images",
    annotations_directory_path="data/train/annotations",
    force_masks=False,
)

# CreateML single JSON.
createml_ds = sv.DetectionDataset.from_createml(
    images_directory_path="data/train/images",
    annotations_path="data/train/annotations.json",
    show_progress=True,
)
```

After loading, inspect classes and a small number of samples before converting:

```python
print(dataset.classes)
print(len(dataset))
image_path, image, detections = dataset[0]
print(image_path, image.shape, len(detections))
print(detections.class_id)
print(detections.data.get("class_name"))
```

If indexing fails with an image read error, see
[troubleshooting](troubleshooting.md#image-read-errors).

## Split into train, validation, and test

`split()` returns exactly two datasets. Split twice for train/valid/test.
`random_state` makes shuffled splits deterministic and does not mutate the
source order.

```python
train_ds, remainder_ds = dataset.split(
    split_ratio=0.8,
    random_state=42,
    shuffle=True,
)
valid_ds, test_ds = remainder_ds.split(
    split_ratio=0.5,
    random_state=42,
    shuffle=True,
)

assert len(train_ds) + len(valid_ds) + len(test_ds) == len(dataset)
```

Use `shuffle=False` when the original ordering encodes a time sequence or an
already stratified export.

## Merge datasets safely

`DetectionDataset.merge([...])` combines classes using a sorted union and remaps
all annotation `class_id` values. It refuses duplicate image paths and refuses to
mix path-backed lazy datasets with dict-backed in-memory datasets.

```python
merged = sv.DetectionDataset.merge([train_ds, valid_ds, test_ds])

print(merged.classes)
for image_path, detections in merged.annotations.items():
    print(image_path, detections.class_id, detections.data.get("class_name"))
```

Before export, check for basename or stem collisions if the source images came
from different directories:

```python
from pathlib import Path

basenames = [Path(path).name.casefold() for path in merged.image_paths]
if len(basenames) != len(set(basenames)):
    raise ValueError("Rename images before exporting to a flat output directory")
```

Exporters also preflight collisions for their own flat output files, but doing a
quick pre-check lets you choose better names before a long conversion.

## Convert YOLO to COCO

```python
import supervision as sv

source = sv.DetectionDataset.from_yolo(
    images_directory_path="source/images",
    annotations_directory_path="source/labels",
    data_yaml_path="source/data.yaml",
    force_masks=False,
)

next_image_id, next_annotation_id = source.as_coco(
    images_directory_path="converted/images",
    annotations_path="converted/annotations.json",
    show_progress=True,
)

print(next_image_id, next_annotation_id)
```

COCO exports write one-indexed category ids while keeping internal
`Detections.class_id` zero-based. Verify class identity by reading
`converted_ds.classes` and internal ids after a round-trip rather than by
comparing raw COCO `category_id` values to internal ids.

## Export multiple splits to COCO with global ids

`as_coco()` returns the first unused image and annotation ids. Chain those values
when exporting train/valid/test splits that may later be combined.

```python
next_image_id, next_annotation_id = train_ds.as_coco(
    images_directory_path="out/train/images",
    annotations_path="out/train/annotations.json",
)
next_image_id, next_annotation_id = valid_ds.as_coco(
    images_directory_path="out/valid/images",
    annotations_path="out/valid/annotations.json",
    starting_image_id=next_image_id,
    starting_annotation_id=next_annotation_id,
)
test_ds.as_coco(
    images_directory_path="out/test/images",
    annotations_path="out/test/annotations.json",
    starting_image_id=next_image_id,
    starting_annotation_id=next_annotation_id,
)
```

Starting ids must be >= 1.

## Preserve masks during conversion

Use `force_masks=True` when the target workflow requires masks even for
box-shaped annotations. For YOLO, COCO, and Pascal VOC exports, the
`min_image_area_percentage`, `max_image_area_percentage`, and
`approximation_percentage` arguments control mask-to-polygon filtering and
simplification.

```python
seg_ds = sv.DetectionDataset.from_coco(
    images_directory_path="seg/images",
    annotations_path="seg/annotations.json",
    force_masks=True,
)

seg_ds.as_yolo(
    images_directory_path="yolo-seg/images",
    annotations_directory_path="yolo-seg/labels",
    data_yaml_path="yolo-seg/data.yaml",
    min_image_area_percentage=0.0,
    max_image_area_percentage=1.0,
    approximation_percentage=0.0,
)
```

COCO can output polygon or RLE segmentations depending on mask topology and
`iscrowd`. LabelMe exports masks as polygon approximations and may shift boxes by
about a pixel after re-import.

## Preserve YOLO OBB corners

Load YOLO OBB labels with `is_obb=True`; corner coordinates are stored in
`detections.data["xyxyxyxy"]`, the value of `ORIENTED_BOX_COORDINATES`. Export
with `is_obb=True` to write the nine-token YOLO OBB line. Do not rely on masks in
OBB mode.

```python
obb_ds = sv.DetectionDataset.from_yolo(
    images_directory_path="obb/images",
    annotations_directory_path="obb/labels",
    data_yaml_path="obb/data.yaml",
    is_obb=True,
)

for _, _, detections in obb_ds:
    corners = detections.data.get("xyxyxyxy")
    if len(detections) and corners is None:
        raise ValueError("OBB detections are missing xyxyxyxy corner data")

obb_ds.as_yolo(
    images_directory_path="obb-out/images",
    annotations_directory_path="obb-out/labels",
    data_yaml_path="obb-out/data.yaml",
    is_obb=True,
)
```

If you synthesize OBB detections yourself, build `detections.data["xyxyxyxy"]` as
a NumPy array with shape `(N, 4, 2)` in pixel coordinates before export. For
non-OBB workflows, route OBB geometry, NMS/NMM, and inference slicing questions
to [detection-and-zones](../../detection-and-zones/SKILL.md).

## Iterate and process annotations

For dataset-focused processing, iterate the dataset, transform annotations, and
construct a new `DetectionDataset` with the same path keys. Keep `class_id`
integer and in range so `"class_name"` can be repopulated.

```python
from dataclasses import replace
import numpy as np
import supervision as sv

new_annotations = {}
for image_path, image, detections in dataset:
    if detections.confidence is None:
        new_annotations[image_path] = detections
    else:
        keep = detections.confidence >= 0.25
        new_annotations[image_path] = detections[keep]

processed = sv.DetectionDataset(
    classes=dataset.classes,
    images=dataset.image_paths,
    annotations=new_annotations,
)
```

When a task is primarily about `Detections` filtering, NMS, masks, or model
adapters rather than dataset I/O, use
[detection-and-zones](../../detection-and-zones/SKILL.md).

## Quick dataset visualization

A minimal dataset inspection loop can build labels from `"class_name"` metadata.
For styling, composition, color lookup, or video annotation, route to
[annotators](../../annotators/SKILL.md).

```python
import supervision as sv

box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

preview_images = []
for index in range(min(16, len(dataset))):
    _, image, detections = dataset[index]
    class_names = detections.data.get("class_name")
    if class_names is None and detections.class_id is not None:
        class_names = [dataset.classes[class_id] for class_id in detections.class_id]
    labels = list(class_names) if class_names is not None else None

    annotated = box_annotator.annotate(image.copy(), detections)
    annotated = label_annotator.annotate(annotated, detections, labels=labels)
    preview_images.append(annotated)
```

Low-level image grids, saving previews, and OpenCV/Pillow details belong to
[media-utils](../../media-utils/SKILL.md).

## Load and export classification folders

```python
import supervision as sv

classification_ds = sv.ClassificationDataset.from_folder_structure(
    root_directory_path="classification/train",
    show_progress=True,
)
print(classification_ds.classes)

train_cls, test_cls = classification_ds.split(
    split_ratio=0.8,
    random_state=42,
    shuffle=True,
)
train_cls.as_folder_structure("classification-out/train", show_progress=True)
test_cls.as_folder_structure("classification-out/test", show_progress=True)
```

The loader ignores hidden entries, root-level files, nested directories, and
unsupported suffixes. Export writes each image basename into the class folder
selected by the annotation's top class.

## Version-pinning workflow

The dataset API is documented as fluid. For reproducible research or production
conversion scripts, pin the `supervision` version used to write and verify the
script, and rerun a tiny load/export round-trip after changing versions.

```text
supervision==0.31.0.dev0
```

At minimum, smoke test:

1. Load one sample per source format used by the project.
2. Check `dataset.classes`, `len(dataset)`, and one non-empty `detections.class_id`.
3. Export to the target format in a temporary directory.
4. Reload the export and compare class names and detection counts.
5. For masks or OBBs, compare mask IoU or `"xyxyxyxy"` corner arrays on a small
   fixture rather than assuming bit-exact round-trips across all formats.
