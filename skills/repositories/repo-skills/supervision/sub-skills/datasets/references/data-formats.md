# Dataset data formats

This reference summarizes the runtime schemas consumed and produced by
`supervision` dataset APIs. Use it to choose the right loader/exporter and to
preserve class ids, class names, masks, and OBB metadata across conversions.

## Core containers

| Container | Purpose | Important fields |
| --- | --- | --- |
| `sv.DetectionDataset` | Detection/segmentation/OBB datasets | `classes: list[str]`, `image_paths: list[str]`, `annotations: dict[str, sv.Detections]` |
| `sv.ClassificationDataset` | Classification datasets | `classes: list[str]`, `image_paths: list[str]`, `annotations: dict[str, sv.Classifications]` |

Detection datasets are path-first in 0.31.0.dev0. A dict of in-memory image
arrays is still accepted but deprecated; prefer `images=["path/to/image.jpg"]`.
The constructor requires `set(images) == set(annotations)` and deep-copies
annotation objects. For every detection with integer `class_id`, it populates
`detections.data["class_name"]` from `dataset.classes`.

`DetectionDataset` iteration and indexing yield:

```python
image_path, image_bgr, detections = dataset[index]
for image_path, image_bgr, detections in dataset:
    ...
```

Lazy image reads use the installed or fallback OpenCV backend. If an image path
cannot be read, indexing or iteration raises `ValueError`.

## Public API matrix

| Format | Load | Export | Notes |
| --- | --- | --- | --- |
| YOLO | `sv.DetectionDataset.from_yolo(images_directory_path, annotations_directory_path, data_yaml_path, force_masks=False, is_obb=False, show_progress=False)` | `dataset.as_yolo(images_directory_path=None, annotations_directory_path=None, data_yaml_path=None, min_image_area_percentage=0.0, max_image_area_percentage=1.0, approximation_percentage=0.0, is_obb=False, show_progress=False)` | Boxes, polygons, and optional OBBs. |
| COCO | `sv.DetectionDataset.from_coco(images_directory_path, annotations_path, force_masks=False, show_progress=False, *, use_iscrowd=True)` | `dataset.as_coco(images_directory_path=None, annotations_path=None, min_image_area_percentage=0.0, max_image_area_percentage=1.0, approximation_percentage=0.0, starting_image_id=1, starting_annotation_id=1, show_progress=False)` | Export returns `(next_image_id, next_annotation_id)`. |
| Pascal VOC | `sv.DetectionDataset.from_pascal_voc(images_directory_path, annotations_directory_path, force_masks=False, show_progress=False)` | `dataset.as_pascal_voc(images_directory_path=None, annotations_directory_path=None, min_image_area_percentage=0.0, max_image_area_percentage=1.0, approximation_percentage=0.0, show_progress=False)` | XML boxes and optional polygons. |
| LabelMe | `sv.DetectionDataset.from_labelme(images_directory_path, annotations_directory_path, force_masks=False)` | `dataset.as_labelme(images_directory_path=None, annotations_directory_path=None)` | Per-image JSON; rectangle and polygon shapes only. |
| CreateML | `sv.DetectionDataset.from_createml(images_directory_path, annotations_path, show_progress=False)` | `dataset.as_createml(images_directory_path=None, annotations_path=None, show_progress=False)` | Single JSON list; axis-aligned boxes only. |
| Classification folders | `sv.ClassificationDataset.from_folder_structure(root_directory_path, show_progress=False)` | `dataset.as_folder_structure(root_directory_path, show_progress=False)` | One class directory per label. |

## Class ids and metadata

Supervision uses zero-based internal `Detections.class_id` values indexing
`dataset.classes`. During dataset construction:

- `class_id` must be an integer NumPy array when present.
- Every `class_id` must satisfy `0 <= class_id < len(dataset.classes)`.
- `detections.data["class_name"]` is populated using the constant
  `CLASS_NAME_DATA_FIELD` whose value is `"class_name"`.

During `DetectionDataset.merge([...])`, the merged class list is the sorted union
of all input class names. Every input dataset's `class_id` values are remapped to
that sorted union, and the constructed merged dataset refreshes `"class_name"`
metadata. Do not assume class id `0` still means the same class after a merge;
read `merged.classes` and check `detections.class_id`.

## YOLO schema

Expected input layout:

```text
dataset/
  data.yaml
  images/
    image_001.jpg
  labels/
    image_001.txt
```

`data.yaml` must contain `names` as either a list or a dict. Numeric dict keys
are sorted numerically; non-numeric dict keys are sorted lexicographically. Mixed
numeric and non-numeric keys are rejected.

YOLO annotation lines are normalized to image width/height:

| Mode | Line shape | Internal result |
| --- | --- | --- |
| Box | `class_id x_center y_center width height` | `Detections.xyxy`; no mask unless `force_masks=True`, where boxes become rectangular masks. |
| Segmentation | `class_id x1 y1 x2 y2 ...` with more than 5 tokens | `Detections.xyxy`; `Detections.mask` is inferred unless `is_obb=True`. |
| OBB | `class_id x1 y1 x2 y2 x3 y3 x4 y4` with `is_obb=True` | Axis-aligned enclosing `xyxy` plus `detections.data["xyxyxyxy"]` with shape `(N, 4, 2)`. |

Use the constant `ORIENTED_BOX_COORDINATES` for OBB data; its value is
`"xyxyxyxy"`. When exporting with `is_obb=True`, every non-empty detection must
carry `detections.data["xyxyxyxy"]` with shape `(N, 4, 2)`. Masks are ignored in
OBB mode. Background images with no label file load as `Detections.empty()` and
export an empty `.txt` file.

## COCO schema

Expected input layout:

```text
dataset/
  images/
    image_001.jpg
  annotations.json
```

The COCO JSON uses `categories`, `images`, and `annotations` entries. Input
`images[].file_name` values are resolved beneath `images_directory_path`; entries
that resolve to the images directory itself, a directory, or a path outside the
images directory are rejected. Duplicate canonical image paths are also rejected.

Class-index rules:

- COCO `categories` are sorted by their on-disk `id` to derive
  `dataset.classes`.
- COCO `annotation.category_id` values are remapped to zero-based internal
  `Detections.class_id` values when loading.
- `as_coco()` writes COCO `categories[].id` and `annotations[].category_id` as
  one-indexed values (`internal_class_id + 1`).
- Legacy zero-indexed COCO category files still load correctly, but new exports
  should be one-indexed.

Mask and metadata rules:

- If `force_masks=True`, masks are decoded for every annotation; missing
  segmentation becomes an empty mask aligned with the object.
- If `force_masks=False`, masks are still decoded when a segmentation field is
  present for an image.
- `use_iscrowd=True` stores `iscrowd` and `area` in `Detections.data`; set it to
  `False` to omit that metadata.
- When masks are not decoded, raw segmentation is preserved under
  `detections.data["coco_raw_segmentation"]` for lossless re-export.
- On export, simple masks are written as polygon segmentations. Masks with holes
  or multiple disconnected components are inferred as `iscrowd=1` and written as
  uncompressed RLE unless `detections.data["iscrowd"]` forces polygon behavior.
- `as_coco()` returns the next unused image and annotation ids. Feed them into
  the next split's `starting_image_id` and `starting_annotation_id` to keep ids
  globally unique across train/valid/test files.

## Pascal VOC schema

Expected input layout:

```text
dataset/
  images/
    image_001.jpg
  annotations/
    image_001.xml
```

Pascal VOC image loading currently scans `.jpg`, `.jpeg`, and `.png` images and
looks for an XML file with the same stem. Missing XML files produce empty
`Detections` for that image.

On disk, Pascal VOC boxes and polygons are one-indexed. Supervision converts
them to zero-based pixel coordinates internally and converts back to one-indexed
coordinates on export without mutating the source `Detections` arrays.

Required XML shape:

```xml
<annotation>
  <object>
    <name>dog</name>
    <bndbox>
      <xmin>1</xmin><ymin>1</ymin><xmax>10</xmax><ymax>10</ymax>
    </bndbox>
    <polygon>
      <x1>1</x1><y1>1</y1>
      <x2>10</x2><y2>1</y2>
      <x3>10</x3><y3>10</y3>
    </polygon>
  </object>
</annotation>
```

`<polygon>` is optional. If any object has a polygon, or `force_masks=True`, the
loader returns masks aligned to all objects. Background images with no `<object>`
entries keep an empty integer `class_id`; with `force_masks=True` they carry an
empty mask array with shape `(0, H, W)`.

## LabelMe schema

Expected input layout:

```text
dataset/
  images/
    image_001.jpg
  annotations/
    image_001.json
```

Each LabelMe JSON should include `imagePath`, `imageWidth`, `imageHeight`, and a
`shapes` list. Only `rectangle` and `polygon` shapes are imported; unsupported
shape types are skipped with a warning.

Shape constraints:

- `rectangle`: at least two points; loaded as `xyxy`.
- `polygon`: at least three points; loaded as a mask and `xyxy`.
- Every supported shape needs `label` and `points`.
- If masks are needed because a polygon is present or `force_masks=True`,
  `imageWidth` and `imageHeight` must be present and non-zero.

The loader strips directory components from `imagePath` and joins only the
basename to `images_directory_path`, neutralizing annotation-driven traversal.
It rejects empty, `.`/`..`, and duplicate image basenames. Classes are inferred
from all supported labels and sorted globally.

Export writes one JSON per image. Masked detections become one or more polygon
shapes; box-only detections, empty masks, and masks that produce no contour fall
back to rectangle shapes so detections are not silently dropped. Mask round-trips
are approximate because polygons are contour approximations.

## CreateML schema

Expected input layout:

```text
dataset/
  images/
    image_001.jpg
  annotations.json
```

The annotation file root must be a JSON list. Each item contains an image entry
and optional annotations:

```json
[
  {
    "image": "image_001.jpg",
    "annotations": [
      {
        "label": "dog",
        "coordinates": {"x": 50, "y": 50, "width": 20, "height": 10}
      }
    ]
  }
]
```

`coordinates.x` and `coordinates.y` are pixel-space box centers. `width` and
`height` are box dimensions. The loader converts them to internal `xyxy` boxes.
Classes are inferred from labels and sorted globally; classes with no boxes
anywhere in the file do not appear in `dataset.classes`.

The `image` value is resolved and validated beneath `images_directory_path`.
Traversal, absolute paths outside the image directory, directory targets, and
duplicate canonical image paths are rejected. CreateML export writes only the
image basename in each JSON item and rejects basename collisions before writing.

## Classification folder structure

Expected input layout:

```text
root/
  cats/
    cat_001.jpg
  dogs/
    dog_001.jpg
```

`ClassificationDataset.from_folder_structure(root)` creates sorted class names
from non-hidden first-level directories. It ignores hidden entries, root-level
files, nested directories, and unsupported image suffixes. Supported image
extensions include `.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, `.tiff`, and
`.webp`.

Each image receives `sv.Classifications(class_id=np.array([class_id]))`.
`as_folder_structure(root)` creates one directory per class and writes each image
basename into the folder selected by the annotation's top class. If
`annotation.confidence` is present, it uses `annotation.get_top_k(1)`; otherwise
it uses `annotation.class_id[0]`.
