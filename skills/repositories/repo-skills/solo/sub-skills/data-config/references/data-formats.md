# Dataset formats and validation

This reference turns the legacy dataset readers into an operating checklist.
The reader names and field shapes are the contract; directory names alone do
not make a dataset compatible.

## Format selection

| Dataset type | Annotation input | Native class | Typical task | Conversion boundary |
|---|---|---|---|---|
| COCO | One JSON object with `images`, `annotations`, `categories` | `CocoDataset` | boxes and instance masks | no conversion if schema is valid |
| Cityscapes | COCO JSON produced from Cityscapes labels | `CityscapesDataset` | boxes or instance masks | raw label conversion is external/deferred |
| PASCAL VOC | split text file plus per-image XML | `VOCDataset` | boxes | XML-to-internal conversion is optional |
| WIDER Face | split text file plus VOC-style XML | `WIDERFaceDataset` | face boxes | annotation preparation is external/deferred |
| Custom | internal list of image records, or a new reader | `CustomDataset` or subclass | boxes by default | custom reader/serializer is required for other targets |

An image record is not an annotation. `filename`, `width`, and `height` describe
an image. Detection instances are separate records carrying boxes and labels.
Instance segmentation carries one mask per instance, usually a polygon or RLE.
Semantic segmentation carries a separate per-pixel map, addressed through
`seg_prefix` and `seg_map`; it is not interchangeable with instance masks.

## COCO detection and instance segmentation

A minimal diagnostic JSON has this shape (values below are representative, not
a dataset to copy blindly):

```json
{
  "images": [
    {"id": 101, "file_name": "train/000101.jpg", "width": 640, "height": 480}
  ],
  "categories": [
    {"id": 1, "name": "widget", "supercategory": "object"}
  ],
  "annotations": [
    {
      "id": 9001, "image_id": 101, "category_id": 1,
      "bbox": [120, 80, 160, 100], "area": 16000,
      "iscrowd": 0
    }
  ]
}
```

Required checks:

- `images`, `annotations`, and `categories` are arrays; image and annotation
  IDs are unique; every annotation image/category ID resolves.
- Each image has a non-empty relative `file_name` and positive integer
  `width`/`height`. Resolve it below the configured image root and confirm the
  file exists. A symlink is acceptable only if its target exists.
- A box is `[x, y, width, height]`, with finite numeric values, positive width
  and height, and non-negative `area` when present. Check that its intended
  extent is plausible for the image; do not silently clip bad labels.
- Category IDs need not be contiguous in JSON, but the reader maps the order
  returned by the category table to labels beginning at one. Freeze category
  order and class names before training; changing it invalidates checkpoints
  and result interpretation.
- For instance masks, `segmentation` must be present for each mask target and
  be polygon data or an RLE object accepted by the COCO mask API. A valid box
  JSON is not a valid mask dataset.
- `iscrowd` annotations are treated as ignored boxes by this reader. Empty
  images may be filtered during training when `filter_empty_gt` is enabled.
  The reader also drops images whose smaller dimension is below 32 by default.

The reader derives a semantic-map filename by replacing `jpg` with `png` when
`with_seg=True`; this convention is separate from instance-mask segmentation.
If a custom image suffix or semantic-map naming rule is used, verify the
reader/config pair explicitly.

## Cityscapes boundary

The native Cityscapes class changes the class tuple to:

```python
('person', 'rider', 'car', 'truck', 'bus', 'train', 'motorcycle', 'bicycle')
```

It otherwise follows the COCO reader. The legacy setup expects a converted JSON
and matching `train`/`val` image roots. Raw Cityscapes polygons, label IDs,
train/val layout, and any flattening of nested image directories must be
converted outside this sub-skill. Do not claim that placing raw label files
under a directory is enough. After conversion, run the COCO checks plus a
class-set check against the eight names and verify every JSON `file_name`.

## PASCAL VOC XML

The standard layout is:

```text
<VOC root>/
  VOC2007/
    Annotations/<image-id>.xml
    JPEGImages/<image-id>.jpg
    ImageSets/Main/{train,val,trainval,test}.txt
```

A split file is a newline-separated list of image IDs, not JSON and not image
paths. Each XML needs:

```xml
<annotation>
  <size><width>640</width><height>480</height></size>
  <object>
    <name>widget</name>
    <difficult>0</difficult>
    <bndbox>
      <xmin>121</xmin><ymin>81</ymin>
      <xmax>279</xmax><ymax>179</ymax>
    </bndbox>
  </object>
</annotation>
```

The reader obtains `JPEGImages/<id>.jpg` and `Annotations/<id>.xml` under the
configured `img_prefix`. It maps XML names through the fixed 20-class VOC
vocabulary, infers year from a `VOC2007` or `VOC2012` prefix, and subtracts one
from parsed box coordinates for its internal representation. `difficult=1`
becomes ignored; a configured `min_size` can also move a box to ignored. Check
class spelling, year, coordinate convention, and case-sensitive filenames.

Combining VOC years uses parallel `ann_file` and `img_prefix` lists. Every pair
must point to the same index's split/root. A list of annotation files creates a
concatenated dataset; it does not merge or renumber XML IDs.

## WIDER Face XML

The reader expects a split list of image IDs and, beneath the selected train or
validation root, an `Annotations/<id>.xml` file. The XML includes `size`, an
optional/expected `folder`, and `object` entries whose class is `face` and
whose `bndbox` carries `xmin`, `ymin`, `xmax`, `ymax`. The image name is formed
from the ID and the XML folder, so validate the actual nested path, for example:

```text
<WIDER split root>/
  Annotations/<id>.xml
  <folder>/<id>.jpg
```

WIDER's config-era example uses `min_size=17` for training. The class has no
instance-mask contract. WIDER annotation generation and placement from the
original label source are intentionally outside the safe validator; validate
what is already local instead.

## Internal custom records

For JSON-compatible diagnostics, the internal list is:

```json
[
  {
    "filename": "images/a.jpg",
    "width": 640,
    "height": 480,
    "ann": {
      "bboxes": [[10, 20, 100, 120]],
      "labels": [1],
      "bboxes_ignore": [],
      "labels_ignore": []
    }
  }
]
```

Every record needs `filename`, `width`, and `height`; `ann` may be omitted for
inference, but training needs `bboxes` and `labels`. Box arrays must have shape
`N x 4`, label arrays length `N`, and ignored arrays must agree with each other.
The runtime documentation describes NumPy arrays (`float32` boxes and `int64`
labels); a JSON list is useful for schema inspection but may need a loader or
serializer that converts it to arrays. Pickle output from a conversion tool is
not inspected by the stdlib validator.

For masks, add a deliberate `masks` field and implement/choose a reader that
knows its representation. For semantic maps, provide `seg_map` and configure
`seg_prefix` plus `LoadAnnotations(with_seg=True)`. Adding arbitrary keys to a
custom JSON file does not cause the pipeline to load them.

## Paths, roots, and symlinks

The effective path rules are:

1. If `data_root` is set, each relative `ann_file`, `img_prefix`, `seg_prefix`,
   and proposal path is joined to it.
2. A relative image `filename` is joined to `img_prefix`; with a null prefix,
   it is used as supplied.
3. Absolute paths bypass those joins. They are valid for local debugging but
   make a config non-portable and should be recorded as an assumption.
4. A dataset root symlink is fine when its target exists. A dangling symlink,
   wrong split root, or symlink that resolves to a different split is a path
   failure, not an annotation conversion problem.

Keep image and annotation roots explicit in the handoff. The validator never
creates or changes links and never treats a directory listing as proof that
all manifest references resolve.

## Read-only validator

The bundled `scripts/validate_dataset_manifest.py` uses only the Python
standard library. Examples:

From the generated skill root, run the bundled helper with explicit user paths:

```bash
python sub-skills/data-config/scripts/validate_dataset_manifest.py \
  --format coco --ann <COCO_JSON> --image-root <IMAGE_ROOT>

python sub-skills/data-config/scripts/validate_dataset_manifest.py \
  --format voc --ann <VOC_SPLIT_OR_MANIFEST> --dataset-root <VOC_ROOT>

python sub-skills/data-config/scripts/validate_dataset_manifest.py \
  --format custom --ann <CUSTOM_RECORDS_JSON> --image-root <IMAGE_ROOT>
```

For VOC, `--dataset-root` should contain `Annotations` and `JPEGImages`; for
WIDER it should be the selected split root. Use `--strict` to promote warnings
(such as omitted image-root checks) to failures. The report is diagnostic only:
it does not decode pixels, invoke pycocotools, instantiate a dataset, or prove
CUDA/MMCV compatibility.
