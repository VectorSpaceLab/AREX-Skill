# Troubleshooting annotations and results

## Fast diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: box must be 4 non-negative floats` from `BoundingBox`. | Bbox is not length 4 or contains negative values. | Use core `[minx, miny, maxx, maxy]`; clamp or reject negatives before construction. |
| Exported bbox width/height is wrong. | COCO `[x, y, w, h]` was passed to a core constructor, or core `[minx, miny, maxx, maxy]` was passed to `from_coco_bbox()`. | Pick the matching factory: core constructor for `[minx, miny, maxx, maxy]`, `from_coco_bbox()` for `[x, y, w, h]`. |
| Area is zero or negative, crops are empty, or visuals draw strange boxes. | SAHI validates bbox length and non-negative coordinates but does not always reject `maxx <= minx` or `maxy <= miny` at construction time. | Assert `maxx > minx` and `maxy > miny` before creating annotations/predictions. |
| `TypeError: id should be integer` or `name should be string`. | `Category` received non-int ID or non-string name. | Normalize category IDs to Python `int` and names to `str`; convert numpy scalar IDs with `int(value)`. |
| `ValueError: category_id must be an integer`. | `ObjectAnnotation`/`ObjectPrediction` received `category_id=None`, a string, or a numpy scalar that was not converted. | Pass a Python `int`. If no category name exists, leave `category_name=None` and SAHI will use the ID as the name. |
| `ValueError: you must provide a bbox or segmentation`. | Neither bbox nor segmentation was supplied. | Supply one valid geometry. For bbox-only predictions, do not pass `segmentation=[]` unless it is intentional. |
| `ValueError: full_shape must be provided`. | `Mask` or a segmentation-backed annotation/prediction was created without full image shape. | Pass `full_shape=[height, width]`. Do not use `[width, height]`. |
| `ValueError: Invalid segmentation mask.` | Segmentation had no polygon coordinates, too few points, or could not produce a bbox. | Use polygon lists with at least three points per polygon; verify with `get_bbox_from_coco_segmentation(segmentation)` before construction. |
| Mask array shape is transposed or clipped unexpectedly. | Mixed up `[height, width]` with `[width, height]`, or shifted polygons exceed the full shape. | Use image array shape as `[image.shape[0], image.shape[1]]`; verify `mask.bool_mask.shape == (height, width)`. |
| `mask.bool_mask.dtype` is not `bool`. | `get_bool_mask_from_coco_segmentation()` returns a 0/1 numpy array. | Cast explicitly with `mask.bool_mask.astype(bool)` when strict boolean dtype is needed. |
| Bool mask converts to empty segmentation. | The mask is empty, one-pixel, one-line, or too small for a valid polygon contour. | Check `mask.any()` and use masks with a region large enough to form at least three contour points. |
| `ImportError` says install `fiftyone`. | Calling `to_fiftyone_detection()` or `to_fiftyone_detections()` without optional FiftyOne installed. | Install FiftyOne only when needed, or fall back to `to_coco_predictions(image_id=...)`. |
| `ImportError` says install `imantics`. | Calling imantics conversion without optional imantics installed. | Install imantics only when needed, or fall back to COCO polygon/bbox dictionaries. |
| FiftyOne boxes appear in the wrong place. | FiftyOne expects relative `[x/W, y/H, w/W, h/H]`; image dimensions were wrong. | Use `PredictionResult.to_fiftyone_detections()` so dimensions come from the result image, or pass correct `image_height` and `image_width`. |
| COCO predictions lose image IDs. | Used `PredictionResult.to_coco_annotations()` or object-level annotation conversion without setting `image_id`. | Use `PredictionResult.to_coco_predictions(image_id=current_id)`, or set `coco_annotation.image_id = current_id` before reading `.json`. |
| All predictions get the same wrong image ID. | Concatenated predictions from multiple images after a single `to_coco_predictions(image_id=...)` call. | Export one `PredictionResult` at a time with that image's ID, then concatenate lists. |
| Mask segmentation is absent in exported JSON. | Prediction/annotation was created from bbox only, or segmentation was empty. | Construct from `segmentation=...` or `from_bool_mask()` and provide `full_shape`. |
| COCO RLE mask dict fails or is skipped. | Low-level `Mask`/`ObjectAnnotation` expect polygon list segmentations, not RLE dicts. | Decode/convert RLE to polygons or keep RLE handling in dataset-level COCO tooling. |
| Image colors look swapped. | Raw OpenCV BGR array was passed where SAHI expects RGB. | Convert with `cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)` before `PredictionResult` or visualization helpers. |
| `read_image_as_pil(np_array)` gives odd channel ordering. | It transposes CHW to HWC but does not convert BGR to RGB. | Pass RGB HWC arrays; convert channel order before calling. |
| Image path read fails. | Path is wrong, file unsupported, or large-image fallback dependencies are absent. | Verify path and extension; for large images install the documented image fallback dependencies or use a supported local RGB array. |
| Visualization file is missing. | Wrong output directory/file name expectation, or `output_dir` was omitted for low-level visualizers. | `PredictionResult.export_visuals(export_dir, file_name)` writes `file_name.png`; `visualize_object_predictions(..., output_dir, file_name, export_format)` writes `file_name.export_format`. |
| `cv2` import fails with unusual OpenCV attribute errors. | Mixed `opencv-python`, `opencv-python-headless`, contrib, or headless contrib versions can leave a broken shared `cv2` package. | Check `get_opencv_conflict_message()` and reinstall a single OpenCV distribution or matching versions. |
| JSON export fails on numpy types. | Plain `json.dump` cannot encode numpy ints/floats/arrays. | Use `sahi.utils.file.save_json()`, which uses `NumpyEncoder`, or convert numpy values to Python types. |
| File listing misses files. | `list_files()` only checks one directory and uses substring matching against lowercased names. | Use `list_files_recursively()` for nested trees and choose `contains` strings carefully. |

## Debug bbox format mistakes

Run these assertions before object construction when inputs come from mixed APIs:

```python
def assert_core_xyxy(box):
    assert len(box) == 4, box
    minx, miny, maxx, maxy = box
    assert minx >= 0 and miny >= 0, box
    assert maxx > minx and maxy > miny, box


def coco_xywh_to_core_xyxy(coco_box):
    x, y, w, h = coco_box
    assert w > 0 and h > 0, coco_box
    return [x, y, x + w, y + h]
```

Use `BoundingBox(core_box).to_coco_bbox()` only after the box is known to be core `[minx, miny, maxx, maxy]`.

## Debug mask/full-shape issues

```python
from sahi.utils.cv import get_bbox_from_coco_segmentation, get_bool_mask_from_coco_segmentation

height, width = 720, 1280
segmentation = [[10, 20, 40, 20, 40, 60, 10, 60]]

bbox = get_bbox_from_coco_segmentation(segmentation)
assert bbox is not None, "segmentation produced no bbox"

mask = get_bool_mask_from_coco_segmentation(segmentation, width=width, height=height).astype(bool)
assert mask.shape == (height, width)
assert mask.any(), "segmentation filled no pixels"
```

When deriving `full_shape` from a numpy image, use:

```python
full_shape = [image.shape[0], image.shape[1]]  # [height, width]
```

## Debug optional conversions safely

```python
try:
    fo_detections = result.to_fiftyone_detections()
except ImportError:
    fo_detections = None
    coco_fallback = result.to_coco_predictions(image_id=image_id)

try:
    imantics_annotations = result.to_imantics_annotations()
except ImportError:
    imantics_annotations = None
```

Do not make optional packages required just to serialize results. COCO prediction dictionaries are available with the base dependencies.

## Output path checks

- For `PredictionResult.export_visuals(export_dir="out", file_name="x")`, expect `out/x.png`.
- For `visualize_object_predictions(..., output_dir="out", file_name="x", export_format="jpg")`, expect `out/x.jpg`.
- For `save_json(data, "out/predictions.json")`, the parent directory is created automatically.
- For any helper that writes files, inspect the returned path or construct the expected path explicitly before assuming the output layout.
