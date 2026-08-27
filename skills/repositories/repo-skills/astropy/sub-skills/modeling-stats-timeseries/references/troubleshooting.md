# Modeling, Stats, and Time Series Troubleshooting

## Fit Does Not Converge

- Check initial parameter guesses and bounds.
- Inspect units and convert inputs to compatible units before fitting.
- Remove or model NaNs/masks explicitly.
- Try a linear fitter for linear-in-parameter models; use nonlinear fitters only
  when needed.
- Inspect residuals and parameter covariance/uncertainty when available.

## Fitted Parameters Have Unexpected Units

Models may support units differently across parameters and fitters. Keep inputs
as `Quantity` when supported, or convert to documented raw units and reattach
units to results. Route unit conversion issues to `units-constants`.

## Sigma Clipping Masks Too Much or Too Little

Tune `sigma`, `sigma_lower`, `sigma_upper`, `cenfunc`, `stdfunc`, `axis`, and
`maxiters`. `grow` expands masks around outliers; do not enable it without a
spatial/time-series reason.

## Periodogram Peaks Are Misinterpreted

- Frequency and period are reciprocals; keep units explicit.
- Normalization choices affect power interpretation.
- False-alarm probabilities depend on assumptions and search grids.
- Irregular sampling and aliases can produce multiple plausible peaks.

## Optional SciPy Behavior Missing

Some fitters, FFT paths, and statistical routines need SciPy for full behavior
or performance. Install `astropy[recommended]` or `scipy` when the selected
workflow requires it.

## Time Series Loses Time Scale or Units

Use `TimeSeries` with `Time` objects and `Quantity` columns. When exporting to
plain dataframes, validate that time scale and units are preserved or stored in
metadata.
