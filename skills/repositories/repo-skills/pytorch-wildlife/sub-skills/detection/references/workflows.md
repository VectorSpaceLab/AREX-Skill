# Detection workflows

These recipes use only public package imports and caller-owned inputs. They do
not assume a package checkout, bundled demo data, or a downloaded model.

## Choose a device and local checkpoint

```python
import torch
from PytorchWildlife.models import detection as pw_detection

device = "cuda" if torch.cuda.is_available() else "cpu"
model = pw_detection.MegaDetectorV6(
    weights="/data/models/MDV6-yolov10-c.pt",
    device=device,
    version="MDV6-yolov10-c",
)
```

For a no-network run, replace the checkpoint with a real local file and do not
omit `weights`. A CPU run is the safest first validation even on a CUDA host.
For CUDA, verify `torch.cuda.is_available()`, select a valid device string, and
confirm the checkpoint/backend pair before processing a large directory.

## Single image from a path

```python
result = model.single_image_detection(
    "/data/camera_traps/capture.jpg",
    det_conf_thres=0.20,
)
dets = result["detections"]
for xyxy, confidence, class_id in zip(
    dets.xyxy, dets.confidence, dets.class_id
):
    name = model.CLASS_NAMES[int(class_id)]
    print(name, float(confidence), xyxy.tolist())
```

The returned boxes are in original-image pixel coordinates after the wrapper's
scaling. Preserve `result["img_id"]` as the join key. If caller code supplies
an ndarray, pass `img_path="frame-0001"` when a stable identifier is needed.

## Single RGB ndarray

```python
from PIL import Image
import numpy as np

rgb = np.asarray(Image.open("capture.jpg").convert("RGB"))
result = model.single_image_detection(rgb, img_path="capture.jpg")
```

Use `H x W x 3`, preferably `uint8`, RGB arrays. Do not pass a `3 x H x W`
tensor unless the selected wrapper explicitly documents that input; these
wrappers use image-array conventions and perform their own transforms.

## Folder batch

```python
results = model.batch_image_detection(
    "/data/camera_traps/",
    batch_size=16,
    det_conf_thres=0.20,
)
for result in results:
    # Use the returned path, not an assumed directory ordering.
    print(result.get("img_id"), len(result["detections"].xyxy))
```

The directory is scanned recursively for common image suffixes. The standard
Ultralytics path accepts `data_source` as either a directory or a list of RGB
HWC arrays. For a list, IDs are generated from sequence positions; supply a
separate mapping if those positions are not stable. V5, MIT, Apache, HerdNet,
and OWL folder paths are the most portable batch contract.

Use `batch_size=1` for HerdNet, OWL-C, and OWL-T. Their patch stitcher is
intended for one image at a time in the current implementation even though the
method exposes a batch-size argument. A larger value can silently discard all
but the first image processed by a loop iteration.

## HerdNet and overhead variants

```python
herd = pw_detection.HerdNet(
    weights="/data/models/herdnet-general.pth",
    device="cpu",
    version="general",
)
result = herd.single_image_detection(
    "aerial-herd.jpg", det_conf_thres=0.20, clf_conf_thres=0.20
)

owl = pw_detection.OWLC(
    weights="/data/models/owl-c.pth", device="cpu", version="general"
)
result = owl.single_image_detection("overhead.jpg", det_conf_thres=0.20)
```

Choose `version="ennedi"` for the HerdNet Ennedi checkpoint or
`version="caribou"` for the OWL-C Caribou checkpoint only when the data domain
matches. OWLT has no version selector. Their normal result still exposes a
`supervision.Detections` object, but labels/classes and coordinate conventions
are wrapper-specific. OWL's source class map uses animal class ID 1; inspect
`CLASS_NAMES` rather than filtering for MegaDetector's ID 0.

## Confidence policy

Start at `0.20` for recall-oriented camera-trap screening, then evaluate a
small representative validation set. Raise the threshold to suppress false
positives; lower it to preserve small or distant animals. For HerdNet, tune
classification and detection thresholds separately because both must pass.
Do not compare raw scores between different model families as if they were
calibrated probabilities.

## Chaining and output routing

To classify animal crops, pass the detector result to the classification
workflow; its crop dataset uses `detections`, `class_id`, and `img_id`. To
save annotated images, JSON, Timelapse records, crops, or separated folders,
route the result to `data-and-postprocessing`. Detection itself should remain
an in-memory operation unless the caller explicitly requests output files.

## Safe preflight

Before model construction, run the bundled checker from any directory:

```bash
python /path/to/check_detection_environment.py --json
```

It reports package version, import/signature availability, torch version, and
CUDA visibility without constructing a model or downloading weights. Run it in
the same environment that will execute inference. For an offline custom-weight
case, separately confirm that the checkpoint path exists and is readable; do
not use a default constructor as that check.
