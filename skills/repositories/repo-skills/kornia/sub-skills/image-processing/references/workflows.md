# Image-processing workflows

## Decode, normalize, process, save

```python
from pathlib import Path
import torch
import kornia.color as KC
import kornia.filters as KF
from kornia.io import ImageLoadType, load_image, write_image

img = load_image("input.png", ImageLoadType.RGB32, device="cpu")  # (3,H,W), float [0,1]
batch = img[None]
blurred = KF.gaussian_blur2d(batch, (5, 5), (1.5, 1.5))[0]
gray = KC.rgb_to_grayscale(blurred)

# PNG/JPEG writing expects uint8; use TIFF for float32 if you need to preserve floats.
write_image("gray.png", (gray.clamp(0, 1) * 255).to(torch.uint8))
```

## Compose differentiable preprocessing

Use Kornia functionals directly inside a model or wrap them in a small module.

```python
import torch
import torch.nn as nn
import kornia.color as KC
import kornia.filters as KF
import kornia.enhance as KE

class Preprocess(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = KE.normalize(x, mean=torch.zeros(3, device=x.device), std=torch.ones(3, device=x.device))
        edges = KF.sobel(x)
        gray = KC.rgb_to_grayscale(x)
        return torch.cat([gray, edges.mean(dim=1, keepdim=True)], dim=1)
```

Keep random transforms outside this deterministic preprocessing module unless you intentionally use the augmentation route.

## Morphology on masks

```python
import torch
import kornia.morphology as KM

mask = torch.rand(2, 1, 64, 64) > 0.5
mask = mask.float()
kernel = torch.ones(5, 5, device=mask.device)
closed = KM.closing(mask, kernel)
```

Morphology expects numeric tensors. Boolean masks should be converted to float when using differentiable-style pipelines.

## Visualize response maps

For feature or edge response maps, convert single-channel data into a displayable RGB tensor only after the compute path is complete.

```python
import kornia.color as KC
response = response.clamp(0, 1)          # (B,1,H,W)
rgb = KC.grayscale_to_rgb(response)      # (B,3,H,W)
```

## Validation checklist

- Input tensor has the expected number of spatial dimensions and channels.
- Values are in the range expected by the selected operator.
- Kernels and images are on the same device.
- Output shape, finite values, and channel count are asserted before passing to another sub-skill.
