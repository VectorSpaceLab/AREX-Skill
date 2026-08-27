# Video Detection Workflows

These recipes are self-contained patterns for using ImageAI video detection with external model/video assets. They avoid depending on the original repository checkout.

## Prerequisites

- Python environment with ImageAI 3.x, PyTorch, torchvision, OpenCV, NumPy, Pillow, SciPy, matplotlib/tqdm dependencies as appropriate.
- PyTorch `.pt` or `.pth` model weights matching the selected ImageAI detector and model type.
- Video file or explicit OpenCV camera/live-stream source.
- For custom video detection: the JSON detection config produced with the custom model.
- Optional CUDA improves throughput; CPU is supported but can be very slow for full videos.

Use the helper for CLI-driven runs:

```bash
python scripts/detect_video.py --help
```

The helper never opens a camera unless `--camera-index` is explicitly provided.

## Standard COCO Video File Detection

```python
from imageai.Detection import VideoObjectDetection

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()  # or RetinaNet/TinyYOLOv3 setters
detector.setModelPath("/path/to/yolov3.pt")
detector.loadModel()

output_path = detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    output_file_path="output_detected",  # ImageAI writes output_detected.mp4
    frames_per_second=20,
    minimum_percentage_probability=50,
    log_progress=True,
)
print(output_path)
```

Command-line equivalent:

```bash
python scripts/detect_video.py \
  --mode coco \
  --model-type yolov3 \
  --model-path /path/to/yolov3.pt \
  --input-video input.mp4 \
  --output-video output_detected \
  --fps 20 \
  --minimum-percentage-probability 50 \
  --log-progress
```

Notes:

- `--output-video` is a base path. ImageAI appends `.mp4`; the helper reports the returned path.
- Standard model choices are `retinanet`, `yolov3`, and `tiny-yolov3`.
- If the model type does not match the weights, `loadModel()` or inference can fail with invalid-weight or shape errors.

## Selected COCO Classes in Video

Use `CustomObjects` only with the standard `VideoObjectDetection` class. Names must match the labels returned by `detector.CustomObjects()` for the loaded model, with spaces replaced by underscores. Some names differ by architecture label file, so prefer common labels such as `person`, `car`, and `bus` unless you have inspected the loaded detector's keys.

```python
custom = detector.CustomObjects(person=True, car=True, bus=True)

output_path = detector.detectObjectsFromVideo(
    input_file_path="traffic.mp4",
    output_file_path="traffic_selected",
    custom_objects=custom,
    frames_per_second=20,
)
```

Command-line equivalent:

```bash
python scripts/detect_video.py \
  --mode coco \
  --model-type yolov3 \
  --model-path /path/to/yolov3.pt \
  --input-video traffic.mp4 \
  --output-video traffic_selected \
  --custom-objects person,car,bus \
  --timeout 30
```

For camera sources, always include `--timeout` unless the user truly wants a long-running job.

## Camera or Live Stream Detection

ImageAI expects an already opened OpenCV `VideoCapture` object through `camera_input`. Do not create one implicitly in reusable code; require an explicit camera index or stream URL from the user.

```python
import cv2
from imageai.Detection import VideoObjectDetection

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise RuntimeError("Camera 0 could not be opened")

try:
    detector = VideoObjectDetection()
    detector.setModelTypeAsTinyYOLOv3()
    detector.setModelPath("/path/to/tiny-yolov3.pt")
    detector.loadModel()

    detector.detectObjectsFromVideo(
        camera_input=camera,
        output_file_path="camera_detected",
        frames_per_second=10,
        frame_detection_interval=5,
        detection_timeout=20,
        minimum_percentage_probability=40,
    )
finally:
    camera.release()
```

Helper command:

```bash
python scripts/detect_video.py \
  --mode coco \
  --model-type tiny-yolov3 \
  --model-path /path/to/tiny-yolov3.pt \
  --camera-index 0 \
  --output-video camera_detected \
  --fps 10 \
  --frame-detection-interval 5 \
  --timeout 20 \
  --minimum-percentage-probability 40
```

Safety guidance:

- Do not open the default camera unless the task explicitly names a camera index or stream.
- Use `detection_timeout` for cameras; without it, processing continues until the camera feed closes or the process is interrupted.
- Check `camera.isOpened()` before calling ImageAI. A closed camera usually yields no frames and may produce an empty or invalid output file.

## Custom Trained Video Detection

Use `CustomVideoObjectDetection` with the matching JSON config produced during ImageAI custom detection training.

```python
from imageai.Detection.Custom import CustomVideoObjectDetection

video_detector = CustomVideoObjectDetection()
video_detector.setModelTypeAsYOLOv3()  # or setModelTypeAsTinyYOLOv3()
video_detector.setModelPath("custom_yolov3.pt")
video_detector.setJsonPath("custom_detection_config.json")
video_detector.loadModel()

output_path = video_detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    output_file_path="custom_detected",
    frames_per_second=20,
    minimum_percentage_probability=40,
    log_progress=True,
)
print(output_path)
```

Helper command:

```bash
python scripts/detect_video.py \
  --mode custom \
  --model-type yolov3 \
  --model-path custom_yolov3.pt \
  --json-path custom_detection_config.json \
  --input-video input.mp4 \
  --output-video custom_detected \
  --fps 20
```

Custom detector differences:

- Valid model types are only `yolov3` and `tiny-yolov3`.
- There is no `custom_objects` parameter. The JSON config defines class labels.
- A JSON/model mismatch can fail during load or produce no meaningful detections.

## Save vs No-Save Analytics

When saving:

```python
returned = detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    output_file_path="detected_base",
    save_detected_video=True,
)
assert returned.endswith(".mp4")
```

When not saving:

```python
counts_by_second = []

def per_second(second_number, output_arrays, count_arrays, average_output_count):
    counts_by_second.append({"second": second_number, "average": dict(average_output_count)})

detector.detectObjectsFromVideo(
    input_file_path="input.mp4",
    save_detected_video=False,
    per_second_function=per_second,
    frames_per_second=10,
)
print(counts_by_second)
```

No-save runs return `None`; they are useful for analytics, batch summaries, or camera monitoring where writing a video file is unnecessary. The bundled helper's `--analysis-summary --no-save` mode prints JSON callback summaries.

## FPS, Frame Interval, and Timeout Choices

| Goal | Suggested settings | Trade-off |
|---|---|---|
| Highest fidelity | `frame_detection_interval=1`, source-like `frames_per_second` | Slowest; detects every frame. |
| Faster CPU preview | `tiny-yolov3`, `frames_per_second=5..10`, `frame_detection_interval=5..20` | Lower temporal precision; skipped frames may not have fresh detections. |
| Bounded camera run | `detection_timeout=<seconds>`, `log_progress=True` | Timeout is based on processed frames divided by `frames_per_second`, not wall-clock time. |
| No video artifact | `save_detected_video=False`, callbacks enabled | No returned file; callbacks must capture desired data. |
| Avoid empty results | Lower `minimum_percentage_probability` from 50/40 to 30 | More false positives. |

Implementation details that matter:

- `frame_detection_interval` runs detection on frame 1 and frames where `frame_number % interval == 0`; in current ImageAI 3.x source, skipped frames are written without fresh boxes and contribute empty detection/count entries to aggregate arrays.
- Per-second callbacks fire at processed frame counts divisible by `frames_per_second`.
- Per-minute callbacks fire at processed frame counts divisible by `frames_per_second * 60`.
- `detection_timeout` increments once per `frames_per_second` processed frames, then breaks when the count reaches the timeout value.

## CPU/GPU Notes

- ImageAI 3.x uses PyTorch. CUDA is optional but strongly recommended for full video inference.
- CPU execution is acceptable for API semantics, short clips, tests, and low-FPS previews, but can be minutes-to-hours slower on long videos.
- Call `useCPU()` before `loadModel()` or pass `--cpu` to the helper when reproducibility or GPU unavailability matters.
- TinyYOLOv3 is usually the best speed-first model choice; RetinaNet is usually heavier.

## Helper Output Summary

`scripts/detect_video.py` prints a JSON object containing:

- `mode`, `model_type`, `source`, `save_detected_video`, `returned_path`.
- Effective video parameters such as FPS, interval, threshold, timeout, and display flags.
- If `--analysis-summary` is used: callback-derived `frames`, `seconds`, `minutes`, `complete`, and count summaries.

The helper validates common unsafe or invalid combinations before loading model weights:

- Requires exactly one of `--input-video` or `--camera-index`.
- Requires `--output-video` unless `--no-save` is supplied.
- Requires `--json-path` in custom mode.
- Rejects `--custom-objects` outside COCO mode.
- Does not open any camera unless `--camera-index` is explicitly present.
