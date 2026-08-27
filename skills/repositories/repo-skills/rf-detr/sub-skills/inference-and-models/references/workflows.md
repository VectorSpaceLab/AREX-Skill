# RF-DETR Inference Workflows

These workflows focus on prediction-time usage. Training, CLI, export, and repository-development flows are intentionally excluded.

## Choose a model

1. Identify the task:
   - Detection: choose `RFDETRSmall` by default; use Nano for lowest latency, Medium/Large for higher accuracy.
   - Segmentation: choose a sized `RFDETRSeg*` class; use `RFDETRSegSmall` as the balanced default.
   - Keypoints: choose `RFDETRKeypointPreview`; keypoints are preview-only in this RF-DETR version.
2. Avoid deprecated stand-ins:
   - Do not introduce new `RFDETRBase` examples.
   - Do not introduce new `RFDETRSegPreview` examples.
   - Only use preview naming for keypoints.
3. If the user asks for detection XLarge/2XLarge, treat it as Plus:
   - Install with `pip install "rfdetr[plus]"`.
   - Preserve the Plus license/account boundary.
   - Catch `ImportError` and explain the missing extra instead of downgrading silently.

## Single-image detection

```python
import supervision as sv
from rfdetr import RFDETRSmall

model = RFDETRSmall()
detections = model.predict("image.jpg", threshold=0.5)

labels = list(detections.data["class_name"])
annotated = sv.BoxAnnotator().annotate(detections.metadata["source_image"], detections)
annotated = sv.LabelAnnotator().annotate(annotated, detections, labels)
```

Use `detections.data["class_name"]` even for COCO-pretrained models. It also works for fine-tuned checkpoints and avoids sparse COCO ID mistakes.

## Single-image segmentation

```python
import supervision as sv
from rfdetr import RFDETRSegSmall

model = RFDETRSegSmall()
detections = model.predict("image.jpg", threshold=0.5)

labels = list(detections.data["class_name"])
annotated = sv.MaskAnnotator().annotate(detections.metadata["source_image"], detections)
annotated = sv.LabelAnnotator().annotate(annotated, detections, labels)
```

Segmentation returns `supervision.Detections` with `mask` populated. Keep mask and box arrays aligned by filtering the `Detections` object itself, not by separately filtering raw arrays.

## Single-image keypoints

```python
import cv2
import supervision as sv
from rfdetr import RFDETRKeypointPreview

model = RFDETRKeypointPreview()
image_bgr = cv2.imread("image.jpg")
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

key_points = model.predict(image_rgb, threshold=0.5)

visible = key_points.keypoint_confidence > 0.2
key_points.visible = visible
annotated = sv.VertexAnnotator().annotate(image_rgb, key_points)
```

Common keypoint follow-ups:

- Use `key_points.data["class_name"]` instead of indexing a class list by `class_id`.
- Use `key_points.data["xyxy"]` when downstream code needs detection boxes.
- For uncertainty visualization, check for `key_points.data["covariance"]` before using ellipse annotators.
- The pretrained preview checkpoint returns 17 keypoints; fine-tuned checkpoints can return a different `K`.

## Batch prediction

```python
from PIL import Image
from rfdetr import RFDETRSmall

model = RFDETRSmall()
images = [Image.open("a.jpg"), Image.open("b.jpg")]
results = model.predict(images, threshold=0.4, include_source_image=False)

for detections in results:
    print(list(detections.data["class_name"]))
```

Rules:

- A list input always returns a list, even when the list has one image.
- `include_source_image=False` reduces memory use and avoids carrying image arrays through output indexing.
- PIL paths and images are converted to RGB; tensor inputs must already be `(C, H, W)` and normalized to `[0, 1]`.

## Fine-tuned checkpoint prediction

```python
from rfdetr import RFDETR

model = RFDETR.from_checkpoint("checkpoint_best_total.pth")
detections = model.predict("validation-image.jpg", threshold=0.35)

for name, score in zip(detections.data["class_name"], detections.confidence):
    print(name, float(score))
```

Trust gate:

```python
# Only for checkpoint files from a fully trusted source.
model = RFDETR.from_checkpoint("legacy_or_custom_object_checkpoint.pth", trust_checkpoint=True)
```

Do not set `trust_checkpoint=True` just to silence an unknown-file error. First establish provenance; full pickle deserialization can execute arbitrary code.

## Shape override for rectangular inference

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall()
detections = model.predict("wide-image.jpg", shape=(512, 768), threshold=0.5)
```

Checklist:

- `shape` is `(height, width)`, not `(width, height)`.
- Both dimensions must be divisible by `patch_size * num_windows`.
- Detection Nano/Small/Medium/Large require multiples of 32.
- Segmentation Nano requires multiples of 12; other segmentation sizes and keypoint preview require multiples of 24.
- If an optimized compiled model already exists, the prediction shape must match that optimized resolution.

## Video file, webcam, and RTSP patterns

Use OpenCV for decoding. The same loop shape works for detection, segmentation, and keypoints; only the model class and annotator change.

```python
import cv2
import supervision as sv
from rfdetr import RFDETRSmall

model = RFDETRSmall()
video_capture = cv2.VideoCapture("video.mp4")  # or 0 for webcam, or an RTSP URL string
if not video_capture.isOpened():
    raise RuntimeError("Failed to open video source")

while True:
    success, frame_bgr = video_capture.read()
    if not success:
        break

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    detections = model.predict(frame_rgb, threshold=0.5, include_source_image=False)
    labels = list(detections.data["class_name"])

    annotated_frame = sv.BoxAnnotator().annotate(frame_bgr, detections)
    annotated_frame = sv.LabelAnnotator().annotate(annotated_frame, detections, labels)
    cv2.imshow("RF-DETR", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
```

Swap annotators by task:

| Task | Model | Primary annotator |
| --- | --- | --- |
| Detection | `RFDETRSmall` or another detection class | `sv.BoxAnnotator()` |
| Segmentation | `RFDETRSegSmall` or another segmentation class | `sv.MaskAnnotator()` |
| Keypoints | `RFDETRKeypointPreview` | `sv.VertexAnnotator()`, `sv.EdgeAnnotator()`, or ellipse annotators when covariance exists |

Video gotchas:

- OpenCV reads BGR; RF-DETR image arrays should be RGB.
- Always check `VideoCapture.isOpened()`.
- For RTSP, expect intermittent `read()` failures and handle reconnect policy outside the model call.
- Disable source-image storage in long streams unless annotation needs it.

## Memory and latency tuning

Low-risk first steps:

```python
detections = model.predict(image, include_source_image=False)
```

- Avoids storing source arrays in `Detections.metadata` or per-keypoint data.
- Helps with video/stream loops and large batches.

Inference optimization:

```python
model.inference(compile=False, dtype="float16")
```

- Creates an optimized inference snapshot while keeping the original module available.
- `dtype="float16"` is most useful on CUDA hardware with FP16 throughput.
- `compile=True` traces a fixed square resolution and batch size; mismatch later raises an error.

Destructive in-place optimization:

```python
model.inference(compile=False, inplace=True, dtype="float16")
```

Use only for inference-only deployments where memory is more important than reversibility:

- Requires `compile=False`.
- Clears the original `model.model.model` after success.
- `remove_optimized_model()` cannot restore the original module.
- Export/deploy and detection-head reinitialization are unavailable after the base model is cleared.
- To change resolution/batch/dtype after in-place optimization, create or reload a new RF-DETR instance.

Tensor-input optimization:

- CPU tensors headed to CUDA are pinned and transferred non-blocking internally.
- A tensor already on the model accelerator skips the image transfer, but `include_source_image=True` still forces a host copy for source storage. Use `include_source_image=False` for the lowest-copy path.
