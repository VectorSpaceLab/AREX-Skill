# Callbacks and Video Analysis

ImageAI video detectors can call user functions at frame, second, minute, and whole-video boundaries. These callbacks are the main way to extract analytics when `save_detected_video=False` or when a downstream task needs counts, boxes, or annotated frames while a video is processed.

## Detection Dictionary Shape

Each detection in an `output_array` is a dictionary:

```python
{
    "name": "person",                   # object label string
    "percentage_probability": 92.41,    # confidence in percent, float
    "box_points": [x1, y1, x2, y2],      # bounding box list of ints
}
```

`output_count` and entries in `count_arrays` map object-name strings to integer counts:

```python
{"person": 2, "car": 5}
```

`average_output_count` is a dictionary across the callback window. Current ImageAI 3.x source computes these averages with integer division, so values are integers even when conceptual averages might be fractional.

## Callback Signatures

| Callback parameter | When called | Without detected frame | With `return_detected_frame=True` |
|---|---|---|---|
| `per_frame_function` | After frame 1 and each frame selected by `frame_detection_interval` | `func(frame_number, output_array, output_count)` | `func(frame_number, output_array, output_count, detected_frame)` |
| `per_second_function` | When processed frame count is a multiple of `frames_per_second` | `func(second_number, output_arrays, count_arrays, average_output_count)` | `func(second_number, output_arrays, count_arrays, average_output_count, detected_frame)` |
| `per_minute_function` | When processed frame count is a multiple of `frames_per_second * 60` | `func(minute_number, output_arrays, count_arrays, average_output_count)` | `func(minute_number, output_arrays, count_arrays, average_output_count, detected_frame)` |
| `video_complete_function` | After processing ends | `func(output_arrays, count_arrays, average_output_count)` | Same; no detected-frame argument is added. |

`detected_frame` is a NumPy array of the current rendered frame. It is provided only to frame, second, and minute callbacks when `return_detected_frame=True`. Do not add a fourth argument to `video_complete_function`.

## Frame Callback Example

```python
frame_events = []

def on_frame(frame_number, output_array, output_count):
    frame_events.append({
        "frame": frame_number,
        "detections": len(output_array),
        "counts": dict(output_count),
    })

detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    output_file_path="detected",
    frames_per_second=10,
    frame_detection_interval=5,
    per_frame_function=on_frame,
)
```

If `frame_detection_interval=5`, ImageAI calls this callback for frame 1 and frames 5, 10, 15, ... . Use interval `1` when every frame needs callback data.

## Per-Second Counts Without Saving Video

This pattern supports analytics-only processing and is useful for the hard case “record counts without saving video”.

```python
second_summary = []

def on_second(second_number, output_arrays, count_arrays, average_output_count):
    second_summary.append({
        "second": second_number,
        "frames_in_window": len(output_arrays),
        "counts_by_frame": [dict(counts) for counts in count_arrays],
        "average_count": dict(average_output_count),
    })

detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    save_detected_video=False,
    frames_per_second=10,
    frame_detection_interval=1,
    minimum_percentage_probability=30,
    per_second_function=on_second,
)

# Function returns None; use second_summary.
```

Command-line helper:

```bash
python scripts/detect_video.py \
  --mode coco \
  --model-type tiny-yolov3 \
  --model-path /path/to/tiny-yolov3.pt \
  --input-video input.mp4 \
  --no-save \
  --analysis-summary \
  --fps 10 \
  --timeout 15
```

## Returning Detected Frames

Use `return_detected_frame=True` only when a callback actually needs the image array; it increases memory pressure and can slow analysis code.

```python
def on_frame(frame_number, output_array, output_count, detected_frame):
    assert detected_frame.ndim == 3
    # Example: send detected_frame to a visualization queue.

video_detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    output_file_path="detected",
    per_frame_function=on_frame,
    return_detected_frame=True,
)
```

For per-second or per-minute callbacks, the frame argument is the current rendered frame at the boundary, not an array of all frames in the window. Use `output_arrays` and `count_arrays` for per-frame analytics over the window.

## Complete-Video Summary

```python
complete_summary = {}

def on_complete(output_arrays, count_arrays, average_output_count):
    complete_summary["frame_count"] = len(output_arrays)
    complete_summary["average_count"] = dict(average_output_count)
    complete_summary["non_empty_frames"] = sum(1 for detections in output_arrays if detections)

detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    save_detected_video=False,
    frames_per_second=10,
    video_complete_function=on_complete,
)
```

Caution: the complete callback stores output arrays and count dictionaries for all processed frames. For long videos or cameras, prefer per-second aggregation plus a timeout to avoid unbounded memory use.

## Combining Selected COCO Classes and Camera Timeout

This pattern supports the hard case “detect only selected COCO classes from a camera with timeout and no accidental infinite run”.

```python
import cv2
from imageai.Detection import VideoObjectDetection

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise RuntimeError("Camera was not opened")

try:
    detector = VideoObjectDetection()
    detector.setModelTypeAsTinyYOLOv3()
    detector.setModelPath("tiny-yolov3.pt")
    detector.loadModel()

    selected = detector.CustomObjects(person=True, car=True, bus=True)
    seconds = []

    def on_second(second_number, output_arrays, count_arrays, average_output_count):
        seconds.append({"second": second_number, "average": dict(average_output_count)})

    detector.detectObjectsFromVideo(
        camera_input=camera,
        save_detected_video=False,
        frames_per_second=5,
        frame_detection_interval=5,
        minimum_percentage_probability=35,
        custom_objects=selected,
        per_second_function=on_second,
        detection_timeout=10,
    )
finally:
    camera.release()
```

Helper command:

```bash
python scripts/detect_video.py \
  --mode coco \
  --model-type tiny-yolov3 \
  --model-path tiny-yolov3.pt \
  --camera-index 0 \
  --custom-objects person,car,bus \
  --no-save \
  --analysis-summary \
  --fps 5 \
  --frame-detection-interval 5 \
  --timeout 10
```

## Arity Checklist

Most callback failures are function-signature mismatches. Before running:

- If `return_detected_frame=False`, frame callback has exactly 3 positional parameters; second/minute have 4; complete has 3.
- If `return_detected_frame=True`, frame callback has 4; second/minute have 5; complete still has 3.
- Avoid callbacks that raise exceptions unless you want the whole video run to fail.
- Keep callback work lightweight; heavy database writes or plotting inside every frame callback can dominate runtime.

## Analysis Data Caveats

- Frame intervals affect how often fresh detections and frame callbacks are produced.
- High `minimum_percentage_probability` may yield empty `output_array` and empty count dictionaries.
- For no-save workflows, the detection call returns `None`; store the desired analytics in outer mutable objects or a class.
- For long jobs, do not store every `detected_frame` unless necessary. Store counts or sampled frames instead.
