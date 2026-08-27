# Inference workflow

This workflow is safe for planning and inspection. Do not claim that a modern PyTorch runtime can run test-phase SSD inference unchanged until the `Detect` compatibility point below is resolved.

## 1. Make repository modules importable

Run commands from the repository root or set `PYTHONPATH` so that `ssd.py`, `data/`, and `layers/` are importable.

A common import pitfall is the COCO label-map side effect: importing `ssd` imports `data`, and importing `data` imports the COCO dataset module. The COCO dataset constructor has a default `COCOAnnotationTransform()` argument that opens `data/coco/coco_labels.txt` under the user's home data directory at import time. If that file is missing, even VOC model construction can fail before reaching `build_ssd`. See `troubleshooting.md` for remedies.

## 2. Choose class count and weights together

For VOC pretrained weights from the README, use:

```python
num_classes = 21  # 20 VOC classes + background
net = build_ssd('test', 300, num_classes)
```

The README lists VOC SSD300 pretrained state dicts such as:

- `ssd300_mAP_77.43_v2.pth`
- `ssd_300_VOC0712.pth`

Weight files are not bundled by the skill and should be supplied by the user. The state dict must match both the architecture and `num_classes`; a VOC head cannot be loaded into a different class-count model without remapping or replacing the confidence heads.

The repository has an `SSD.load_weights(base_file)` helper, but the condition `if ext == '.pkl' or '.pth':` is always truthy because `'.pth'` is a non-empty string. Prefer direct, explicit loading so you control `map_location` and error handling:

```python
import torch
from ssd import build_ssd

net = build_ssd('test', 300, 21)
state = torch.load('weights/ssd_300_VOC0712.pth', map_location='cpu')
net.load_state_dict(state)
net.eval()
```

If a checkpoint was saved from `torch.nn.DataParallel`, strip a leading `module.` prefix before loading.

## 3. Decide how to handle `Detect` before running test-phase forward

`build_ssd('test')` attaches:

```python
self.softmax = nn.Softmax(dim=-1)
self.detect = Detect(num_classes, 0, 200, 0.01, 0.45)
```

On modern PyTorch, the repository's old-style `Detect(Function)` can raise an error like:

```text
Legacy autograd function with non-static forward method is deprecated.
```

Choose one of these paths:

1. **Patch for modern PyTorch before inference/evaluation.** Convert `Detect` into a regular callable/module-style class or a new-style autograd function. For inference, gradients are not required, so a small `nn.Module` or plain class that implements `__call__`/`forward` with the existing tensor code is usually enough.
2. **Use a legacy-compatible PyTorch environment.** This may match the era of the repository but can be difficult to combine with current Python/CUDA versions.
3. **Inspect train-phase outputs only.** Use `build_ssd('train')` to inspect raw `loc`, `conf`, and `priors`, then apply your own decode/NMS code outside the legacy `Detect` wrapper.

Do not run full demo/eval workflows until this decision is made; route those workflows to `../evaluation-demos/SKILL.md` after the model path is compatible.

## 4. Preprocess one image

The source data transform resizes an image to 300 x 300 and subtracts a mean. Images read by OpenCV are BGR arrays.

For VOC-style test/evaluation code, the mean is:

```python
MEANS = (104, 117, 123)
```

Minimal preprocessing pattern:

```python
import cv2
import torch
from data import BaseTransform

image = cv2.imread('image.jpg', cv2.IMREAD_COLOR)  # BGR, H x W x 3
height, width = image.shape[:2]
transform = BaseTransform(300, (104, 117, 123))
x = torch.from_numpy(transform(image)[0]).permute(2, 0, 1).unsqueeze(0)
x = x.float()
```

Notes:

- `BaseTransform` returns `(image, boxes, labels)`; use element `[0]` for the image array.
- Keep the tensor and model on the same device.
- Avoid `torch.set_default_tensor_type('torch.cuda.FloatTensor')` unless you are deliberately following the legacy scripts; explicit `.to(device)` is easier to reason about.
- The webcam demo used `(104/256.0, 117/256.0, 123/256.0)` as its mean, while `test.py` and dataset config use `(104, 117, 123)`. For static image inference with README VOC weights, prefer the repository-wide `MEANS` tuple unless reproducing the webcam script exactly.

## 5. Forward and postprocess

After resolving the `Detect` compatibility issue:

```python
with torch.no_grad():
    detections = net(x)
```

Expected test output shape:

```text
(batch, num_classes, top_k, 5)
```

For each class index `cl >= 1`, each retained row is:

```text
score, xmin, ymin, xmax, ymax
```

Coordinates are normalized. Scale them back to the original image size:

```python
scale = torch.tensor([width, height, width, height], dtype=detections.dtype)
boxes_xyxy = detections[0, cl, :, 1:] * scale
scores = detections[0, cl, :, 0]
mask = scores >= visual_threshold
```

VOC class names are zero-based foreground labels in `VOC_CLASSES`, so detection class `cl` maps to `VOC_CLASSES[cl - 1]`.

## 6. Inspection without weights or data

Use the bundled helper scripts from this sub-skill directory:

```bash
python scripts/inspect_model_shapes.py --phase train --num-classes 21
python scripts/inspect_model_shapes.py --phase train --num-classes 21 --run-forward
python scripts/check_box_utils.py
```

These checks are low-cost and do not require datasets or pretrained weights. They are intended to verify importability, model construction, prior shape, and box utility behavior, not full mAP or demo quality.
