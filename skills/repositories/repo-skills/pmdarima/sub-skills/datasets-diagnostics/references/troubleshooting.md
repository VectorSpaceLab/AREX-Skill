# Dataset and diagnostics troubleshooting

## pmdarima cannot import

A source tree is not a working runtime until its compiled extensions are built.
An `ImportError` naming `pmdarima.__check_build`, `pmdarima.arima._arima`, or a
compiled utility module is an installation/build problem, not a dataset error.
Run the bundled checker with a verified installed environment from an arbitrary
working directory. Do not add the evidence checkout to `PYTHONPATH`, copy
shared objects into this skill, or bypass the package build check.

Capture:

```text
Python executable/version, pmdarima.__version__, pmdarima.__file__, platform,
NumPy/SciPy/statsmodels/scikit-learn versions, Matplotlib status, full traceback
```

`pmdarima.show_versions()` prints dependency information and returns `None`.
The evidence anchor is v2.1.1 at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`; the prepared inspection package
may report `0.0.0`, so record the runtime version/path instead of pretending it
is identical to the source tag.

## Loader output has an unexpected type, shape, index, or NaN

- Ordinary `load_<name>` functions return an ndarray by default and a Series
  with `as_series=True`. Inspect actual type, shape, length, dtype, labels, and
  missing count; do not rely on a generic loader description.
- Series labels are metadata, not guaranteed `DatetimeIndex`/`.freq` values.
  `load_airpassengers(as_series=True)` is positional; `load_lynx` has integer
  years; `load_sunspots`, `load_wineind`, and `load_woolyrnq` have string-like
  month/quarter labels.
- `load_ausbeer` contains a trailing `NaN` at this anchor. Choose and document
  dropping, imputation, truncation, or task-specific handling before numerical
  diagnostics. `check_endog` permits non-finite values by default, so pass
  `force_all_finite=True` when finite input is required.
- `load_msft()` returns seven columns, including an unparsed `Date`. Parse and
  order dates if required, then select one numeric target. A full multi-column
  DataFrame is rejected as univariate endogenous input.
- `load_gasoline()` can create `~/.pmdarima-data` and make an HTTP request when
  no cache exists. It is not an offline loader. Use a caller-supplied local
  series if network/cache mutation is not allowed.

## `m` is unknown, invalid, fractional, or too large

`m` is observations per repeated cycle, not `len(y)`. Justify it with the
observation calendar and forecasting hypothesis: for example, monthly annual
seasonality uses `m=12`, quarterly annual seasonality `m=4`, and daily weekly
seasonality `m=7`. Sampling frequency alone does not prove a repeating cycle.

`nsdiffs`, `CHTest`, and `OCSBTest` require `m > 1`; decomposition requires a
Python integer `m > 1` and at least two complete periods. The gasoline weekly
period `365.25 / 7` is fractional, and the Taylor loader's calendar notes are
internally inconsistent. Do not round or lower either period to make an API
pass. Resolve the calendar or route Fourier/date features to
[preprocessing](../../preprocessing/SKILL.md).

A short series may cause CH to return `0` without a calculation, OCSB to fail a
regression, or `nsdiffs` to warn after differencing makes `len(y) < m`. These
outcomes are not evidence that a smaller `m` is correct. Acquire more history,
use a separately justified test, or mark `D` unresolved.

## NaN or infinity reaches a diagnostic

Validate with `check_endog(y, force_all_finite=True)` before `ndiffs`,
`nsdiffs`, decomposition, PACF, and the usual ACF path. ACF's
`missing="none"` does not repair NaNs, while PACF here does not expose a missing
policy. Errors may originate in scikit-learn, statsmodels, NumPy linear algebra,
or compiled code and can vary by dependency version.

Do not silently replace values. Record whether the policy is drop, bounded
interpolation, model-based imputation, or rejection, and whether it is fit only
on training data. Route learned imputation/transformation to
[preprocessing](../../preprocessing/SKILL.md) so it can be contained inside each
training fold.

## `ndiffs` or `nsdiffs` fails or disagrees

- `max_d` and `max_D` must be positive. Results cannot exceed those bounds and
  are recommendations, not proof of a final differencing order.
- KPSS uses a stationarity null; ADF and PP use unit-root-oriented conventions.
  Record test, alpha, options, and p-value/boolean meaning. Send unresolved
  disagreement to [forecasting](../../forecasting/SKILL.md) and compare choices
  with [model-selection](../../model-selection/SKILL.md), rather than taking a
  maximum without explanation.
- Constant finite input intentionally returns `0` through a fast path.
- ADF/OCSB regression on too few or collinear observations can raise a
  `ValueError` or wrapped linear algebra error. Increase valid history or use a
  different supported, scientifically justified test and record the change.
- CH can be expensive on large series. Keep diagnostic samples and bounds
  explicit; do not start an unbounded search.

## `diff` is empty or `diff_inv` does not recover the original

Every `diff(x, lag, differences)` pass removes up to `lag` leading rows. A lag
at least as long as the current input yields an empty array; repeated passes can
erase a short window. `lag <= 0` or `differences <= 0` raises `ValueError`.
Always record input/output lengths before passing a result onward.

`diff_inv` follows a zero-initialized integration convention. Although it
validates `xi` length/shape, the v2.1.1 compiled vector integrator does not seed
its output with `xi` values. It therefore does not losslessly recover an
arbitrary nonzero original level. Preserve the original prefix and implement a
separately tested reconstruction when exact restoration is required; do not
label a zero-prefixed result as exact.

## ACF/PACF or `tsdisplay` rejects lag settings

Use a finite one-dimensional input and explicit conservative lags. PACF usually
requires `nlags < len(y) / 2`; use at most `(len(y) - 1) // 2` for a small
sample. `tsdisplay` explicitly raises when `lag_max >= len(y)`. Reduce the lag
only when the resulting diagnostic still answers the task; otherwise obtain
more observations.

ACF/PACF are numeric descriptions, not ARIMA order selectors. Record ACF
`fft`, `missing`, and `adjusted`, plus PACF `method`. If a current statsmodels
version rejects a legacy method alias, use a supported method such as
`"ywadjusted"` for numeric PACF and record the compatibility change.

## Decomposition fails or looks plausible for the wrong reasons

Check, in order:

1. `type_` is exactly `"additive"` or `"multiplicative"`.
2. `m` is a source-backed Python integer greater than one.
3. `len(y) >= 2*m` after applying the missing policy.
4. Multiplicative input has a compatible positive/nonzero scale.
5. Reconstruction is checked only where trend/random components are finite.

Moving-average endpoint NaNs are expected. A wrong calendar can still produce
smooth, plausible components, so visual plausibility never validates `m`.
Decomposition is descriptive and does not replace forecasting evaluation.

## A plot fails, opens a window, hangs, or leaks figures

Matplotlib is optional. Its absence should fail only an explicitly requested
plot path; numeric loaders, differencing, ACF, and PACF remain usable. In CI or
on a server:

1. set `MPLBACKEND=Agg` before importing pmdarima;
2. pass `show=False` to `plot_acf`, `plot_pacf`, `tsdisplay`, and
   `decomposed_plot`;
3. use `lag_max < len(y)` for `tsdisplay`;
4. call `matplotlib.pyplot.close("all")` and assert no figure numbers remain.

The pmdarima visualization module initializes its compatible pyplot handle at
package import time, so setting the backend afterward may be too late. Return
object types can vary with dependency versions; close all figures rather than
assuming one exact Axes/Figure class.

## The bundled checker fails

Run it by absolute path from a neutral directory:

```bash
cd /tmp
python /absolute/path/to/check_dataset_and_diagnostics.py --help
python /absolute/path/to/check_dataset_and_diagnostics.py
python /absolute/path/to/check_dataset_and_diagnostics.py --plot  # optional
```

The default route is local, deterministic, plot-free, and network-free. A
compiled-extension error means the installed environment is unusable. If only
`--plot` fails, report or repair the optional Matplotlib stack; do not weaken
the numeric assertions. If an assertion changes after a dependency upgrade,
record the imported package/dependency versions and compare the public contract
before adapting the assertion. Never import source files as a workaround.
