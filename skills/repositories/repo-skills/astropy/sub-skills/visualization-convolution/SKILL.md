---
name: visualization-convolution
description: "Use Astropy visualization and convolution for image normalization,
  stretches, WCSAxes, RGB rendering, FITS bitmap export, kernels, direct
  convolution, and FFT convolution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Visualization and Convolution Router

Use this sub-skill when a task centers on displaying astronomy images or
convolving array data with Astropy kernels.

## Load This When

- The user needs image scaling, `ImageNormalize`, intervals, stretches,
  `ZScaleInterval`, `PercentileInterval`, `AsinhStretch`, `LogStretch`, or
  Matplotlib normalization.
- The task mentions WCSAxes plotting, world-coordinate axes, overplotting
  coordinates, or publication-style FITS image display.
- The task needs RGB composites, `make_lupton_rgb`, or `fits2bitmap`.
- The task uses convolution kernels, `Gaussian2DKernel`, `convolve`,
  `convolve_fft`, NaN interpolation, boundary modes, or kernel normalization.

## Route Away When

- Constructing or validating the WCS object is the main challenge; use
  `../wcs-nddata/SKILL.md`.
- FITS/table reading and writing is the main task; use `../tables-io/SKILL.md`.
- Statistical clipping or model fitting is central; use
  `../modeling-stats-timeseries/SKILL.md`.
- Optional dependency installation or CLI availability is the main issue; use
  `../cli-config-data/SKILL.md`.

## First Actions

1. Identify the input: NumPy array, FITS image, WCS object, RGB channels,
   masked/NaN data, or kernel.
2. For display, separate data extraction, normalization, plotting, and file
   output.
3. Choose interval and stretch based on data distribution; avoid hard-coded
   min/max until inspecting the image.
4. For WCS plotting, create/validate WCS first, then pass it as Matplotlib
   projection.
5. For convolution, choose direct `convolve` for small kernels or
   `convolve_fft` for larger FFT-friendly kernels.
6. Decide boundary, fill value, NaN treatment, and kernel normalization.
7. Validate output shape, finite values, and whether NaNs should remain masked
   or interpolated.

## References

- [references/api-reference.md](references/api-reference.md) lists verified
  visualization and convolution API signatures.
- [references/workflows.md](references/workflows.md) covers normalization,
  WCSAxes plotting, RGB, CLI bitmap export, and convolution recipes.
- [references/troubleshooting.md](references/troubleshooting.md) covers NaNs,
  zero-sum kernels, optional Matplotlib/SciPy issues, WCSAxes pitfalls, and
  unsafe file overwrites.

## Safety and Validation

- Use temporary output paths for generated PNG/JPEG/FITS experiments.
- Do not overwrite user image outputs without explicit permission.
- Preserve units and WCS decisions from sibling routes; this sub-skill owns
  display/convolution choices, not file semantics.
- For convolution, assert shape and inspect edge behavior before using output in
  downstream science.

## Native-Backed Validation Ideas

- Normalize a small image with `ImageNormalize(..., interval=ZScaleInterval())`
  and assert finite output.
- Convolve a tiny array with `Gaussian2DKernel` and assert output shape.
- Run `fits2bitmap --help` or use a temporary FITS fixture for a bounded CLI
  smoke.
