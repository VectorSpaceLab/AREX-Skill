# FCOS Inference Workflows

## Installed CLI workflow

The installed package provides a script named `fcos` that accepts one image path or URL. It constructs the MobileNetV2 high-level detector, reads the image, resizes it to short side 800, prints detections, and opens a display window.

For automated agents, avoid the GUI behavior by using the bundled safe wrapper:

```bash
python sub-skills/inference-demo/scripts/fcos_cli_safe_wrapper.py image.jpg --model-name fcos_syncbn_bs32_c128_MNV2_FPN_1x --cpu-only --dry-run
```

Add `--run` only when imports, weights, display constraints, and runtime cost are acceptable. The wrapper prints JSON-style detections instead of opening a window.

## Python API workflow

```python
import cv2
from fcos import FCOS

image = cv2.imread("image.jpg")  # BGR
model = FCOS(model_name="fcos_syncbn_bs32_c128_MNV2_FPN_1x", nms_thresh=0.6, cpu_only=True)
results = model.detect(image, min_confidence=0.5)
for item in results:
    print(item["label_name"], item["score"], item["box"])
```

Use `cpu_only=False` only when CUDA is available and the package was built for it. If the image came from PIL, skimage, or imageio, convert RGB to BGR exactly once before calling `detect`.

## Image preparation workflow

Validate and resize a local image without constructing the detector:

```bash
python sub-skills/inference-demo/scripts/prepare_image_for_fcos.py image.jpg --output prepared-bgr.npy --short-side 800
```

The output `.npy` file is a BGR `uint8` array that can be loaded and passed to `FCOS.detect`.

## Headless/no-display workflow

Do not call `show_bboxes` or the original installed CLI in a headless environment. Use `detect` and serialize results. If rendered images are required, draw boxes with OpenCV/Pillow and write a file instead of calling `cv2.imshow`.

## Webcam workflow

The webcam demo requires camera hardware, a display session, compatible OpenCV backend, model weights, and usually a GPU. Treat it as an interactive workflow; do not run it as a default verification or unattended task.
