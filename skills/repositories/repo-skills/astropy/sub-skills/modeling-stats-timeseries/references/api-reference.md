# Modeling, Stats, and Time Series API Reference

## Modeling and Fitting

- `models.Gaussian1D(amplitude=1, mean=0, stddev=1, **kwargs)` is a common 1D model.
- `models.Linear1D`, polynomial models, blackbody/physical models, tabular models, and compound model operators support many astronomy tasks.
- `fitting.LevMarLSQFitter(calc_uncertainties=False)` is a common nonlinear least-squares fitter.
- `fitting.LinearLSQFitter` is useful for linear models.
- Model parameters can use `.fixed`, `.bounds`, `.tied`, and units-aware inputs where supported.

## Statistics

- `sigma_clip(data, sigma=3.0, sigma_lower=None, sigma_upper=None, maxiters=5, cenfunc='median', stdfunc='std', axis=None, masked=True, return_bounds=False, copy=True, grow=False)` masks outliers.
- `sigma_clipped_stats(data, ..., std_ddof=0, axis=None, grow=False)` returns mean, median, and std after clipping.
- `mad_std(data, axis=None, func=None, ignore_nan=False)` estimates robust standard deviation.
- Other families include biweight statistics, Bayesian blocks, histogram helpers, circular stats, spatial/Ripley functions, and information theory utilities.

## Time Series and Periodograms

- `TimeSeries(data=None, *, time=None, time_start=None, time_delta=None, n_samples=None, **kwargs)` stores time-indexed rows.
- `LombScargle(t, y, dy=None, fit_mean=True, center_data=True, nterms=1, normalization='standard')` computes Lomb-Scargle periodograms.
- `BoxLeastSquares(t, y, dy=None)` supports transit-like box least-squares searches.
- Keep `t`, frequency, and period units explicit; use `Quantity` frequencies when possible.

## Uncertainty Helpers

`astropy.uncertainty` provides distribution objects and helpers for propagating
sampled uncertainties through functions. Use it when analytic propagation or
NDData uncertainty classes are not enough.
