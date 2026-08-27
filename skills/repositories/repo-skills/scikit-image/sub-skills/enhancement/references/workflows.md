# Enhancement Workflows

This guide covers common color, exposure, filter, and restoration tasks. The main decision points are:

- whether the data should stay in its native numeric range or be normalized,
- whether the array has a channel axis,
- whether the task is tone/contrast adjustment, smoothing, or restoration.

## 1. Decide scale and channel layout first

- Use `channel_axis` for every multichannel array.
- Use `None` for grayscale or scalar data.
- Use `preserve_range=True` whenever the function exposes it and the values should remain in native units.
- Convert to float intentionally when an algorithm expects normalized data.

```python
import numpy as np
from skimage import data, img_as_float

image = data.astronaut()
print(image.shape, image.dtype, image.min(), image.max())
image = img_as_float(image)
```

If the pixel values are measurements rather than display intensities, keep that meaning explicit throughout the pipeline.

## 2. Color conversion and display

Use color conversion when the next step depends on a different channel representation.

- `rgb2gray` for scalar analysis or thresholding.
- `gray2rgb` and `gray2rgba` for display or compatibility.
- `rgba2rgb` when you need to remove alpha by blending.
- `rgb2hsv` / `hsv2rgb` when hue, saturation, and value are the useful axes.
- `label2rgb` when you already have labels and only need to visualize them.

```python
from skimage import color

gray = color.rgb2gray(image)
rgb = color.gray2rgb(gray)
overlay = color.label2rgb(labels, image=gray, bg_label=0, alpha=0.35)
```

`label2rgb` only paints existing labels; it does not create them.

## 3. Exposure and contrast

Use exposure functions to change how intensities are distributed.

- `rescale_intensity` stretches or clips an intensity window.
- `equalize_hist` spreads histogram mass across the full range.
- `equalize_adapthist` performs local contrast enhancement.
- `adjust_gamma`, `adjust_log`, and `adjust_sigmoid` apply tone curves.
- `match_histograms` transfers intensity statistics from a reference image.
- `is_low_contrast` checks whether enhancement is likely worthwhile.

```python
from skimage import exposure

p2, p98 = np.percentile(gray, (2, 98))
stretched = exposure.rescale_intensity(gray, in_range=(p2, p98))
clahe = exposure.equalize_adapthist(stretched, clip_limit=0.01)
```

For color images, prefer a luminance-style workflow or use `match_histograms(..., channel_axis=...)` when the source and reference should stay multichannel.

```python
matched = exposure.match_histograms(image, reference, channel_axis=-1)
```

## 4. Filters, edges, and thresholding

Use filters when you want to smooth, sharpen, or emphasize structure before a later step.

- `gaussian` for basic smoothing.
- `difference_of_gaussians` for band-pass style enhancement.
- `median` for impulse noise.
- `sobel`, `scharr`, `prewitt`, `farid`, and `laplace` for edge emphasis.
- `unsharp_mask` for sharpening.
- Threshold utilities such as `threshold_otsu`, `threshold_li`, `threshold_yen`, `threshold_local`, `threshold_sauvola`, `threshold_niblack`, `threshold_multiotsu`, `apply_hysteresis_threshold`, and `try_all_threshold` for preprocessing decisions.

```python
from skimage import filters

smooth = filters.gaussian(image, sigma=1.2, channel_axis=-1, preserve_range=True)
edges = filters.sobel(gray)
cutoff = filters.threshold_otsu(gray)
mask = gray > cutoff
```

Use thresholding only to produce a cutoff or binary mask. If you need region labels or measurements, hand off to another sub-skill.

## 5. Restoration and denoising

Use restoration when the image has noise, missing pixels, blur, or wrapped phase.

- `estimate_sigma` to gauge noise before choosing a denoiser.
- `denoise_tv_chambolle` and `denoise_tv_bregman` for piecewise-smooth images.
- `denoise_bilateral` for edge-preserving smoothing.
- `denoise_wavelet` and `denoise_nl_means` for more general denoising.
- `inpaint_biharmonic` for masked defects.
- `wiener`, `unsupervised_wiener`, and `richardson_lucy` for deconvolution.
- `rolling_ball` for background subtraction.
- `unwrap_phase` for wrapped phase maps.
- `cycle_spin`, `calibrate_denoiser`, and `denoise_invariant` for denoiser stability and calibration.

```python
from skimage import restoration

sigma = restoration.estimate_sigma(noisy, channel_axis=-1, average_sigmas=True)
denoised = restoration.denoise_wavelet(
    noisy,
    channel_axis=-1,
    convert2ycbcr=True,
    rescale_sigma=True,
)
restored = restoration.inpaint_biharmonic(image, mask, channel_axis=-1)
```

Notes:

- `convert2ycbcr=True` only makes sense for color input.
- `rescale_sigma=True` is useful when the noise estimate came from normalized float data.
- For deconvolution, make sure the PSF is compatible with the image dimensionality and normalized when that is part of the model.
- For `rolling_ball`, use a scalar image or process channels intentionally.

## 6. Safe chaining patterns

A common order is:

1. convert color only if needed,
2. adjust exposure,
3. smooth or restore,
4. convert or quantize the final output for storage.

Examples:

- Low-contrast grayscale image: `rescale_intensity` or `equalize_hist`.
- Color photo with a color cast: `match_histograms(..., channel_axis=-1)`.
- Noisy color photo: `estimate_sigma` then `denoise_wavelet(..., channel_axis=-1, rescale_sigma=True)`.
- Masked defect: `inpaint_biharmonic(..., channel_axis=-1)`.
- Blurred image: `unsupervised_wiener` or `richardson_lucy` with a compatible PSF.
