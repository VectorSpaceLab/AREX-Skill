# Objects and exports

This reference covers the SAHI object model used after a detector or dataset workflow has already produced boxes, masks, scores, or `PredictionResult` objects. It is intentionally focused on object construction and conversion, not on running prediction or dataset-scale COCO tooling.

## Coordinate and shape conventions

| Value | Shape | Meaning | Notes |
| --- | --- | --- | --- |
| Core/VOC bbox | `[minx, miny, maxx, maxy]` | Absolute pixel corners used by `BoundingBox`, `ObjectAnnotation`, and `ObjectPrediction` constructors. | Width is `maxx - minx`; height is `maxy - miny`. Ensure `maxx > minx` and `maxy > miny` before downstream export. |
| COCO bbox | `[x, y, width, height]` | Export/import format for COCO annotations and predictions. | `ObjectAnnotation.from_coco_bbox()` converts this to core/VOC internally. |
| COCO segmentation | `[[x1, y1, x2, y2, ...], ...]` | Polygon list for masks. | Each polygon needs at least three points. RLE dict segmentations are not accepted by these low-level objects. |
| Full shape | `[height, width]` | Complete image canvas for masks. | Required for `Mask` and segmentation-backed `ObjectAnnotation`/`ObjectPrediction`. |
| Shift amount | `[shift_x, shift_y]` | Offset from a slice back to the full image. | `get_shifted_*()` applies this offset and returns an unshifted object. |
| Image size on `PredictionResult` | `(image_width, image_height)` | Derived from the PIL image stored in the result. | Input image can be PIL, path string, or RGB HWC numpy array. |

## Core object quick table

| Object | Constructor / common factory | Primary fields | Conversion helpers |
| --- | --- | --- | --- |
| `BoundingBox` | `BoundingBox(box, shift_amount=(0, 0))` | Immutable `box`, `minx`, `miny`, `maxx`, `maxy`, `area`, `shift_x`, `shift_y`. | `to_xyxy()`, `to_voc_bbox()`, `to_xywh()`, `to_coco_bbox()`, `get_expanded_box()`, `get_shifted_box()`. |
| `Category` | `Category(id: int, name: str)` | Immutable `id` and `name`. | Type validation only. |
| `Mask` | `Mask(segmentation, full_shape, shift_amount=[0, 0])` | `segmentation`, `bool_mask`, `shape`, `full_shape`, `shift_amount`. | `from_bool_mask()`, `from_float_mask()`, `get_shifted_mask()`. |
| `ObjectAnnotation` | `ObjectAnnotation(bbox=..., segmentation=..., category_id=..., category_name=..., shift_amount=..., full_shape=...)` | `bbox`, optional `mask`, `category`, `merged`. | `from_coco_bbox()`, `from_coco_segmentation()`, `from_coco_annotation_dict()`, `from_bool_mask()`, `from_shapely_annotation()`, `from_imantics_annotation()`, `to_coco_annotation()`, `to_coco_prediction()`, `to_shapely_annotation()`, `to_imantics_annotation()`, `get_shifted_object_annotation()`. |
| `PredictionScore` | `PredictionScore(value)` | Numeric `.value`; numpy scalar arrays are converted to Python floats. | `is_greater_than_threshold()`, comparisons with ints/floats. |
| `ObjectPrediction` | `ObjectPrediction(bbox=..., category_id=..., category_name=..., segmentation=..., score=..., shift_amount=..., full_shape=...)` | Inherits annotation fields and adds `score`. | `to_coco_prediction(image_id=None)`, `to_fiftyone_detection(image_height, image_width)`, `get_shifted_object_prediction()`. |
| `PredictionResult` | `PredictionResult(object_prediction_list, image, durations_in_seconds={})` | PIL `.image`, `.image_width`, `.image_height`, `.object_prediction_list`, `.durations_in_seconds`. | `export_visuals()`, `to_coco_annotations()`, `to_coco_predictions(image_id=None)`, `to_imantics_annotations()`, `to_fiftyone_detections()`. |

## Construct boxes, masks, annotations, and predictions

```python
import numpy as np
from PIL import Image
from sahi.annotation import BoundingBox, Category, Mask, ObjectAnnotation
from sahi.prediction import ObjectPrediction, PredictionResult, PredictionScore

# Core objects use absolute [minx, miny, maxx, maxy] coordinates.
bbox = BoundingBox([10, 20, 30, 50])
assert bbox.to_xywh() == [10, 20, 20, 30]
assert bbox.area == 600

category = Category(id=3, name="vehicle")
score = PredictionScore(np.array(0.91))
assert score.value == 0.91

# Bbox-backed annotation/prediction.
annotation = ObjectAnnotation(
    bbox=[10, 20, 30, 50],
    category_id=category.id,
    category_name=category.name,
    full_shape=[80, 100],
)
prediction = ObjectPrediction(
    bbox=[10, 20, 30, 50],
    category_id=category.id,
    category_name=category.name,
    score=score.value,
    full_shape=[80, 100],
)

# Segmentation-backed objects need full_shape=[height, width].
segmentation = [[10, 20, 30, 20, 30, 50, 10, 50]]
mask = Mask(segmentation=segmentation, full_shape=[80, 100])
seg_prediction = ObjectPrediction(
    segmentation=segmentation,
    category_id=4,
    category_name="mask-object",
    score=0.82,
    full_shape=[80, 100],
)
assert seg_prediction.bbox.to_xyxy() == [10, 20, 30, 50]
assert mask.bool_mask.shape == (80, 100)

image = Image.new("RGB", (100, 80), "white")
result = PredictionResult([prediction, seg_prediction], image=image)
```

## Import from COCO-style objects

Use the factory matching the incoming coordinate format:

```python
from sahi.annotation import ObjectAnnotation

# COCO bbox is [x, y, width, height].
ann_from_coco_bbox = ObjectAnnotation.from_coco_bbox(
    bbox=[10, 20, 20, 30],
    category_id=3,
    category_name="vehicle",
    full_shape=[80, 100],
)
assert ann_from_coco_bbox.bbox.to_xyxy() == [10, 20, 30, 50]

ann_from_coco_dict = ObjectAnnotation.from_coco_annotation_dict(
    annotation_dict={"bbox": [10, 20, 20, 30], "segmentation": [], "category_id": 3},
    category_name="vehicle",
    full_shape=[80, 100],
)

ann_from_segmentation = ObjectAnnotation.from_coco_segmentation(
    segmentation=[[10, 20, 30, 20, 30, 50, 10, 50]],
    category_id=4,
    category_name="mask-object",
    full_shape=[80, 100],
)
```

Low-level `ObjectAnnotation` and `Mask` expect polygon segmentation lists. If a dataset loader has COCO RLE dict masks, decode or convert them before constructing these objects, or keep that workflow in the dataset-level tools.

## Export COCO annotations and predictions

There are two common export levels.

### Per-object export

```python
# Ground-truth-style annotation from ObjectAnnotation.
coco_annotation = annotation.to_coco_annotation()
coco_annotation.image_id = 17
annotation_json = coco_annotation.json
# {'image_id': 17, 'bbox': [10.0, 20.0, 20.0, 30.0],
#  'category_id': 3, 'segmentation': [], 'iscrowd': 0, 'area': 600}

# Prediction export from ObjectPrediction; image_id is accepted here.
prediction_json = prediction.to_coco_prediction(image_id=17).json
# {'image_id': 17, 'bbox': [10.0, 20.0, 20.0, 30.0], 'score': 0.91,
#  'category_id': 3, 'category_name': 'vehicle', 'segmentation': [],
#  'iscrowd': 0, 'area': 600}
```

### Per-result export

```python
# Preserves the same image_id for all predictions in this single-image result.
prediction_dicts = result.to_coco_predictions(image_id=17)

# Historical helper name: returns COCO-prediction-shaped dicts with image_id=None.
annotation_like_dicts = result.to_coco_annotations()
```

For multi-image loops, call `to_coco_predictions(image_id=current_image_id)` once per image and concatenate the lists. Do not call it once with one image ID for predictions from multiple images.

Mask predictions preserve polygon segmentation in the exported JSON:

```python
seg_json = seg_prediction.to_coco_prediction(image_id=17).json
assert seg_json["segmentation"] == [[10, 20, 30, 20, 30, 50, 10, 50]]
assert seg_json["bbox"] == [10.0, 20.0, 20.0, 30.0]
```

## Shifted sliced predictions

When predictions are created from a slice, provide the slice offset as `shift_amount=[shift_x, shift_y]` and the full image shape as `[height, width]`, then export the shifted object:

```python
slice_pred = ObjectPrediction(
    bbox=[5, 7, 15, 17],
    category_id=1,
    category_name="small-object",
    score=0.7,
    shift_amount=[100, 200],
    full_shape=[512, 512],
)
full_image_pred = slice_pred.get_shifted_object_prediction()
assert full_image_pred.bbox.to_xyxy() == [105, 207, 115, 217]
assert full_image_pred.bbox.shift_amount == (0, 0)
```

For segmentation-backed objects, `get_shifted_object_prediction()` also shifts polygon coordinates and clamps them to the provided `full_shape` width/height.

## Optional FiftyOne and imantics conversions

`fiftyone` and `imantics` are optional. Do not assume they are installed unless the caller's environment has them.

| Conversion | Requires | Behavior |
| --- | --- | --- |
| `ObjectPrediction.to_fiftyone_detection(image_height, image_width)` | `fiftyone` | Returns a `fo.Detection` with `label`, relative `bounding_box=[x/W, y/H, w/W, h/H]`, and `confidence`. This helper is bbox-focused. |
| `PredictionResult.to_fiftyone_detections()` | `fiftyone` | Converts all predictions using the result image dimensions. |
| `ObjectAnnotation.to_imantics_annotation()` | `imantics` | Converts bbox-backed annotations to imantics bbox annotations and mask-backed annotations to imantics mask annotations. |
| `ObjectAnnotation.from_imantics_annotation(annotation, full_shape=...)` | `imantics` object input | Builds a SAHI annotation from an imantics annotation. Provide `full_shape` for mask conversions. |
| `PredictionResult.to_imantics_annotations()` | `imantics` | Converts each prediction through `to_imantics_annotation()`. |

Guard optional conversions:

```python
try:
    detections = result.to_fiftyone_detections()
except ImportError:
    detections = None  # fall back to result.to_coco_predictions(image_id=17)
```

## Visualization from result objects

`PredictionResult.export_visuals()` is the simplest output route for a single-image result:

```python
result.export_visuals(
    export_dir="outputs",
    text_size=0.8,
    rect_th=2,
    hide_labels=False,
    hide_conf=False,
    file_name="prediction_visual",
)
# Writes outputs/prediction_visual.png
```

Use `sahi.utils.cv.visualize_object_predictions()` directly when you need `color`, `text_th`, or `export_format` control. It accepts an RGB numpy image, the object prediction list, and writes `file_name + '.' + export_format` when `output_dir` is supplied.
