# Dataset, annotation, and result contracts

The repository evaluates `bbox` detections through `pycocotools`. The safest
way to use a custom dataset is to convert it to the COCO Object Detection
format and validate it before invoking TensorRT.

## Image directory contract

Both evaluators accept a directory, not a manifest. They select every filename
whose name ends with lowercase `.jpg` and derive the image ID as follows:

```python
image_id = int(jpg.split('.')[0].split('_')[-1])
```

Consequences:

- `COCO_val2017_000000123456.jpg` maps to integer `123456`.
- The final underscore-separated token must be decimal digits.
- The extension must be exactly lowercase `.jpg` for these scripts.
- The directory should contain only the intended split. Extra JPEGs cause
  inference to run on IDs that may not be in the annotation file; other image
  extensions are silently ignored.
- The scripts do not verify `cv2.imread()` returned a valid image and do not
  compare the directory's IDs with the annotation IDs before inference.
- The result evaluator uses all sorted image IDs from the ground truth, even if
  the result file has no detections for some of them. Missing detections can
  lower recall; extra or unknown IDs can make `loadRes()` fail or invalidate the
  comparison.

A custom dataset may use any prefix, but retain the final numeric image ID
convention unless the evaluator itself is intentionally modified and tested.

## COCO annotation JSON

At minimum, the annotation document should be a JSON object with:

```json
{
  "images": [
    {"id": 123456, "file_name": "COCO_val2017_000000123456.jpg",
     "width": 640, "height": 480}
  ],
  "annotations": [
    {"id": 1, "image_id": 123456, "category_id": 1,
     "bbox": [10.0, 20.0, 100.0, 80.0], "area": 8000.0,
     "iscrowd": 0}
  ],
  "categories": [
    {"id": 1, "name": "person", "supercategory": "person"}
  ]
}
```

For COCO detection evaluation, each ground-truth annotation needs a valid
`image_id` and `category_id`; `bbox` is `[x, y, width, height]` in pixel
coordinates with positive width and height. Standard COCO files also carry
`area`, `iscrowd`, and annotation IDs. `pycocotools.COCO` is the authoritative
parser for a real run; the bundled checker is intentionally smaller and only
checks the layout invariants it can safely establish without external
packages.

The `images[].id` values must be unique. Category IDs must be unique and must
be the IDs used by both ground truth and results. Standard COCO category IDs
are not a dense 0–79 range: several numeric IDs are unused.

## Detection result JSON

Both scripts write a JSON array. Each detection has exactly the operational
fields consumed by `COCO.loadRes()`:

```json
[
  {
    "image_id": 123456,
    "category_id": 1,
    "bbox": [10.0, 20.0, 100.0, 80.0],
    "score": 0.97
  }
]
```

Required invariants:

- `image_id` is an integer present in `images[].id`.
- `category_id` is an integer present in `categories[].id`.
- `bbox` has four finite numeric values `[x, y, width, height]`.
- `width` and `height` are positive; the repository's generated values are
  derived from detector corners with `x2 - x1 + 1` and `y2 - y1 + 1`.
- `score` is a finite numeric confidence. It is written as a float.
- Empty detections are represented by `[]`, which is valid JSON, but
  `COCO.loadRes()` behavior for an empty result set should be checked with the
  installed `pycocotools` version before a full run.

The evaluators use a very low detector threshold (`0.01`) so that COCOeval can
rank detections. This is not the same as the display-demo defaults, which often
use a higher confidence threshold. YOLO additionally performs plugin-side
postprocessing and per-class NMS before serialization.

## SSD and YOLO category semantics

SSD COCO models produce category IDs compatible with the COCO annotation
vocabulary used by `instances_val2017.json`. The evaluator writes the detector
class directly.

YOLO's model output uses the contiguous 0–79 ordering in
`utils/yolo_classes.COCO_CLASSES_LIST`. Standard COCO result IDs use the
repository's `yolo_cls_to_ssd` mapping, for example raw YOLO `0` (person) maps
to COCO ID `1`, raw `11` (stop sign) maps to COCO ID `13`, and the final raw
class maps to COCO ID `90`. Do not replace this list with a simple `class + 1`
rule.

`--non_coco` means “do not translate”; it does not mean “use another known
COCO format.” Use it only when `categories[].id` intentionally equals raw YOLO
indices and the annotations describe the same class order. With a custom class
count, `category_num` and the annotation category vocabulary must be explicit.

## Coordinate and preprocessing semantics

Detector utilities return corner boxes in original-image pixels:

```text
[x1, y1, x2, y2]
```

The evaluator converts them to:

```text
[x1, y1, x2 - x1 + 1, y2 - y1 + 1]
```

SSD TensorRT uses a fixed `(300, 300)` input and normalizes the source image to
RGB `[-1, 1]`; TensorFlow SSD uses normalized TensorFlow output boxes. YOLO
uses the engine input shape, RGB `[0, 1]`, optional 127-valued letterbox
padding, inverse padding correction, and clipping to the original dimensions.
Ground truth remains in the original image coordinate system.

A preprocessing or coordinate-system mismatch can preserve valid-looking JSON
while making AP collapse. Compare one hand-inspected image and box before
running the full split.

## Safe fixture check

Use a tiny local directory and JSON files to validate filename parsing, ID
membership, categories, bbox dimensions, and scores:

```bash
python3 skills/disco/tensorrt-demos/sub-skills/evaluation/scripts/validate-coco-eval-layout.py \
  --images-dir ./tiny/images \
  --annotations ./tiny/instances.json \
  --results ./tiny/results.json
```

This helper is not a COCO converter and does not validate every optional COCO
field. It must never be used as evidence that a real dataset has been loaded
or that a model has been evaluated.
