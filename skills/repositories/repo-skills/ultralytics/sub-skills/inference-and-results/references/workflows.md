# Inference Workflows

This reference gives concrete Ultralytics prediction patterns for Python and CLI use. It is intentionally runtime-safe: examples use placeholders such as `weights.pt`, `image.jpg`, and `video.mp4` instead of depending on a source checkout.

## Python Prediction Patterns

### Single Image or Small Batch

```python
from ultralytics import YOLO

model = YOLO("weights.pt")
results = model("image.jpg", imgsz=640, conf=0.25, device="cpu")
for result in results:
    print(result.path, result.summary(normalize=True))
```

`model(source, **kwargs)` is an alias for `model.predict(source=source, **kwargs)`. Both return a list when `stream=False`.

For an in-memory batch, pass a list of supported image-like sources:

```python
results = model(["image1.jpg", "image2.jpg"], imgsz=640, batch=2)
assert len(results) == 2
```

### Streaming Video, Webcam, Directory, or Long Source List

```python
from ultralytics import YOLO

model = YOLO("weights.pt")
for result in model.predict(source="video.mp4", stream=True, vid_stride=1):
    summary = result.summary(normalize=True)
    # Process this frame, then let it be garbage-collected.
```

Use `stream=True` for long-running sources because `stream=False` materializes all frame/image `Results` in memory. Do not wrap the generator in `list(...)` unless the source is known to be small.

### Supported Source Shapes

Ultralytics prediction can load common visual sources through `source`:

| Source kind | Example | Notes |
| --- | --- | --- |
| Local file | `"image.jpg"`, `"video.mp4"` | Images return one result; videos should use `stream=True`. |
| Directory/glob | `"images/"`, `"images/*.jpg"`, `"images/**/*.jpg"` | Use `stream=True` for large sets. |
| Text/CSV list | `"sources.txt"`, `"sources.csv"` | Each row/path becomes an input source. |
| URL | `"https://.../image.jpg"` | Requires network availability and supported codecs. |
| Webcam | `0` | Use `stream=True`; hardware availability is environment-specific. |
| Screenshot | `"screen"` | May require OS/display support. |
| Stream URL | `"rtsp://..."`, `"rtmp://..."`, `"tcp://..."` | Use `stream=True`; tune `stream_buffer` and `vid_stride`. |
| Multi-stream file | `"feeds.streams"` | One stream per line; batched inference size equals stream count. |
| PIL/OpenCV/NumPy | `PIL.Image`, `np.ndarray` | OpenCV arrays are usually BGR; PIL images are RGB. |
| Torch tensor | `torch.Tensor` | Provide image tensor shape expected by the predictor. |

### Prediction Overrides That Matter Most

- `imgsz`: inference size; `check_imgsz` adjusts to model stride where needed.
- `conf`: confidence threshold; Python predict defaults include `conf=0.25` when not supplied.
- `iou`, `max_det`, `classes`, `agnostic_nms`: postprocessing filters.
- `device`: `cpu`, CUDA index, or backend-supported device string.
- `half`, `dnn`, `compile`: backend/performance options; availability depends on device and model format.
- `batch`: batch size for image sets, directories, videos, or stream lists where supported.
- `vid_stride`: skip video frames for faster processing.
- `stream_buffer`: whether to buffer stream frames; `False` favors newest frames and lower memory.
- `retina_masks`: return segmentation masks in original image shape.
- `save`, `save_txt`, `save_conf`, `save_crop`, `show`: file/display side effects.
- `project`, `name`, `exist_ok`: output directory control.

## CLI Prediction Patterns

Ultralytics CLI uses:

```bash
yolo TASK MODE arg=value
```

`MODE` is required. For prediction, use `predict`; `TASK` can be omitted when the model file declares the task.

```bash
yolo predict model=weights.pt source=image.jpg imgsz=640 conf=0.25 device=cpu save=True
```

Task-specific forms are valid when you want to be explicit:

```bash
yolo detect predict model=weights.pt source=image.jpg save=True
yolo segment predict model=weights-seg.pt source=video.mp4 stream_buffer=False
yolo classify predict model=weights-cls.pt source=images/
yolo obb predict model=weights-obb.pt source=image.jpg
yolo pose predict model=weights-pose.pt source=image.jpg
yolo semantic predict model=weights-sem.pt source=image.jpg
```

CLI arguments must be `arg=value`; flags such as `--imgsz 640` are not the primary Ultralytics CLI shape and often cause argument errors.

## Memory-Safe Streaming Checklist

Use this when adapting a video or live source workflow:

```python
from ultralytics import YOLO

model = YOLO("weights.pt")
stream = model(source="rtsp://camera.example/stream", stream=True, imgsz=640, vid_stride=2)
for result in stream:
    result = result.cpu()
    # Extract only the fields needed for this frame.
    if result.boxes is not None:
        rows = result.summary(normalize=True)
```

- Keep only derived rows, counters, or saved file names if the job is long-running.
- Avoid appending every `Results` object to a list for videos or streams.
- Avoid `save=True` or `save_frames=True` unless disk output is intentional and budgeted.
- For multi-camera `.streams`, expect batched results and variable stream health; handle missing/late frames defensively.

## Callbacks and Custom Predictors

Advanced applications can add prediction callbacks or pass a custom predictor:

```python
def on_predict_batch_end(predictor):
    # predictor.batch contains paths, original images, and status strings.
    # predictor.results is the current batch of Results objects.
    pass

model.add_callback("on_predict_batch_end", on_predict_batch_end)
for result in model.predict("video.mp4", stream=True):
    pass
```

Callbacks can mutate `predictor.results`; keep mutations local and tested because downstream iteration yields that object.

## Threaded Applications

Safest pattern: create a model inside each worker.

```python
from threading import Thread
from ultralytics import YOLO

def worker(source):
    model = YOLO("weights.pt")
    return model(source, device="cpu")

threads = [Thread(target=worker, args=(path,)) for path in ["image1.jpg", "image2.jpg"]]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
```

Shared model fallback:

```python
from ultralytics import YOLO
from ultralytics.utils import ThreadingLocked

model = YOLO("weights.pt")

@ThreadingLocked()
def locked_predict(source):
    return model.predict(source=source)
```

Use process-based workers when CPU/GPU throughput and isolation matter more than startup cost.
