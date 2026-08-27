# Dataset and diagnostic API reference

Evidence: pmdarima v2.1.1 at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`, principally
`pmdarima/datasets/**`, `arima/stationarity.py`, `arima/seasonality.py`,
`arima/utils.py`, `utils/array.py`, `utils/wrapped.py`, and
`utils/visualization.py`, with their tests. Import the installed, built package
at runtime; never add the evidence checkout to `PYTHONPATH`.

## Built-in datasets

Most in-memory or bundled-data loaders use:

```python
load_<name>(as_series=False, dtype=np.float64)
```

They return a one-dimensional `numpy.ndarray` by default and a
`pandas.Series` for `as_series=True`. The Series labels are not necessarily a
`DatetimeIndex`, do not necessarily carry `.freq`, and are generally not
preserved by numerical helpers. Record the actual type, shape, dtype, labels,
and missing count.

| Loader | Shape at the anchor | Calendar evidence and cautions |
|---|---:|---|
| `load_airpassengers` | `(144,)` | Monthly, 1949–1960; `m=12` for annual seasonality. The Series has a positional `RangeIndex`. |
| `load_ausbeer` | `(212,)` | Quarterly, 1956 Q1–2008 Q3; `m=4`. The final value is `NaN`, so choose a missing-value policy first. |
| `load_austres` | `(89,)` | Quarterly; `m=4`. |
| `load_heartrate` | `(150,)` | Measurements every 0.5 seconds; no seasonal cycle is implied by spacing alone. |
| `load_lynx` | `(114,)` | Annual, 1821–1934; usually non-seasonal (`m=1`, so do not call `nsdiffs`). The Series index contains years. |
| `load_sunspots` | `(2820,)` | Monthly; `m=12`. The Series uses string labels such as `Jan 1749`. |
| `load_taylor` | `(4032,)` | Docstring title says half-hourly electricity demand, but its Notes incorrectly call it annual/non-seasonal. Resolve the real calendar and relevant daily/weekly cycles before choosing `m`. |
| `load_wineind` | `(176,)` | Monthly; `m=12`. The Series uses labels such as `Jan 1980`. |
| `load_woolyrnq` | `(119,)` | Quarterly; `m=4`. The Series uses labels such as `Q1 1965`. |

`load_msft()` takes no `as_series` option and returns a bundled `(7983, 7)`
DataFrame with `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, and `OpenInt`.
The source loader does not parse or sort `Date`. Select exactly one numeric
column for univariate diagnostics and preserve date-order evidence separately.

`load_gasoline(as_series=False, dtype=...)` is the exception to offline local
loading. It looks in the module cache and `~/.pmdarima-data`, otherwise sends an
HTTP request to the URL declared in `datasets/gasoline.py`. Do not use it in an
offline smoke. Its documented weekly period is `365.25 / 7`, which is not an
integer accepted as `m`; represent such calendar effects through the
[preprocessing route](../../preprocessing/SKILL.md) rather than silently
rounding.

Internal helpers `get_data_path()` and `get_data_cache_path()` expose package
data and user-cache paths. `_base.load_date_example()` and private underscored
loaders are test/support APIs, not the default public dataset route.

## Target, exogenous, and array utilities

```python
from pmdarima.utils import as_series, c, check_endog, check_exog, diff, diff_inv

check_endog(y, dtype=np.float64, copy=True,
            force_all_finite=False, preserve_series=True)
check_exog(X, dtype=np.float64, copy=True, force_all_finite=True)
as_series(x, **kwargs)
c(*args)
diff(x, lag=1, differences=1)
diff_inv(x, lag=1, differences=1, xi=None)
```

- `check_endog` accepts one-dimensional input or a squeezable one-column
  DataFrame. A multi-column DataFrame fails. With `preserve_series=True`, it
  restores a Series index after checking. Its default deliberately permits
  NaN and infinity, so set `force_all_finite=True` before finite-only
  diagnostics.
- `check_exog` is for two-dimensional feature input. A DataFrame remains a
  DataFrame; list/ndarray input becomes a numeric ndarray. It rejects
  non-finite values by default.
- `as_series` uses a positional index for non-Series input and returns an
  existing Series unchanged. `c()` is an R-like one-level concatenator:
  `c()` returns `None`, while `c(1, [2, 3])` returns a flat ndarray.
  Multi-level nested inputs can fail.
- `diff` accepts a vector or matrix. `lag` is the observation offset and
  `differences` is the number of repeated passes; both must be positive. Each
  pass removes up to `lag` leading rows. A lag at least as long as the current
  input yields an empty first dimension. The result is a numeric ndarray; it
  does not preserve a pandas index.
- `diff_inv` restores the *zero-initialized* integration convention used by
  this implementation. In v2.1.1 the public `xi` argument is shape-validated
  but the compiled `C_intgrt_vec` does not use its values when integrating a
  vector. Therefore, do not claim that `diff_inv(diff(original), xi=...)`
  exactly reconstructs a nonzero original level. For vectors, `xi` must have
  length `lag * differences`; for matrices it must have shape
  `(lag * differences, n_features)`. Wrong shape raises `IndexError`.

## Non-seasonal and seasonal differencing tests

```python
from pmdarima.arima import ndiffs, nsdiffs

ndiffs(x, alpha=0.05, test="kpss", max_d=2, **kwargs) -> int
nsdiffs(x, m, max_D=2, test="ocsb", **kwargs) -> int
```

`ndiffs` supports `test="kpss"`, `"adf"`, or `"pp"`; `max_d` must be
positive. `nsdiffs` supports `test="ocsb"` or `"ch"`; `m > 1` and
`max_D > 0` are required. Both validate a one-dimensional numeric target and
return an integer no larger than the configured bound. A constant finite series
returns `0` without a full test.

`nsdiffs` runs the selected test, applies `diff(x, lag=m)` if needed, and
repeats until the bound. If a seasonal difference leaves fewer than `m`
observations, it warns and returns the reached `D`; short or singular OCSB
regressions can instead raise. `CHTest` returns `0` without calculation when
`len(x) < 2*m + 5`, while OCSB has different regression/data requirements.
Never lower `m` merely to force a result.

For p-value auditing:

```python
from pmdarima.arima import ADFTest, KPSSTest, PPTest

ADFTest(alpha=0.05, k=None).should_diff(x) -> (pvalue, bool)
KPSSTest(alpha=0.05, null="level", lshort=True).should_diff(x)
PPTest(alpha=0.05, lshort=True).should_diff(x)
```

For a one-step seasonal test:

```python
from pmdarima.arima import CHTest, OCSBTest

CHTest(m).estimate_seasonal_differencing_term(x) -> 0 | 1
OCSBTest(m, lag_method="aic", max_lag=3).estimate_seasonal_differencing_term(x)
```

KPSS tests a stationarity null while ADF/PP use unit-root conventions. Report
the test, alpha, options, p-value/boolean semantics, and disagreement. Prefer
`ndiffs`/`nsdiffs` for ordinary recommendations. They do not select `p`, `q`,
`P`, or `Q`; route fitting to [forecasting](../../forecasting/SKILL.md) and
comparison to [model-selection](../../model-selection/SKILL.md).

## Classical decomposition

```python
from pmdarima.arima import decompose
parts = decompose(x, type_, m, filter_=None)
```

`type_` must be exactly `"additive"` or `"multiplicative"`; `m` must be a
Python integer greater than one; and `len(x) / m >= 2`. The optional filter is
passed to a valid-mode convolution; the default is an `m`-point moving average.
The returned named tuple contains `x`, `trend`, `seasonal`, and `random`, all
aligned to input length. Moving-average padding introduces endpoint NaNs in the
trend and random terms. On the finite interior, additive reconstruction is
`trend + seasonal + random`; multiplicative reconstruction is
`trend * seasonal * random`.

Use additive form for roughly level-independent seasonal magnitude.
Multiplicative decomposition divides by estimated components and therefore
requires a compatible positive/nonzero scale. A mathematically accepted `m`
can still be calendrically wrong; validate the calendar independently.

## Numeric ACF and PACF

```python
from pmdarima.utils import acf, pacf

acf(x, nlags=None, qstat=False, fft=None, alpha=None,
    missing="none", adjusted=False)
pacf(x, nlags=None, method="ywadjusted", alpha=None)
```

These are thin statsmodels wrappers. They return an ndarray in the simplest
case and tuples when confidence intervals or Q-statistics are requested. Lag
zero is included, so `nlags=6` normally returns seven values. Set `nlags`,
`fft`, `missing`, `adjusted`, and PACF `method` explicitly where reproducibility
matters. PACF generally requires `nlags < len(x) / 2`; a conservative bound is
`min(requested, (len(x) - 1) // 2)`. The default ACF missing mode does not
repair NaNs, and PACF has no `missing` argument here; apply the task's missing
policy first.

## Optional plotting diagnostics

```python
from pmdarima.utils import (
    autocorr_plot, decomposed_plot, plot_acf, plot_pacf, tsdisplay,
)

plot_acf(series, ax=None, lags=None, alpha=None, use_vlines=True,
         unbiased=False, fft=True, title="Autocorrelation", zero=True,
         vlines_kwargs=None, show=True, **kwargs)
plot_pacf(series, ax=None, lags=None, alpha=None, method="yw",
          use_vlines=True, title="Partial Autocorrelation", zero=True,
          vlines_kwargs=None, show=True, **kwargs)
tsdisplay(y, lag_max=50, figsize=(8, 6), title=None, bins=25,
          series_kwargs=None, acf_kwargs=None, hist_kwargs=None, show=True)
```

`decomposed_plot(parts, figure_kwargs=None, show=True)` displays four
components, and `autocorr_plot(series, show=True)` delegates to pandas.
Matplotlib is optional; these APIs raise `ImportError` if it is unavailable.
With `show=False`, they return created Axes/Figure objects instead of showing
them. In this v2.1.1 implementation, pass `figure_kwargs={}` explicitly to
`decomposed_plot` because its default `None` is forwarded with `**` and can
raise `TypeError`; treat that as a compatibility/source bug, not a data error.
`tsdisplay` constructs series, ACF, and histogram panels and raises when
`lag_max >= len(y)`.

For a server or CI process, select `MPLBACKEND=Agg` before importing pmdarima,
pass `show=False`, and finish with `matplotlib.pyplot.close("all")`. Do not
assume every plotting wrapper returns the same object type across dependency
versions.
