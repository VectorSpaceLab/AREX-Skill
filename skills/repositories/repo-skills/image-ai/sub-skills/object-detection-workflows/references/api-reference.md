# ImageAI Object Detection API Reference

This reference covers the current ImageAI 3.x still-image detection APIs verified from source and installed-package inspection. It intentionally excludes video/camera APIs and training/data APIs.

## Classes and model setup

| Use case | Import | Class | Supported model types | Required asset calls before detection |
|---|---|---|---|---|
| COCO still-image detection | `from imageai.Detection import ObjectDetection` | `ObjectDetection` | `retinanet`, `yolov3`, `tiny-yolov3` | call exactly one model-type setter, `setModelPath(path)`, then `loadModel()` |
| Custom still-image detection | `from imageai.Detection.Custom import CustomObjectDetection` | `CustomObjectDetection` | `yolov3`, `tiny-yolov3` | call exactly one model-type setter, `setModelPath(path)`, `setJsonPath(json_path)`, then `loadModel()` |

Model-type setter mapping:

| CLI/model label | COCO method | Custom method | Notes |
|---|---|---|---|
| `retinanet` | `setModelTypeAsRetinaNet()` | not supported | COCO only; loads `coco91_classes.txt` internally after `loadModel()` |
| `yolov3` | `setModelTypeAsYOLOv3()` | `setModelTypeAsYOLOv3()` | COCO or custom, depending on class |
| `tiny-yolov3` | `setModelTypeAsTinyYOLOv3()` | `setModelTypeAsTinyYOLOv3()` | COCO or custom, faster/smaller model family |

`setModelPath(path)` requires an existing file and the backend extension checker accepts only `.pt` and `.pth`. A `.h5` file raises a TensorFlow-era compatibility error. Any other extension raises an invalid model-file error.

`useCPU()` may be called before `loadModel()` to force CPU inference even if CUDA is available. If called after a model is already loaded, the class reloads the model on CPU.

## Verified detection signatures

### `ObjectDetection.detectObjectsFromImage`

```python
detector.detectObjectsFromImage(
    input_image,
    output_image_path=None,
    output_type="file",
    extract_detected_objects=False,
    minimum_percentage_probability=50,
    display_percentage_probability=True,
    display_object_name=True,
    display_box=True,
    custom_objects=None,
)
```

### `CustomObjectDetection.detectObjectsFromImage`

```python
detector.detectObjectsFromImage(
    input_image,
    output_image_path=None,
    output_type="file",
    extract_detected_objects=False,
    minimum_percentage_probability=40,
    display_percentage_probability=True,
    display_object_name=True,
    display_box=True,
    custom_objects=None,
    nms_treshold=0.4,
    objectness_treshold=0.4,
)
```

Keep the misspelled custom API parameter names exactly as source spells them: `nms_treshold` and `objectness_treshold`.

## Detection parameters

| Parameter | Applies to | Meaning | Common choices and caveats |
|---|---|---|---|
| `input_image` | COCO and custom | Image file path, OpenCV/Numpy image array, or PIL image object | Source accepts file paths with `.jpg`, `.jpeg`, `.png`; arrays are treated as OpenCV/BGR style input and returned arrays are OpenCV/BGR rendered images. Current source does not accept `input_type`; pass the object directly. |
| `output_image_path` | COCO and custom | Destination for annotated image when `output_type="file"` | Required if the caller wants a saved annotated image or extracted object files. If omitted in file mode, detections are returned but no annotated file is written. |
| `output_type` | COCO and custom | Output mode for rendered image | Only `file` and `array` are valid. `file` may write `output_image_path`; `array` returns an image array. |
| `extract_detected_objects` | COCO and custom | Crop each returned object above `minimum_percentage_probability` | File output returns extracted file paths; array output returns extracted Numpy arrays. |
| `minimum_percentage_probability` | COCO and custom | Final percentage threshold for returned detections and rendered/extracted objects | Default is `50` for COCO and `40` for custom detection. Lower values return more uncertain detections; higher values return fewer detections. |
| `display_percentage_probability` | COCO and custom | Whether annotated output displays confidence text | Does not change detections; only affects rendered output. |
| `display_object_name` | COCO and custom | Whether annotated output displays label text | Does not change detections; only affects rendered output. |
| `display_box` | COCO and custom | Whether annotated output draws bounding boxes | Does not change detections; only affects rendered output. |
| `custom_objects` | COCO and custom | Label filter dictionary with object-name keys and boolean values | For COCO, build it with `ObjectDetection.CustomObjects(...)`. For custom models, create keys from config labels with spaces replaced by underscores; the class checks prediction labels against this dictionary. |
| `nms_treshold` | custom only | YOLO non-maximum suppression confidence setting passed to prediction post-processing | Source spelling is `treshold`, not `threshold`. Default `0.4`. |
| `objectness_treshold` | custom only | YOLO objectness confidence setting before class filtering | Source spelling is `treshold`, not `threshold`. Default `0.4`. |

## Return shapes

Every detection is a dictionary:

```python
{
    "name": "person",
    "percentage_probability": 96.34,
    "box_points": [x1, y1, x2, y2],
}
```

`box_points` are integer coordinates in `[x1, y1, x2, y2]` order. Native tests assert `x1 < x2` and `y1 < y2` for valid detections.

| `output_type` | `extract_detected_objects` | Return value | Side effects |
|---|---:|---|---|
| `file` | `False` | `detections` | Writes `output_image_path` only when provided. |
| `file` | `True` | `(detections, extracted_paths)` | Writes `output_image_path` when provided, then creates extraction directory from output basename plus `-extracted` and writes crop files there. |
| `array` | `False` | `(image_array, detections)` | No output file is written. `image_array` is an OpenCV/Numpy BGR rendered image. |
| `array` | `True` | `(image_array, detections, extracted_arrays)` | No output file is written. `extracted_arrays` contains OpenCV/Numpy crop arrays. |

No-detection behavior is usually shape-stable: array mode returns the rendered/original image array with an empty detections list, and extraction mode adds an empty extraction list. File mode normally returns an empty list, or `(detections, extracted_paths)` after post-processing. One source edge case to handle defensively: YOLO/TinyYOLO with no post-NMS predictions can return `(original_image_array, [])` for `output_type="file", extract_detected_objects=True` before the usual file-writing path runs.

## `CustomObjects` filtering

For COCO still images, call `CustomObjects` on a loaded or loadable `ObjectDetection` instance:

```python
custom = detector.CustomObjects(car=True, motorcycle=True, cell_phone=True)
detections = detector.detectObjectsFromImage(
    input_image="input.jpg",
    output_image_path="filtered.jpg",
    custom_objects=custom,
)
```

`CustomObjects` constructs a dictionary with every COCO class initially `False` and then sets requested labels to `True`. It raises `ValueError` if a requested label is not in the class list. Use underscores in keyword names when the class label contains a space: `traffic_light`, `stop_sign`, `cell_phone`, `teddy_bear`, and similar.

For custom detection models, ImageAI does not expose a `CustomObjects()` helper on `CustomObjectDetection`, but `detectObjectsFromImage(custom_objects=...)` accepts a compatible dictionary. Build it from the custom model labels in the JSON config, with spaces replaced by underscores.

## Current API versus older examples

Some older ImageAI docs and examples mention `detectCustomObjectsFromImage(...)` and `input_type="array"`/`input_type="stream"`. The verified ImageAI 3.x source inspected for this skill uses `detectObjectsFromImage(custom_objects=...)` for still-image object filtering and does not include an `input_type` parameter in the current still-image signatures. Pass a path, Numpy array, or PIL image object directly as `input_image`.
