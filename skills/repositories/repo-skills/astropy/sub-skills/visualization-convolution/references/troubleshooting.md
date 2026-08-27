# Visualization and Convolution Troubleshooting

## Display Is Too Dark or Saturated

Try a robust interval (`ZScaleInterval`, `PercentileInterval`) and a nonlinear
stretch (`AsinhStretch`, `SqrtStretch`, or `LogStretch`). Inspect the data
range and NaNs before setting fixed `vmin`/`vmax`.

## Matplotlib or Export Import Fails

Visualization workflows need Matplotlib, and bitmap export may need image-output
backends such as Pillow. Install `astropy[recommended]` or the specific missing
package.

## WCSAxes Labels Are Wrong

Validate the WCS separately. Check `origin="lower"` in `imshow`, axis order, and
whether the plotted array has been transposed or sliced without updating WCS.

## Convolution Produces NaNs or Warnings

- Check `nan_treatment`: `interpolate` fills via kernel weights, while `fill`
  uses `fill_value`.
- Set `preserve_nan=True` if original NaN positions should remain NaN.
- Ensure the kernel is normalizable when `normalize_kernel=True`.

## Zero-Sum Kernel Error

Derivative or edge-detection kernels may sum to zero. Use
`normalize_kernel=False` when scientifically appropriate and document the choice.

## FFT Convolution Memory Risk

`convolve_fft` can allocate large padded arrays. Keep `allow_huge=False` unless
the user explicitly approves memory-heavy behavior. Downsample, crop, or use
direct convolution for bounded checks.

## Output File Overwrite Risk

Do not write PNG/JPEG/FITS outputs over user files unless requested. Use a
temporary directory for trial normalization, RGB, and `fits2bitmap` checks.
