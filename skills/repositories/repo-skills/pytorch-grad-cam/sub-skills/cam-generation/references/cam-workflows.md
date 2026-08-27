# Core CAM Workflows

## Minimal classification CAM

```python
import numpy as np
import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

model.eval()
target_layers = [model.layer4[-1]]        # choose a spatial layer
input_tensor = input_tensor.to(next(model.parameters()).device)
targets = [ClassifierOutputTarget(281)]   # one target per batch item

with GradCAM(model=model, target_layers=target_layers) as cam:
    grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
    model_outputs = cam.outputs

mask = grayscale_cam[0]
visualization = show_cam_on_image(rgb_float_0_to_1, mask, use_rgb=True)
```

If `targets=None`, the package uses the highest-scoring class for each batch
member. When `targets` is a list, keep its length aligned with the batch.

## Target layer choices

Common starting points:

| Model family | Starting layer |
| --- | --- |
| ResNet-18/50 | `model.layer4[-1]` or sometimes `model.layer4` |
| VGG / DenseNet / MobileNet | `model.features[-1]` |
| MNASNet | `model.layers[-1]` |
| Faster R-CNN | route to `model-task-adaptation`; target often involves the backbone/FPN |
| ViT / Swin | route to `model-task-adaptation` for a `reshape_transform` |

Use layers before classification heads and after enough spatial abstraction.
Passing several layers averages CAMs across them.

## Smoothing

```python
grayscale_cam = cam(
    input_tensor=input_tensor,
    targets=targets,
    aug_smooth=True,
    eigen_smooth=True,
)
```

- `aug_smooth=True` uses test-time augmentation (flips and brightness factors)
  and can be about six times slower.
- `eigen_smooth=True` projects weighted activations to remove noise.

## Guided backpropagation overlay

```python
import cv2
from pytorch_grad_cam import GuidedBackpropReLUModel
from pytorch_grad_cam.utils.image import deprocess_image

gb_model = GuidedBackpropReLUModel(model=model, device=str(next(model.parameters()).device))
gb = gb_model(input_tensor, target_category=None)
cam_mask = cv2.merge([mask, mask, mask])
cam_gb = deprocess_image(cam_mask * gb)
```

Use this when the user wants fine-grained pixel gradients combined with a CAM
mask. Keep image/channel order explicit (`use_rgb=True` when the image is RGB).

## Safe bundled smoke test

Run the bundled tiny model smoke instead of downloading pretrained weights:

```bash
python sub-skills/cam-generation/scripts/tiny_cam_smoke.py --method gradcam
python sub-skills/cam-generation/scripts/tiny_cam_smoke.py --method finercam --batch-size 2
```

The smoke asserts that the CAM output shape is `(batch, height, width)`.

## Performance notes

- `ScoreCAM` and `AblationCAM` can be much slower than gradient-weighted methods.
- Set `cam.batch_size` for `ScoreCAM`/`AblationCAM` to trade memory for speed.
- Use CPU for small diagnostic checks; use CUDA only when the package and model
  environment are already CUDA-compatible.
- Reuse a CAM object for repeated calls only while its hooks remain valid; use a
  `with` block to release hooks when finished.
