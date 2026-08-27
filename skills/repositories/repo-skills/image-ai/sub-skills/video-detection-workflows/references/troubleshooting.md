# Video Detection Troubleshooting

## Quick Diagnosis Matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: You must set 'input_file_path'... or 'camera_input'...` | No video source supplied. | Provide `input_file_path` or explicitly create/pass `cv2.VideoCapture`; with helper, use exactly one of `--input-video` or `--camera-index`. |
| Error says output path is required | `save_detected_video=True` but no `output_file_path`. | Provide an output base path or set `save_detected_video=False` / helper `--no-save`. |
| Camera job runs forever | Camera source has no natural EOF and no timeout. | Set `detection_timeout`; for helper camera mode, always pass `--timeout` unless intentionally long-running. |
| Camera does nothing or output has 0x0 frames | `cv2.VideoCapture` did not open or source has no readable frames. | Check `camera.isOpened()`, camera permissions, device index, stream URL, and OpenCV backend. Release the camera in `finally`. |
| Video file produces no frames | Missing file, unreadable path, unsupported codec/container, or OpenCV was built without needed codec support. | Validate file existence, open with `cv2.VideoCapture(path).isOpened()`, transcode to a common H.264/MP4 or MJPEG/AVI file, and avoid non-ASCII/problematic paths if codec tooling is old. |
| Output file path returned but video cannot play | `cv2.VideoWriter` codec/container issue or zero width/height input. | Confirm source width/height > 0; try a simple `.mp4` base path; ensure OpenCV has MP4V support; transcode input; check disk permissions/free space. |
| Callback arity error or generic invalid-video/callback `ValueError` | Function signature does not match `return_detected_frame`. | Use 3/4 args for frame, 4/5 for second/minute, and always 3 for complete. See `callbacks-and-analysis.md`. |
| No detections | Threshold too high, wrong model type/weights, selected `custom_objects` excludes all labels, or custom JSON/model mismatch. | Lower `minimum_percentage_probability`, verify model type matches weights, remove filters, inspect custom JSON classes. |
| `object '<name>' doesn't exist...` | Invalid COCO `CustomObjects` key for the loaded model. | Inspect `detector.CustomObjects().keys()` and use exact keys; labels with spaces appear with underscores when present, e.g. `traffic_light`, `stop_sign`, `cell_phone`. |
| Custom detector rejects `custom_objects` | `CustomVideoObjectDetection.detectObjectsFromVideo` has no `custom_objects` argument. | Do not pass COCO filters to custom video models; labels come from the JSON config. |
| `.h5` model rejected | ImageAI 3.x is PyTorch-backed. | Use `.pt`/`.pth` ImageAI 3.x weights. TensorFlow-era `.h5` requires old ImageAI 2.1.6 compatibility outside this skill. |
| `RuntimeError: Invalid weights!!!` | Weight file does not match selected architecture/classes. | Match `setModelType...()` to the downloaded or trained model; use the correct JSON for custom models. |
| Very slow processing | CPU execution, large model, high FPS, interval 1, frame callback doing heavy work. | Use CUDA if available, TinyYOLOv3 for speed, lower output FPS, increase `frame_detection_interval`, use `--timeout`, and keep callbacks lightweight. |
| Memory grows on long videos | Complete-video arrays or stored detected frames accumulate. | Prefer per-second aggregation, avoid storing frames, use timeouts/sampling, and disable `return_detected_frame` unless needed. |

## OpenCV Source Checks

Before calling ImageAI with a file source:

```python
from pathlib import Path
import cv2

path = Path("input.mp4")
if not path.is_file():
    raise FileNotFoundError(path)

cap = cv2.VideoCapture(str(path))
try:
    if not cap.isOpened():
        raise RuntimeError("OpenCV could not open the video file")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        raise RuntimeError("OpenCV opened the file but reported invalid frame size")
finally:
    cap.release()
```

Before camera detection:

```python
import cv2

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise RuntimeError("Camera 0 could not be opened")
```

The bundled helper performs these checks before invoking ImageAI.

## Output Path Rules

- `output_file_path` is a base path, not necessarily a full final filename.
- Current ImageAI 3.x video code appends `.mp4`, so `output_file_path="runs/out"` writes `runs/out.mp4` and returns that string.
- If the user supplies `runs/out.mp4` as the base path directly, ImageAI writes `runs/out.mp4.mp4`. Prefer passing the base without extension or let the helper strip a trailing video extension.
- Parent directories must exist and be writable.
- When `save_detected_video=False`, output path is optional and no path is returned.

## Callback Failures

Use this arity map:

```text
return_detected_frame=False:
  per_frame(frame_number, output_array, output_count)
  per_second(second_number, output_arrays, count_arrays, average_output_count)
  per_minute(minute_number, output_arrays, count_arrays, average_output_count)
  complete(output_arrays, count_arrays, average_output_count)

return_detected_frame=True:
  per_frame(frame_number, output_array, output_count, detected_frame)
  per_second(second_number, output_arrays, count_arrays, average_output_count, detected_frame)
  per_minute(minute_number, output_arrays, count_arrays, average_output_count, detected_frame)
  complete(output_arrays, count_arrays, average_output_count)
```

If the standard detector raises a broad `ValueError` mentioning invalid video or callback configuration, inspect callback exceptions first; the implementation catches many different failures under the same message.

## Performance and Timeout Tuning

- `detection_timeout` is approximate video seconds computed from processed frame counts and `frames_per_second`, not a strict wall-clock deadline.
- On CPU, a 10-second timeout can still take much longer than 10 wall-clock seconds if inference is slow.
- `frame_detection_interval` is the main compute-saving knob. For mostly static camera scenes, intervals like 5, 10, or 20 can be reasonable.
- `frames_per_second` controls the writer FPS and callback second boundaries. Set it to match the desired output/analytics cadence.
- `log_progress=True` helps detect stalls, but adds console noise.
- Use `return_detected_frame=False` unless visualization needs the frame array.

## Custom Model and JSON Mismatch

For `CustomVideoObjectDetection`, the `.pt`/`.pth` file and JSON detection config must be from the same custom training run or at least have matching architecture and class count.

Failure signs:

- Weight-loading errors or tensor shape mismatch.
- Detection labels are wrong or absent.
- Custom YOLOv3 weights used with TinyYOLOv3 setter, or the reverse.
- JSON file missing or points to a different dataset/class list.

Fix by selecting the correct `setModelTypeAsYOLOv3()` or `setModelTypeAsTinyYOLOv3()`, pairing the JSON config with its trained model, and validating the training artifacts in `custom-training-and-data`.

## No Detections Checklist

1. Lower threshold: try `minimum_percentage_probability=30`.
2. Remove `custom_objects` filters.
3. Test a short known-good clip and image with the same model family.
4. Confirm the model file is not a TensorFlow `.h5` or an incompatible architecture.
5. For custom models, inspect the JSON class names and training route.
6. Confirm input frames are readable and not blank/dark/resized unexpectedly.

## Helper-Specific Errors

`scripts/detect_video.py` intentionally fails early when:

- Both `--input-video` and `--camera-index` are supplied, or neither is supplied.
- `--output-video` is omitted while saving is enabled.
- `--mode custom` lacks `--json-path`.
- `--mode custom` is paired with `--model-type retinanet`.
- `--custom-objects` is supplied outside COCO mode.
- `--camera-index` cannot be opened.

These checks avoid accidental camera starts, confusing `.mp4.mp4` outputs, and long-running unbounded camera jobs.
