# Dataset and diagnostics workflows

These procedures are offline-first, explicit about calendar assumptions, and
bounded for interactive or CI use. They create evidence for a later forecasting
or model-selection task; they do not fit, compare, persist, or update the final
ARIMA model.

## 1. Establish the target and calendar

1. Select a package-local loader whose source documentation matches the task.
   Use `load_airpassengers` for a compact monthly example (`m=12`),
   `load_austres`/`load_ausbeer`/`load_woolyrnq` for quarterly examples
   (`m=4`), `load_sunspots`/`load_wineind` for monthly examples (`m=12`),
   and `load_lynx` for annual/non-seasonal data. Treat `load_taylor` as a
   calendar ambiguity: its docstring describes half-hourly demand but its Notes
   call it annual/non-seasonal. Resolve the actual business calendar before
   choosing `m`.
2. Use `as_series=True` when labels are part of the evidence. Otherwise use
   the ndarray form. Record type, shape, length, dtype, index/date semantics,
   and `isna()` count. The observation count is not frequency metadata.
3. Normalize with a finite target check before statistics:

   ```python
   import numpy as np
   import pmdarima as pm

   raw = pm.datasets.load_airpassengers(as_series=True)
   y = pm.utils.check_endog(
       raw, dtype=np.float64, copy=True,
       force_all_finite=True, preserve_series=True,
   )
   record = {
       "loader": "load_airpassengers", "as_series": True,
       "type": type(y).__name__, "shape": tuple(y.shape),
       "dtype": str(y.dtype), "missing": int(y.isna().sum()),
       "m": 12, "m_evidence": "loader documents monthly observations",
   }
   ```
4. For `load_ausbeer`, explicitly handle its trailing `NaN`. For `load_msft`,
   parse and sort `Date` if needed, then choose one numeric column such as
   `Close`; the entire DataFrame is not a valid univariate endogenous target.
   Keep `load_gasoline` out of offline procedures because it may fetch and its
   weekly period is fractional. Route irregular/fractional calendar features
   to [preprocessing](../../preprocessing/SKILL.md).
5. If the calendar is unknown, stop with an unresolved assumption rather than
   inferring `m` from a chart or array length.

## 2. Produce bounded `d` and `D` recommendations

1. Call `ndiffs` for non-seasonal differencing and, only with a justified
   integer `m > 1`, call `nsdiffs` for seasonal differencing. Keep `max_d` and
   `max_D` small and record them:

   ```python
   from pmdarima.arima import ndiffs, nsdiffs
   from pmdarima.utils import diff

   d = ndiffs(y, alpha=0.05, test="kpss", max_d=2)
   D = nsdiffs(y, m=12, max_D=1, test="ocsb")
   y_d = diff(y, lag=1, differences=d)
   y_D = diff(y, lag=12, differences=D)
   evidence = {
       "d": int(d), "D": int(D),
       "len_d": int(len(y_d)), "len_D": int(len(y_D)),
   }
   ```
2. For a material choice, repeat `ndiffs` with `test="adf"` or `"pp"` and
   report disagreement. KPSS, ADF, and PP have different null hypotheses and
   boolean conventions; do not merge their outputs as if they were the same
   test.
3. A constant finite series takes the deterministic `0` path. Invalid
   `max_d`/`max_D`, non-finite targets, and stationarity regressions on too few
   rows should remain visible as errors. Seasonal differencing can warn when
   the result becomes shorter than `m`; do not lower the period silently.
4. `diff` removes up to `lag` rows on every pass. Record the output lengths and
   do not call downstream diagnostics on an empty or too-short result. If
   integration is needed, understand that `diff_inv` uses a zero-initialized
   compiled convention in this release; do not label it a lossless recovery of
   arbitrary nonzero levels.
5. Hand final order decisions to [forecasting](../../forecasting/SKILL.md) and
   out-of-sample comparisons to [model-selection](../../model-selection/SKILL.md).

## 3. Summarize serial dependence numerically

Use explicit lags and methods, after applying the missing policy:

```python
from pmdarima.utils import acf, pacf

acf_lags = min(24, len(y) - 2)
pacf_lags = min(acf_lags, (len(y) - 1) // 2)
a = acf(y, nlags=acf_lags, fft=False,
        missing="none", adjusted=False)
p = pacf(y, nlags=pacf_lags, method="ywadjusted")
summary = {
    "acf_len": int(len(a)), "acf_lag_0": float(a[0]),
    "pacf_len": int(len(p)), "pacf_lag_0": float(p[0]),
}
```

The wrappers are descriptive. They do not automatically choose ARIMA orders.
Keep lag bounds below the PACF limit for small data and record dependency
compatibility adjustments, such as replacing an old PACF method with
`"ywadjusted"`.

## 4. Decompose a known seasonal signal

Use at least two complete cycles and select additive versus multiplicative from
the data scale:

```python
import numpy as np
from pmdarima.arima import decompose

parts = decompose(np.asarray(y, dtype=float), type_="additive", m=12)
values = {
    name: np.asarray(getattr(parts, name), dtype=float)
    for name in ("x", "trend", "seasonal", "random")
}
for name, value in values.items():
    print(name, value.shape, int(np.isnan(value).sum()))
finite = np.isfinite(values["trend"])
assert np.allclose(
    values["x"][finite],
    (values["trend"] + values["seasonal"] + values["random"])[finite],
)
```

Moving-average endpoints are expected to be NaN. Multiplicative reconstruction
uses `trend * seasonal * random` and requires compatible positive/nonzero data.
A valid-looking decomposition with a wrong `m` is still a calendar error.
`decomposed_plot` is an optional presentation step, not a replacement for
numeric checks.

## 5. Optional headless visualization

Do not make a plot a prerequisite for a numeric handoff. When it is requested
in CI or on a server, establish the backend before importing pmdarima:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
from pmdarima.utils import decomposed_plot, plot_acf, plot_pacf, tsdisplay

plot_acf(y, lags=24, show=False)
plot_pacf(y, lags=12, method="yw", show=False)
tsdisplay(y, lag_max=24, title="diagnostic", show=False)
# v2.1.1 requires an explicit mapping for figure_kwargs.
decomposed_plot(parts, figure_kwargs={}, show=False)
plt.close("all")
assert not plt.get_fignums()
```

`tsdisplay` requires `lag_max < len(y)`. If Matplotlib is absent, retain the
numeric ACF/PACF record and report the optional dependency gap; fail only when
a requested plot path cannot run. Never use `show=True` in automation.

## 6. Reproducible handoff

Record:

- package version, executable, imported package path, and compiled-extension
  import status;
- loader/options, type/shape/length/dtype/index or date semantics, missing
  count, and the chosen policy;
- frequency evidence, integer `m`, and any unresolved calendar assumption;
- `ndiffs`/`nsdiffs` test names, alpha/bounds, results, warnings, and
  differenced lengths;
- decomposition type, `m`, component shapes, endpoint NaN counts, and the
  finite-interior reconstruction result;
- ACF/PACF methods, lags, missing policy, and key values;
- plotting requested/not requested, backend, optional dependency status, and
  figure cleanup result.

Then route the record to [forecasting](../../forecasting/SKILL.md),
[preprocessing](../../preprocessing/SKILL.md), or
[model-selection](../../model-selection/SKILL.md) as appropriate. Keep model
fitting, persistence, and update mechanics outside this route.

## Bundled smoke check

From any current working directory, run:

```bash
python /absolute/path/to/check_dataset_and_diagnostics.py --help
python /absolute/path/to/check_dataset_and_diagnostics.py
# only when Matplotlib is installed and a headless check is wanted:
python /absolute/path/to/check_dataset_and_diagnostics.py --plot
```

The default path uses one package-local AirPassengers loader and tiny
finite arrays. It performs no network access, plotting, model fit, credentials,
or unbounded search. It asserts loader type/shape, finite validation, constant
stationarity paths, differencing, m validation, decomposition, ACF/PACF, NaN
handling, and short-series errors.
