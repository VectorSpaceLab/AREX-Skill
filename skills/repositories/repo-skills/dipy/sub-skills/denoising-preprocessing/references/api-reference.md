# Denoising And Preprocessing API Reference

This reference covers Dipy denoising and preprocessing APIs future agents can use without opening the source checkout. File IO, gradient-file parsing, affine/header preservation, and tractogram/PAM handling are routed to `../../io-data/`.

## Array And Gradient Invariants

| Item | Contract | Validate before running |
| --- | --- | --- |
| DWI data | 4D array with spatial axes first and diffusion volumes on the last axis: `(X, Y, Z, N)`. | `data.ndim == 4`; `len(bvals) == data.shape[-1]`; finite values; positive values when downstream log or bias routines are used. |
| 3D image | 3D scalar image for NLMeans, Gibbs, masks, or mean-b0 style checks. | `arr.ndim == 3`; expected spatial shape and finite values. |
| Mask | 3D boolean-like mask for brain/preprocessing region. | `mask.shape == data.shape[:3]` or `arr.shape`; `np.count_nonzero(mask) > 0`; convert to bool for validation. |
| Sigma | Noise standard deviation as scalar, per-volume vector, 3D map, or PCA-specific 3D map depending on API. | Shape exactly matches the API rules below; values are finite and nonnegative. |
| Patch radius | PCA radius is scalar or length-3 spatial radius; Patch2Self v3 supports only `(0, 0, 0)`. | Spatial dimensions are at least `2 * patch_radius + 1` unless a dimension is singleton. |
| Gradient table | Required when LPCA estimates sigma internally and for DWI bias correction. | `gtab.b0s_mask.any()` for bias correction; b0 threshold matches acquisition; non-b0 b-vectors are unit length. |

## Noise Estimation

| API | Use | Key options | Returns and checks |
| --- | --- | --- | --- |
| `dipy.denoise.noise_estimate.estimate_sigma(arr, *, disable_background_masking=False, N=0)` | Fast global sigma estimate for 3D or 4D magnitude images. | `N` is receiver-coil correction: `0` disables correction, `1` for SENSE-like Rician, supported values include `1, 4, 6, 8, 12, 16, 20, 24, 32, 64`. | Returns one sigma per input volume; shape `(1,)` for 3D and `(Nvols,)` for 4D. Rejects unsupported array rank and unsupported `N`. |
| `dipy.denoise.noise_estimate.piesno(data, N, *, alpha=0.01, step=100, itermax=100, eps=1e-5, return_mask=False)` | Probabilistic noise estimation for data with a non-masked noisy background and repeated measurements on the last axis. | Use when PIESNO assumptions hold; `N` can use the known optimal quantiles or falls back to median. | Returns sigma, optionally a pure-noise mask. Rejects arrays with fewer than 3 dimensions. |
| `dipy.denoise.pca_noise_estimate.pca_noise_estimate(data, gtab, patch_radius=1, correct_bias=True, smooth=2, images_as_samples=False)` | Local 3D sigma map for PCA denoising from gradient-aware DWI data. | Needs 4D data and `gtab`; `patch_radius < 1` is reset to 1 with warning; `correct_bias=True` applies Rician bias correction. | Returns a 3D sigma map. Rejects spatial dimensions too small for the patch. |

## Denoising APIs

| API | Use | Key options | Returns and checks |
| --- | --- | --- | --- |
| `dipy.denoise.nlmeans.nlmeans(arr, sigma, *, mask=None, patch_radius=1, block_radius=None, rician=True, num_threads=None, method='blockwise')` | Non-local means denoising for 3D or 4D images when a sigma estimate is available or can be estimated first. | `method` is `blockwise` or `classic`; default `block_radius` is `2` for blockwise and `5` for classic; `rician=True` for magnitude MRI; `num_threads=1` for deterministic small probes. | Output shape and dtype match input. For 4D, sigma may be scalar, length-`N` vector, or 3D spatial map. Mask must be 3D. |
| `dipy.denoise.localpca.localpca(arr, *, sigma=None, mask=None, patch_radius=2, gtab=None, patch_radius_sigma=1, pca_method='eig', tau_factor=2.3, return_sigma=False, correct_bias=True, out_dtype=None, suppress_warning=False)` | Local PCA denoising with a known sigma or an internally estimated sigma. | If `sigma is None`, pass `gtab`; `pca_method` is `eig` or `svd`; `tau_factor=None` uses a random-matrix threshold; `return_sigma=True` returns sigma alongside denoised data. | Requires 4D data. Scalar sigma or 3D sigma map accepted. Mask outside voxels are zeroed. Rejects wrong patch, sigma, rank, or PCA method. |
| `dipy.denoise.localpca.mppca(arr, *, mask=None, patch_radius=2, pca_method='eig', return_sigma=False, out_dtype=None, suppress_warning=False)` | Marcenko-Pastur PCA denoising when noise is unknown and enough volumes are available for local PCA. | `patch_radius` controls local sample count; `pca_method='eig'` is faster, `svd` can be used for comparison. | Requires 4D data. With `return_sigma=True`, returns `(denoised, sigma_map)`. Same patch and mask rules as LPCA. |
| `dipy.denoise.patch2self.patch2self(data, bvals, *, patch_radius=(0,0,0), model='ols', b0_threshold=50, out_dtype=None, alpha=1.0, verbose=False, b0_denoising=True, clip_negative_vals=False, shift_intensity=True, tmp_dir=None, version=3, gram=True)` | Self-supervised DWI denoising from the noisy DWI itself. | `model` is `ols`, `ridge`, `lasso`, or a scikit-learn estimator-like object; `version=3` is default and does not accept nonzero `patch_radius`; `version=1` can use scalar or length-3 patch radius and `gram` acceleration for supported models. | Requires 4D data and `len(bvals) == data.shape[-1]`. Warns for fewer than 10 volumes. Output shape matches input. |
| `dipy.denoise.gibbs.gibbs_removal(vol, *, slice_axis=2, n_points=3, inplace=True, num_processes=1)` | Suppress Gibbs ringing in 2D, 3D, or 4D images before quantitative modeling. | `slice_axis` must be one of the first three axes; set `inplace=False` unless modifying the input array is intentional; `num_processes=0` is invalid. | Output has the same shape. Rejects 1D/5D arrays, invalid slice axis, non-bool `inplace`, or invalid process count. |

## Bias Correction APIs

| API | Use | Key options | Returns and checks |
| --- | --- | --- | --- |
| `dipy.denoise.bias_correction.bias_field_correction(data, gtab, *, mask=None, method='bspline', order=3, n_control_points=(8,8,8), pyramid_levels=(4,2,1), n_iter=4, lambda_reg=0.001, robust=True, gradient_weighting=True, return_bias_field=False, zero_background=False)` | Correct smooth multiplicative DWI bias estimated from mean b0 volumes and applied uniformly to all volumes. | `method`: `poly`, `bspline`, or `auto`; `poly` is faster for smooth global bias, `bspline` is more flexible, `auto` runs both and picks lower in-mask coefficient of variation. | Requires 4D DWI and a `GradientTable` with b0 volumes. Output dtype matches input. With `return_bias_field=True`, returns `(corrected, bias_field)` where `bias_field.shape == data.shape[:3]`. |
| `dipy.workflows.nn.BiasFieldCorrectionFlow` via `dipy_correct_biasfield` | File-producing CLI workflow for DWI poly/bspline/auto or optional DeepN4. | For DWI methods pass `bval` and `bvec`; `method='n4'` is for T1-like images and can fetch/use neural-network weights. | DWI methods save corrected image and bias field. Treat `n4` as optional/model-asset-dependent. |

## Minimal API Patterns

### NLMeans With Estimated Sigma

```python
import numpy as np
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.nlmeans import nlmeans

arr = np.asarray(arr, dtype=np.float32)
sigma = estimate_sigma(arr, N=0)
denoised = nlmeans(arr, sigma=sigma, rician=True, method="blockwise", num_threads=1)
assert denoised.shape == arr.shape
```

### LPCA With A Known Sigma

```python
from dipy.denoise.localpca import localpca

assert data.ndim == 4
assert mask.shape == data.shape[:3]
denoised = localpca(data, sigma=float_sigma, mask=mask, patch_radius=1, pca_method="eig")
assert denoised.shape == data.shape
```

### Patch2Self Safe Validation

```python
from dipy.denoise.patch2self import patch2self

assert data.ndim == 4
assert len(bvals) == data.shape[-1]
denoised = patch2self(data, bvals, model="ols", version=3, patch_radius=(0, 0, 0))
assert denoised.shape == data.shape
```

### DWI Bias Correction

```python
from dipy.denoise.bias_correction import bias_field_correction

assert data.ndim == 4
assert mask.shape == data.shape[:3]
corrected, bias = bias_field_correction(
    data, gtab, mask=mask, method="poly", pyramid_levels=(2, 1),
    n_iter=1, return_bias_field=True,
)
assert corrected.shape == data.shape and bias.shape == data.shape[:3]
```
