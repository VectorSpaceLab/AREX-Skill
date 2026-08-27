# Discrete Transform Workflows

## When to read

Read this when you need a practical recipe for DWT/IDWT, multilevel transforms, coefficient packing, SWT/MRA, padding, thresholding, or fully separable transforms.

## 1D DWT / IDWT

1. Pick a small wavelet such as `db1` or `db2`.
2. Use `mode='symmetric'` unless the task explicitly needs a different boundary rule.
3. Call `pywt.dwt(x, wavelet, mode)` and inspect `(cA, cD)`.
4. Reconstruct with `pywt.idwt(cA, cD, wavelet, mode)`.
5. If the result length is surprising, use `pywt.dwt_coeff_len(...)` before hand-building coefficient arrays.

Example:

```python
import numpy as np
import pywt

x = np.array([3, 7, 1, 1, -2, 5, 4, 6], dtype=float)
cA, cD = pywt.dwt(x, 'db2')
rec = pywt.idwt(cA, cD, 'db2')
```

## 2D and ND transforms

- Use `dwt2` / `idwt2` for the common 2D image layout.
- Use `dwtn` / `idwtn` when the task needs named coefficient dictionaries.
- Use `wavedec2` / `waverec2` or `wavedecn` / `waverecn` for multilevel image or volume workflows.
- Keep the transform axes explicit when the data is not transformed over all axes.

Typical patterns:

```python
coeffs = pywt.wavedec2(img, 'db1', level=2)
restored = pywt.waverec2(coeffs, 'db1')

coeffs_n = pywt.wavedecn(volume, 'db1', axes=(0, 2))
restored_n = pywt.waverecn(coeffs_n, 'db1', axes=(0, 2))
```

## Coefficient packing

Use coefficient packing when another system wants one array plus slices.

- `coeffs_to_array` / `array_to_coeffs` keep the shaped layout.
- `ravel_coeffs` / `unravel_coeffs` flatten the coefficients to 1D.
- If the coefficient tree is not tightly packable, allow zero padding or use `padding=np.nan` for visibility.
- If the transform only used a subset of axes, pass the same `axes=` value back into the packing helper.

## SWT and MRA

- `swt`/`swt2`/`swtn` require the transformed length(s) to be compatible with `2**level`.
- `periodization` is the safe mode family for SWT-based MRA.
- For orthogonal wavelets, `norm=True` plus `trim_approx=True` gives the cleanest variance/energy bookkeeping.
- `mra`, `mra2`, and `mran` return additive coefficient arrays that `imra`, `imra2`, and `imran` sum back together.

## Thresholding and padding

- Use `threshold(..., 'soft')` for the usual shrinkage behavior.
- Use `threshold(..., 'hard')` when coefficients should be zeroed but not shrunk.
- Use `threshold_firm` when you want a smoother transition between soft and hard behavior.
- Use `pad` when you need to inspect the explicit boundary extension that a transform would use.

## Fully separable transforms

Use `fswavedecn` when the axes should be decomposed one axis at a time.

```python
fs = pywt.fswavedecn(np.ones((4, 4)), 'haar', levels=1)
restored = pywt.fswaverecn(fs)
```

The returned `FswavedecnResult` is the object to inspect; it is not the same as a `wavedecn` coefficient list.

## Bundled smoke fixtures

- `pywt.data.ecg()` is good for 1D transform and threshold checks.
- `pywt.data.camera()` is good for 2D and ND image workflows.
- `pywt.data.nino()` is useful for CWT-adjacent transform planning even though CWT itself belongs to the wavelet/CWT sub-skill.
