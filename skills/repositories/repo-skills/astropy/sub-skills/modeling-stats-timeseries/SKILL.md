---
name: modeling-stats-timeseries
description: "Use Astropy modeling, fitting, robust statistics, histograms, time
  series, periodograms, and uncertainty helpers for astronomy analysis."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Modeling, Stats, and Time Series Router

Use this sub-skill when a task centers on Astropy models, fitters, robust
statistics, periodograms, or time-series containers.

## Load This When

- The task mentions `astropy.modeling`, predefined models, `Gaussian1D`,
  polynomials, compound models, parameter constraints, bounds, tied parameters,
  or fitters.
- The task needs `sigma_clip`, `sigma_clipped_stats`, `mad_std`, biweight
  statistics, histograms, Bayesian blocks, or circular statistics.
- The task uses `TimeSeries`, `BinnedTimeSeries`, `LombScargle`,
  `BoxLeastSquares`, periodograms, false-alarm probabilities, or time-binned
  light curves.
- The task needs uncertainty distributions from `astropy.uncertainty`.

## Route Away When

- Creating times or coordinates is the main issue; use
  `../time-coordinates/SKILL.md`.
- Units and equivalencies are the main obstacle; use
  `../units-constants/SKILL.md`.
- Plotting fit results or images is central; use
  `../visualization-convolution/SKILL.md`.
- Table file formats dominate; use `../tables-io/SKILL.md`.

## First Actions

1. Identify input arrays/tables, units, masks, uncertainties, and time scale.
2. For fitting, choose a model class and fitter compatible with constraints and
   linear/nonlinear behavior.
3. Initialize parameters near plausible values; set bounds/fixed/tied flags
   before fitting.
4. For outliers, use sigma clipping or robust stats before or during fitting.
5. For periodograms, make time and frequency units explicit and choose the
   normalization/statistical interpretation.
6. Validate with residuals, parameter units, output shapes, finite values, and
   a small synthetic check.

## References

- [references/api-reference.md](references/api-reference.md) lists model,
  fitter, stats, and periodogram APIs.
- [references/workflows.md](references/workflows.md) gives fitting, robust
  statistics, histogram, time-series, and periodogram recipes.
- [references/troubleshooting.md](references/troubleshooting.md) covers bad
  initial guesses, unit mismatches, optional SciPy behavior, periodogram
  pitfalls, and masked/NaN data.

## Safety and Validation

- Do not treat a fitted parameter as valid without checking residuals and
  parameter units.
- Do not silently drop masks/NaNs; choose clipping or filtering explicitly.
- Use bounded/synthetic data for smoke tests; avoid long searches or benchmark
  grids unless requested.
- For time series, preserve time scale and units through period/frequency
  calculations.

## Native-Backed Validation Ideas

- Fit `Linear1D` or `Gaussian1D` to small synthetic data and assert parameters.
- Apply `sigma_clip` to `[1, 1, 100]` and assert the outlier is masked.
- Run a tiny `LombScargle` power calculation and assert finite output.
