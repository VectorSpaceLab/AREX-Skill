# fastMRI MRI Operator Troubleshooting

Use this guide when tensor operators fail before or during reconstruction, loss, or metric code.

## `Tensor does not have separate complex dim.`

Cause:

- `fastmri.fft2c`, `ifft2c`, `complex_abs`, `complex_abs_sq`, `complex_conj`, and related helpers require `data.shape[-1] == 2`.
- Native PyTorch complex tensors such as `torch.complex64` have no final real/imaginary dimension.

Fix:

```python
if torch.is_complex(data):
    data = torch.view_as_real(data)
if data.ndim < 3 or data.shape[-1] != 2:
    raise ValueError(f"expected fastMRI complex layout (..., height, width, 2), got {tuple(data.shape)}")
```

For NumPy inputs, prefer `fastmri.data.transforms.to_tensor(np_array)`, which stacks real and imaginary parts for complex NumPy arrays.

## FFT Looks Shifted or Uses Wrong Axes

Cause:

- `fastmri.fft2c` and `fastmri.ifft2c` treat dimensions `-3` and `-2` as spatial dimensions and dimension `-1` as real/imaginary values.
- A tensor shaped like `(height, width)` or `(batch, height, width)` is real-valued, not fastMRI complex layout.
- Accidentally moving coil or batch dimensions into `-3` or `-2` changes which axes are transformed.

Fix:

- Keep complex data as `(..., height, width, 2)`.
- Use `torch.view_as_real(native_complex)` if starting from a native complex tensor.
- When shifting manually, use `fastmri.fftshift(x, dim=[-3, -2])` or `fastmri.ifftshift(x, dim=[-3, -2])` to avoid shifting the final complex dimension.

## Center Crop Raises `Invalid shapes.`

Cause:

- `transforms.center_crop(data, shape)` crops the last two dimensions of real data.
- `transforms.complex_center_crop(data, shape)` crops dimensions `-3` and `-2` of complex data.
- The requested crop must be positive and no larger than the corresponding data dimensions.

Fix:

```python
height = min(pred.shape[-2], target.shape[-2])
width = min(pred.shape[-1], target.shape[-1])
pred = transforms.center_crop(pred, (height, width))
target = transforms.center_crop(target, (height, width))
```

For complex tensors, compute `height` and `width` from `shape[-3]` and `shape[-2]`, then use `complex_center_crop`.

## Dtype or Device Mismatch

Cause:

- PyTorch arithmetic and `torch.fft` require tensors in the same operation to be on compatible devices and dtypes.
- `SSIMLoss` stores its convolution window as a module buffer; the module must be moved to the same device as inputs.
- `torch.view_as_complex` expects a valid real tensor layout with final dimension size `2`.

Fix:

```python
device = prediction.device
target = target.to(device=device, dtype=prediction.dtype)
data_range = data_range.to(device=device, dtype=prediction.dtype)
loss_fn = fastmri.SSIMLoss().to(device)
loss = loss_fn(prediction, target, data_range)
```

For operator checks, start with CPU `float32` or `float64` tensors and move all inputs together after shape validation.

## RSS Has the Wrong Output Shape

Cause:

- `fastmri.rss` and `fastmri.rss_complex` reduce the `dim` argument.
- The default `dim=0` is not correct for batched multicoil tensors shaped like `(batch, coils, height, width)` or `(batch, coils, height, width, 2)`.

Fix:

```python
real_coils = torch.zeros(2, 8, 64, 64)
combined = fastmri.rss(real_coils, dim=1)
assert combined.shape == (2, 64, 64)

complex_coils = torch.zeros(2, 8, 64, 64, 2)
combined = fastmri.rss_complex(complex_coils, dim=1)
assert combined.shape == (2, 64, 64)
```

## SSIM Loss Shape Errors

Cause:

- `fastmri.SSIMLoss` uses `conv2d`, so predictions and targets should be image tensors shaped like `(batch, channel, height, width)`.
- `data_range` is indexed as `data_range[:, None, None, None]`, so it must have one value per batch item.
- Prediction and target spatial dimensions must match.

Fix:

```python
pred, target = transforms.center_crop_to_smallest(pred, target)
pred = pred[:, None] if pred.ndim == 3 else pred
target = target[:, None] if target.ndim == 3 else target
data_range = target.amax(dim=(-2, -1)).reshape(target.shape[0])
data_range = torch.clamp(data_range, min=1e-8)
loss = fastmri.SSIMLoss().to(pred.device)(pred, target.to(pred), data_range.to(pred))
```

## Array Metric Shape Errors

Cause:

- `fastmri.evaluate.ssim(gt, pred)` requires a 3D ground-truth array and prediction dimensions matching the ground truth exactly.
- `psnr` and `ssim` default to `gt.max()` for data range.
- The file-level evaluator square-crops target and reconstruction arrays before metrics; direct metric calls do not automatically crop mismatched arrays.

Fix:

```python
from fastmri.data import transforms

gt_t = torch.as_tensor(gt)
pred_t = torch.as_tensor(pred)
gt_t, pred_t = transforms.center_crop_to_smallest(gt_t, pred_t)
gt = gt_t.numpy()
pred = pred_t.numpy()
if gt.ndim != 3 or pred.shape != gt.shape:
    raise ValueError(f"expected matching 3D arrays, got gt={gt.shape}, pred={pred.shape}")
maxval = float(np.nanmax(gt))
if not np.isfinite(maxval) or maxval <= 0:
    maxval = 1.0
score = fastmri.evaluate.ssim(gt, pred, maxval=maxval)
```

## Non-finite or Zero Max Value Metrics

Cause:

- `psnr` and `ssim` use `gt.max()` as `data_range` when `maxval` is omitted.
- Zero or non-finite targets can produce surprising PSNR/SSIM values or warnings.
- `nmse` divides by `np.linalg.norm(gt) ** 2`.

Fix:

- Replace or reject non-finite values before metrics with `np.nan_to_num` or explicit validation.
- Pass a finite positive `maxval` when the target maximum is unsuitable.
- Skip or separately report NMSE for all-zero ground truth arrays.

## `ModuleNotFoundError: No module named 'requests'`

Cause:

- `fastmri.data` imports `requests`, but some package metadata for this checkout may not declare it as an install dependency.

Fix:

- If a task only needs top-level MRI operators, try importing `fastmri` first and avoid data-loading utilities.
- If the task needs `fastmri.data.transforms` or dataset code, install `requests` in the active project environment according to the user's dependency-management policy.
- For runtime validation, the smoke script imports `fastmri.data.transforms` for center crop, so this missing dependency can surface even without HDF5 data access.
