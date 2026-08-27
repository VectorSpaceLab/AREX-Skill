# Video Detection API Reference

This reference records the ImageAI 3.x PyTorch video APIs verified from source signatures, implementation behavior, examples, and tests. Model files are external assets; this sub-skill does not bundle release weights or videos.

## Detector Families

| Workflow | Class | Models | Extra assets | COCO `CustomObjects`? |
|---|---|---|---|---|
| Standard COCO video/camera detection | `imageai.Detection.VideoObjectDetection` | RetinaNet, YOLOv3, TinyYOLOv3 | Matching pretrained `.pt`/`.pth` weight file | Yes, through `CustomObjects(...)` and `custom_objects=` |
| Custom trained video/camera detection | `imageai.Detection.Custom.CustomVideoObjectDetection` | YOLOv3, TinyYOLOv3 | Matching custom `.pt`/`.pth` weight file plus JSON detection config | No. Labels come from the custom JSON config. |

Both detector families use OpenCV video I/O internally and run frame-level inference through the corresponding image-detection class.

## Standard VideoObjectDetection Setup

```python
from imageai.Detection import VideoObjectDetection

detector = VideoObjectDetection()
detector.setModelTypeAsRetinaNet()      # or setModelTypeAsYOLOv3(), setModelTypeAsTinyYOLOv3()
detector.setModelPath("model.pt")       # accepts .pt or .pth; .h5 is rejected by ImageAI 3.x
detector.useCPU()                       # optional; call before loadModel() to force CPU
detector.loadModel()
```

Methods:

| Method | Notes |
|---|---|
| `setModelTypeAsRetinaNet()` | Standard COCO RetinaNet. Uses the 91-class RetinaNet label file internally. |
| `setModelTypeAsYOLOv3()` | Standard COCO YOLOv3. |
| `setModelTypeAsTinyYOLOv3()` | Standard COCO TinyYOLOv3. Usually fastest and least accurate. |
| `setModelPath(model_path: str)` | Requires a PyTorch `.pt` or `.pth` file. TensorFlow `.h5` files are rejected with a compatibility message. |
| `useCPU()` | Forces CPU and reloads the model if already loaded. CPU is valid but slow for video. |
| `loadModel()` | Must be called before detection. |
| `CustomObjects(**kwargs)` | Returns a dictionary for selected COCO classes for the loaded model. Use names from `detector.CustomObjects().keys()`; labels with spaces are represented with underscores, for example `traffic_light`, `stop_sign`, `cell_phone`, and `sports_ball` when present. Invalid names raise `ValueError`. |

Verified signature:

```python
VideoObjectDetection.detectObjectsFromVideo(
    input_file_path="",
    camera_input=None,
    output_file_path="",
    frames_per_second=20,
    frame_detection_interval=1,
    minimum_percentage_probability=50,
    log_progress=False,
    display_percentage_probability=True,
    display_object_name=True,
    display_box=True,
    save_detected_video=True,
    per_frame_function=None,
    per_second_function=None,
    per_minute_function=None,
    video_complete_function=None,
    return_detected_frame=False,
    detection_timeout=None,
    custom_objects=None,
)
```

## CustomVideoObjectDetection Setup

```python
from imageai.Detection.Custom import CustomVideoObjectDetection

video_detector = CustomVideoObjectDetection()
video_detector.setModelTypeAsYOLOv3()        # or setModelTypeAsTinyYOLOv3()
video_detector.setModelPath("custom.pt")
video_detector.setJsonPath("custom_detection_config.json")
video_detector.useCPU()                      # optional; call before loadModel()
video_detector.loadModel()
```

Methods:

| Method | Notes |
|---|---|
| `setModelTypeAsYOLOv3()` | Custom YOLOv3 detector. |
| `setModelTypeAsTinyYOLOv3()` | Custom TinyYOLOv3 detector. |
| `setModelPath(model_path: str)` | Requires custom ImageAI PyTorch `.pt` or `.pth` weights. |
| `setJsonPath(configuration_json: str)` | Required. Must match the model architecture/classes produced during training. |
| `useCPU()` | Forces CPU. |
| `loadModel()` | Must be called before detection. |

Verified signature:

```python
CustomVideoObjectDetection.detectObjectsFromVideo(
    input_file_path="",
    camera_input=None,
    output_file_path="",
    frames_per_second=20,
    frame_detection_interval=1,
    minimum_percentage_probability=40,
    log_progress=False,
    display_percentage_probability=True,
    display_object_name=True,
    display_box=True,
    save_detected_video=True,
    per_frame_function=None,
    per_second_function=None,
    per_minute_function=None,
    video_complete_function=None,
    return_detected_frame=False,
    detection_timeout=None,
)
```

`CustomVideoObjectDetection` has no `custom_objects` argument. To restrict classes for a custom model, train or configure the model labels upstream; do not pass COCO `CustomObjects` to the custom-video detector.

## Current API vs Stale Custom-Object Examples

Some ImageAI prose/examples from earlier versions call `detector.detectCustomObjectsFromVideo(...)` for selected COCO classes. The verified current ImageAI 3.x `VideoObjectDetection` class does not expose that method; use `detectObjectsFromVideo(..., custom_objects=detector.CustomObjects(...))` instead.

## Detection Parameters

| Parameter | Applies to | Meaning and verified behavior |
|---|---|---|
| `input_file_path` | Both | Video file path. Required when `camera_input` is not supplied. Internally passed to `cv2.VideoCapture(input_file_path)`. |
| `camera_input` | Both | Existing `cv2.VideoCapture` object for a device camera, IP stream, or other OpenCV source. Replaces `input_file_path` when not `None`. |
| `output_file_path` | Both | Output base path without extension when saving. If saving is enabled, ImageAI writes `output_file_path + ".mp4"`. |
| `frames_per_second` | Both | FPS for the output `cv2.VideoWriter` and for second/minute/timeout accounting. Defaults to `20`. Must be a positive integer. |
| `frame_detection_interval` | Both | Run fresh object detection on frame 1 and every Nth frame where `frame_number % N == 0`. In current ImageAI 3.x source, skipped frames are still written when saving and are stored as empty detection/count entries for aggregate callbacks. Use `1` for every frame. |
| `minimum_percentage_probability` | Standard default 50; custom default 40 | Confidence threshold in percent for detection output. High values can produce no detections. |
| `log_progress` | Both | Prints `Processing Frame : <n>` for each frame read. Useful for long jobs. |
| `display_percentage_probability` | Both | Show/hide percentage text in rendered video frames. Does not remove the score from callback dictionaries. |
| `display_object_name` | Both | Show/hide object-name text in rendered video frames. Does not remove the name from callback dictionaries. |
| `display_box` | Both | Show/hide bounding boxes in rendered video frames. |
| `save_detected_video` | Both | When `True`, output path is required and returned as a string. When `False`, no output video is saved and the function returns `None`; use callbacks for analytics. |
| `per_frame_function` | Both | Called after frame 1 and each frame selected by `frame_detection_interval`. See callback reference. |
| `per_second_function` | Both | Called when processed frame count reaches each multiple of `frames_per_second`, except frame 1. See callback reference. |
| `per_minute_function` | Both | Called when processed frame count reaches each multiple of `frames_per_second * 60`, except frame 1. See callback reference. |
| `video_complete_function` | Both | Called after the processing loop completes if provided. See callback reference. |
| `return_detected_frame` | Both | Adds the current rendered/detected frame numpy array to frame, second, and minute callbacks only. Does not add a frame to `video_complete_function`. |
| `detection_timeout` | Both | Stop after approximately this many seconds according to processed frame count and `frames_per_second`, not wall-clock time. Essential for camera sources. |
| `custom_objects` | Standard only | Dictionary from `detector.CustomObjects(...)` to restrict COCO classes. |

## Return Values

| Situation | Return |
|---|---|
| `save_detected_video=True` and detection completes | String output path equal to `output_file_path + ".mp4"`. Tests assert that the `.mp4` file exists for standard and custom video paths. |
| `save_detected_video=False` | `None`. Callbacks are the primary output channel. |
| No input source supplied | Raises `ValueError` requiring `input_file_path` or `camera_input`. |
| Saving enabled without `output_file_path` | Raises `ValueError` requiring an output video filepath or `save_detected_video=False`. |
| Invalid input video, writer/path issue, or callback arity issue in standard detector | Standard detector wraps many failures in a `ValueError` mentioning invalid input video, output path, or callback parameters. Custom detector may propagate lower-level exceptions in some paths. |

## Callback Data Shapes

See [`callbacks-and-analysis.md`](callbacks-and-analysis.md) for examples. Summary:

| Callback | `return_detected_frame=False` | `return_detected_frame=True` |
|---|---|---|
| `per_frame_function` | `(frame_number, output_array, output_count)` | `(frame_number, output_array, output_count, detected_frame)` |
| `per_second_function` | `(second_number, output_arrays, count_arrays, average_output_count)` | `(second_number, output_arrays, count_arrays, average_output_count, detected_frame)` |
| `per_minute_function` | `(minute_number, output_arrays, count_arrays, average_output_count)` | `(minute_number, output_arrays, count_arrays, average_output_count, detected_frame)` |
| `video_complete_function` | `(output_arrays, count_arrays, average_output_count)` | Same; no detected frame argument. |

Detection dictionaries have this shape:

```python
{
    "name": "car",                         # str
    "percentage_probability": 87.18,       # float percent
    "box_points": [x1, y1, x2, y2],        # list of ints in current ImageAI 3.x tests/source
}
```

Count dictionaries map object-name strings to integer counts, for example `{"person": 2, "car": 5}`. `average_output_count` is computed as integer division by the number of frames in the second/minute/video in current source, even though prose examples may display averages as decimals.
