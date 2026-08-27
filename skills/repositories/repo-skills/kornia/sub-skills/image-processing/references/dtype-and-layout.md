# Dtype and layout rules

## Tensor layout

Kornia image-processing APIs are PyTorch-first. Most image functions accept one image as `(C, H, W)` or batches as `(B, C, H, W)`. Some lower-level functions accept arbitrary leading dimensions before the final spatial axes, but BCHW is the safest convention for agents composing workflows.

Common conversions:

| Situation | Preferred handling |
| --- | --- |
| NumPy/PIL/OpenCV image in HWC | Convert to tensor and permute to CHW/BCHW before calling Kornia. |
| Single image `(C,H,W)` used with a batch-only op | Add a batch dimension with `image[None]`, then remove it if needed. |
| Grayscale image `(H,W)` | Add a channel dimension when the selected operator expects channels. |
| Batch image `(B,H,W,C)` from another library | Move channels to dimension 1 before Kornia calls. |

## Value range

- `ImageLoadType.RGB32` and `ImageLoadType.GRAY32` return float32 images scaled to `[0, 1]`.
- Most differentiable image-processing examples assume float tensors in `[0, 1]`.
- A float tensor in `[0, 255]` is not the same as a uint8 image. Scale it explicitly (`x.float() / 255`) or convert to uint8 only for file writing/backends that require uint8.
- `write_image` can write uint8 PNG/JPEG/TIFF. Float32 image writing is limited to TIFF; for PNG/JPEG convert to uint8 first.

## Device and dtype

- Kornia follows PyTorch device placement: operations run where the input tensor lives.
- CPU is sufficient for correctness checks; CUDA is an accelerator, not a different API.
- Half precision support is partial. Convolution/pooling-style morphology and many filters work, while FFT, linalg, and some geometric/feature paths may fail or need internal casting.
- Keep exact-reference tests in float32 or float64 unless a low-precision behavior is the subject of the task.

## Shape/range assertion pattern

```python
import torch
import kornia.filters as KF

x = torch.rand(2, 3, 32, 48)  # B,C,H,W in [0,1]
y = KF.gaussian_blur2d(x, (3, 3), (1.2, 1.2))
assert y.shape == x.shape
assert torch.isfinite(y).all()
```

When an operator changes channels or spatial shape, assert the exact expected result immediately after the call so downstream failures point to the conversion step.
