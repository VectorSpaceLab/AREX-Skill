# Troubleshooting: KTR / KTRLite

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: cmdstanpy` or `ModuleNotFoundError: pyro` | Required backend is missing. | `KTRLite` needs Stan/CmdStan; `KTR` needs both Stan/CmdStan and Pyro. Install the missing backend set before retrying. |
| `Invalid estimator. Must be one of ['pyro-svi']` | `KTR` was given the wrong estimator. | Use `estimator="pyro-svi"` for `KTR` and `estimator="stan-map"` for `KTRLite`. |
| `length of seasonality and fs_order not matching` | `seasonality` and `seasonality_fs_order` were not the same length. | Make the lists the same length. |
| `reduce seasonality_fs_order to avoid over-fitting` | Fourier order is too large for the period. | Keep `2 * order < period` for each seasonality entry. |
| `Number of observations ... is less than max seasonality ...` | The series is shorter than the largest seasonal period. | Use a longer training series or smaller seasonality periods. |
| `Datetime index must be ordered and not repeat` | Dates are unsorted or duplicated. | Sort the frame, deduplicate dates, and keep the time index monotonic. |
| `pd.infer_freq` returns nothing useful or knot dates drift unexpectedly | The series is irregular, too short, or frequency is ambiguous. | Pass `date_freq` explicitly and keep the date grid regular. |
| Explicit knot dates are silently missing | Knot dates fell outside the training span and were filtered out. | Keep knot dates inside the observed training range or switch to `*_segments` / `*_knot_distance`. |
| `predict(..., decompose=True)` on KTRLite has no regression column | KTRLite does not model exogenous regressors. | Use KTR if you need a regression component. |
| `fit_wbic` is unavailable on KTRLite | WBIC is a KTR / SVI concept, not a KTRLite / MAP concept. | Use `get_bic()` for KTRLite and `fit_wbic()` / `get_wbic()` for KTR. |
| Direct `orbit.template.ktr` import fails or behaves oddly | Circular import between `orbit.template.ktr` and `orbit.models`. | Import via `orbit.models` only. |

Additional reminders:

- `date_freq=None` asks the model to infer the frequency with `pandas.infer_freq`.
- For smoke tests, prefer daily data with at least a few dozen rows and keep the seasonal periods below the
  training length.
- If you only need knots and level curves, KTRLite is usually the simpler starting point.
