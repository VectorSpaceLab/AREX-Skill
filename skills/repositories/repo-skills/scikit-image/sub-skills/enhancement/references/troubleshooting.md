# Enhancement Troubleshooting

Use this page when an enhancement call changes the wrong axis, the wrong scale, or the wrong family of pixels.

## Symptom table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| RGB colors get mixed or a color image is treated like grayscale | `channel_axis` is missing or points at the wrong dimension | Pass the actual channel axis explicitly. Use `None` only for scalar or grayscale data. |
| Output is unexpectedly 0-1, too dark, or too bright | The function normalized the data or you forgot to preserve the native range | Use `preserve_range=True` when available, or convert and rescale intentionally before the step. |
| Exposure or histogram matching looks wrong | `in_range`, `out_range`, or channel layout does not match the image semantics | Inspect `dtype`, `min`, and `max`; use percentile bounds or `match_histograms(..., channel_axis=...)` with matching layouts. |
| Thresholding on a color image gives odd results | Thresholding utilities are scalar-image tools | Convert to grayscale first or pick one channel before thresholding. |
| `threshold_local` or `threshold_multiotsu` raises a shape or value error | The block size or number of classes does not fit the image | Make the block size odd and dimension-matched, and reduce the number of classes if there are too few distinct values. |
| Denoising is too strong or too weak | The chosen denoiser or its parameters do not match the noise model | Tune `sigma`, `weight`, `sigma_color`, `sigma_spatial`, `h`, or `wavelet_levels`; choose TV, bilateral, wavelet, or NL means according to the image structure. |
| `denoise_wavelet` or `estimate_sigma` complains about channels or YCbCr | `convert2ycbcr=True` was used without valid multichannel input, or `channel_axis` is missing | Use `convert2ycbcr=True` only for color images and set `channel_axis` explicitly. |
| A wavelet denoiser fails to import or run | PyWavelets is missing | Install `pywt` / PyWavelets, or switch to a non-wavelet restoration function. |
| `inpaint_biharmonic`, deconvolution, or background subtraction raises shape errors | The mask or PSF is not compatible with the image shape | Make the mask match the spatial dimensions and ensure the PSF has the expected dimensionality. |
| `cycle_spin(..., num_workers=...)` warns | `num_workers` is deprecated in the current API | Use `workers` instead. |
| `rolling_ball` removes fine structure or seems ineffective | The radius does not match the background scale, or the input still has color channels | Tune the radius and decide whether to process a grayscale image or each channel separately. |
| `unwrap_phase` gives nonsense values | The input is not actually wrapped phase data | Use `unwrap_phase` only for phase-like data from interferometry or a similar source. |

## Quick checks

1. Print `shape`, `dtype`, `min`, and `max` before the enhancement step.
2. Confirm the correct `channel_axis` for every multichannel array.
3. Decide whether the next step expects normalized float data or native units.
4. If the output should remain physically meaningful, keep `preserve_range=True` whenever the function exposes it.
5. If a result looks overprocessed, try the weakest version of the same family before switching families.

## Family-specific hints

- `gaussian` and `difference_of_gaussians`: use `preserve_range=True` for native-valued inputs, and remember that smoothing should not mix channels.
- `match_histograms`: source and reference must agree on channel layout and channel count.
- `denoise_wavelet`: `rescale_sigma=True` is usually safer when the input has already been normalized.
- `denoise_bilateral`: increase `sigma_spatial` for broader smoothing and `sigma_color` for looser color similarity.
- `denoise_tv_*`: increase `weight` for stronger smoothing.
- `unsharp_mask`: use it for sharpening, not for denoising.
- `threshold_local`: use an odd block size and a value that matches the image dimensionality.
