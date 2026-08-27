# fastMRI MRI Operator API Reference

This reference covers safe use of fastMRI's tensor-level MRI operators. Prefer top-level `fastmri` imports for the public operator API:

```python
import torch
import fastmri
from fastmri.data import transforms
```

## Complex Tensor Convention

fastMRI represents complex PyTorch tensors as real tensors with the final dimension storing real and imaginary values:

- Valid complex tensor shape: `(..., height, width, 2)`.
- The final dimension must have size `2`; native PyTorch complex dtypes are not accepted by fastMRI helpers directly.
- `fastmri.tensor_to_complex_np(data)` converts a fastMRI-style tensor to a NumPy complex array through `torch.view_as_complex(data)`.
- `transforms.to_tensor(np_complex_array)` converts a complex NumPy array to the fastMRI real/imaginary layout.

Validation snippet:

```python
def require_fastmri_complex(data):
    if data.ndim < 3 or data.shape[-1] != 2:
        raise ValueError(f"expected (..., height, width, 2), got {tuple(data.shape)}")
    return data
```

Native PyTorch complex conversion:

```python
native = torch.zeros(4, 8, dtype=torch.complex64)
fastmri_layout = torch.view_as_real(native)
image = fastmri.complex_abs(fastmri_layout)
```

## Centered FFT and IFFT

Use:

- `fastmri.fft2c(data, norm="ortho") -> torch.Tensor`
- `fastmri.ifft2c(data, norm="ortho") -> torch.Tensor`

Requirements:

- `data.shape[-1] == 2`.
- Spatial dimensions are `data.shape[-3]` and `data.shape[-2]`.
- Leading dimensions are batch, coil, slice, or other non-spatial dimensions.
- Input dtype/device must be compatible with `torch.fft` after `torch.view_as_complex`.

Behavior:

- `ifftshift` is applied over spatial dims before FFT/IFFT.
- `torch.fft.fftn` or `torch.fft.ifftn` is applied over the two spatial complex dimensions.
- `fftshift` is applied over spatial dims after FFT/IFFT.
- The output keeps the same real/imaginary final dimension layout.

Round-trip shape check:

```python
kspace = torch.zeros(2, 16, 20, 2)
image = fastmri.ifft2c(kspace)
back = fastmri.fft2c(image)
assert image.shape == kspace.shape
assert back.shape == kspace.shape
```

## Shift and Roll Helpers

Use:

- `fastmri.roll(x, shift=[...], dim=[...])`
- `fastmri.fftshift(x, dim=None)`
- `fastmri.ifftshift(x, dim=None)`

Notes:

- `roll` requires `len(shift) == len(dim)`.
- `fftshift` with `dim=None` shifts all dimensions.
- For MRI complex tensors, use `dim=[-3, -2]` when you intend to shift only the spatial dimensions and not the final real/imaginary dimension.

## Complex Math

Use:

- `fastmri.complex_abs(data)` returns magnitude and removes the final complex dimension.
- `fastmri.complex_abs_sq(data)` returns squared magnitude and removes the final complex dimension.
- `fastmri.complex_mul(x, y)` multiplies two fastMRI-style complex tensors and returns the same layout.
- `fastmri.complex_conj(x)` conjugates a fastMRI-style complex tensor.
- `fastmri.tensor_to_complex_np(data)` returns a NumPy complex array.

All complex math helpers require the final dimension size `2`; `complex_mul` requires both operands to follow that convention.

## RSS Coil Combine

Use:

- `fastmri.rss(data, dim=0)` for real-valued magnitudes or coil images.
- `fastmri.rss_complex(data, dim=0)` for fastMRI-style complex coil tensors.

The `dim` argument is the coil dimension and is reduced. The default `dim=0` is correct only when coils are dimension `0`.

Examples:

```python
coil_images = torch.zeros(8, 320, 320)
combined = fastmri.rss(coil_images, dim=0)
assert combined.shape == (320, 320)

batched_complex = torch.zeros(2, 8, 320, 320, 2)
combined = fastmri.rss_complex(batched_complex, dim=1)
assert combined.shape == (2, 320, 320)
```

## Crops and Normalization

Use:

- `transforms.center_crop(data, shape)` for real image tensors; crops the last two dimensions.
- `transforms.complex_center_crop(data, shape)` for fastMRI-style complex tensors; crops dimensions `-3` and `-2` and preserves final size `2`.
- `transforms.center_crop_to_smallest(x, y)` for real-valued tensors before array loss or metric comparisons.
- `transforms.normalize_instance(data, eps=0.0)` returns `(normalized, mean, std)` using statistics from `data`.

Crop shape must be positive and no larger than the target dimensions. For complex crop, validate `(..., height, width, 2)` first.

Metric prep snippet:

```python
pred, target = transforms.center_crop_to_smallest(pred, target)
pred = torch.nan_to_num(pred)
target = torch.nan_to_num(target)
```

## SSIM Loss

Use `fastmri.SSIMLoss(win_size=7, k1=0.01, k2=0.03)` for tensor loss. Its forward call is:

```python
loss = fastmri.SSIMLoss()(prediction, target, data_range)
```

Shape expectations from the implementation:

- `prediction` and `target` should be 4D image tensors accepted by `torch.nn.functional.conv2d`, commonly `(batch, channel, height, width)`.
- `data_range` should have one value per batch item because the loss reshapes it as `data_range[:, None, None, None]`.
- `reduced=True` returns scalar `1 - SSIM.mean()`; `reduced=False` returns the per-window loss map.

## Array Metrics

`fastmri.evaluate` exposes array-level metric helpers:

- `mse(gt, pred)` computes mean squared error.
- `nmse(gt, pred)` computes squared error norm divided by ground-truth norm squared.
- `psnr(gt, pred, maxval=None)` uses `gt.max()` as `data_range` when `maxval` is omitted.
- `ssim(gt, pred, maxval=None)` requires `gt.ndim == 3` and `pred.ndim == gt.ndim`, then averages per-slice structural similarity.

Before using array metrics:

- Ensure ground truth and prediction dimensions match exactly.
- Center-crop predictions and targets to the same square or challenge-specific crop when needed.
- Pass a positive finite `maxval` if `gt.max()` is zero, non-finite, or not the desired data range.
- Watch for `nmse` divide-by-zero when the ground truth norm is zero.

The file-level evaluator crops target and prediction arrays to a square based on the target's final dimension before pushing metrics. For file-level evaluation and submissions, use the evaluation-submission sub-skill instead of duplicating that workflow here.

## Minimal Operator Pipeline

```python
import torch
import fastmri
from fastmri.data import transforms

kspace = torch.zeros(8, 64, 64, 2)
require_fastmri_complex(kspace)
image_complex = fastmri.ifft2c(kspace)
image_complex = transforms.complex_center_crop(image_complex, (32, 32))
image_mag = fastmri.complex_abs(image_complex)
image_rss = fastmri.rss(image_mag, dim=0)
image_norm, mean, std = transforms.normalize_instance(image_rss, eps=1e-11)
assert image_norm.shape == (32, 32)
```
