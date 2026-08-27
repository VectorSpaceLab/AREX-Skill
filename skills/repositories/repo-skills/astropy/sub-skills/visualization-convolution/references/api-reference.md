# Visualization and Convolution API Reference

## Normalization and Stretches

- `ImageNormalize(data=None, interval=None, vmin=None, vmax=None, stretch=LinearStretch(), clip=False, invalid=-1.0)` creates Matplotlib-compatible normalization.
- `ZScaleInterval(n_samples=1000, contrast=0.25, max_reject=0.5, min_npixels=5, krej=2.5, max_iterations=5)` estimates display limits using a common astronomy image heuristic.
- `PercentileInterval(percentile, n_samples=None)` chooses symmetric percentile limits.
- Stretches include `LinearStretch`, `SqrtStretch`, `LogStretch`, `AsinhStretch(a=0.1)`, and histogram equalization variants.

## RGB and Plotting

- `make_lupton_rgb(image_r, image_g, image_b, interval=None, stretch_object=None, minimum=None, stretch=5, Q=8, filename=None, output_dtype=numpy.uint8)` creates Lupton-style RGB composites.
- WCSAxes plotting is used through Matplotlib projection: `plt.subplot(projection=wcs)` or `fig.add_subplot(..., projection=wcs)`.
- Use WCSAxes after WCS construction has been validated by the WCS route.

## Convolution

- `convolve(array, kernel, boundary='fill', fill_value=0.0, nan_treatment='interpolate', normalize_kernel=True, mask=None, preserve_nan=False, normalization_zero_tol=1e-08)` performs direct convolution.
- `convolve_fft(array, kernel, boundary='fill', fill_value=0.0, nan_treatment='interpolate', normalize_kernel=True, normalization_zero_tol=1e-08, preserve_nan=False, mask=None, crop=True, return_fft=False, fft_pad=None, psf_pad=None, min_wt=0.0, allow_huge=False, ...)` performs FFT convolution.
- Kernels include Gaussian, Box, Tophat, MexicanHat, AiryDisk, Moffat, RickerWavelet, Ring, Trapezoid, and custom kernels.
- `Gaussian2DKernel(x_stddev, y_stddev=None, theta=0.0, **kwargs)` is a common smoothing kernel.

## CLI

`fits2bitmap` converts FITS images to bitmap outputs. Run `fits2bitmap --help`
first; use temporary output paths for smoke checks.
