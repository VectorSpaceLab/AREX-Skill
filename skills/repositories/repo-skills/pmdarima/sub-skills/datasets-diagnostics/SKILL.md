---
name: datasets-diagnostics
description: "Inspect pmdarima's built-in time-series datasets, validate target
  and seasonal inputs, estimate differencing, and run numeric or headless
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Datasets and diagnostics

Use this route before fitting or selecting a forecasting model when the target
series, observation calendar, missing-value policy, differencing need, or
serial-dependence evidence is not explicit. Read the three linked references
before making a material decision:

- [API reference](references/api-reference.md) — loaders, validators, array
  helpers, stationarity, seasonality, ACF/PACF, and plotting contracts.
- [Workflows](references/workflows.md) — bounded offline procedures and the
  handoff record.
- [Troubleshooting](references/troubleshooting.md) — build/import, data,
  frequency, short-series, statistical, and headless-plot failures.

Run the bundled [deterministic checker](scripts/check_dataset_and_diagnostics.py)
for a small local smoke test. It does not fetch data, fit an ARIMA model, or
create plots unless `--plot` is explicitly requested.

## Operating route

1. **Identify the source and calendar.** Choose a local loader whose documented
   time basis matches the task. Record the loader, `as_series` option, Python
   type, shape, length, dtype, index/date semantics, and missing count. A
   one-dimensional array does not carry frequency metadata; choose `m` from
   domain/calendar evidence, never from the sample count or a plot. For
   `load_msft()`, inspect the seven-column DataFrame, parse/sort `Date` only
   when needed, and select one numeric target. Do not pass the full DataFrame
   to univariate helpers. Avoid `load_gasoline()` in offline work: it can use
   a network URL/cache and its documented weekly period is fractional.
2. **Validate the target.** Normalize a univariate target with
   `check_endog`. Use `force_all_finite=True` before stationarity or seasonal
   tests, ACF/PACF, and decomposition unless the task has an explicit missing
   data policy. Use `check_exog` only for a two-dimensional exogenous matrix;
   route feature construction to [preprocessing](../preprocessing/SKILL.md).
3. **Estimate differencing, then report limits.** With a justified integer
   `m > 1`, call bounded `ndiffs` for non-seasonal `d` and `nsdiffs` for
   seasonal `D`. Record test names, alpha, bounds, warnings, and output
   lengths from any explicit `diff` calls. Compare tests only with their
   hypotheses and settings recorded. These are bounded recommendations, not
   final ARIMA order selection or proof that a model will forecast well.
4. **Decompose only compatible data.** Use `decompose` with exactly
   `type_="additive"` or `type_="multiplicative"`, an integer `m > 1`, at
   least two complete cycles, and a scale compatible with the chosen type.
   Inspect endpoint NaNs in `trend` and `random`; check reconstruction only on
   the finite interior. Do not feed padded components to another diagnostic
   without a missing-value policy.
5. **Prefer numeric dependence summaries.** Use `acf` and `pacf` with
   explicit conservative lags and methods. PACF has stricter lag limits than
   ACF. Treat these as descriptive evidence, not automatic `p`/`q` order
   selection.
6. **Make plots optional and headless.** If qualitative inspection is needed,
   set a non-interactive Matplotlib backend before importing pmdarima, pass
   `show=False`, and close all figures. `tsdisplay` requires
   `lag_max < len(y)`. A missing Matplotlib installation blocks only the
   requested visualization path, not numeric diagnostics.
7. **Handoff, do not overreach.** Send the normalized target, calendar,
   missing policy, `d`/`D` recommendations, transformed lengths, and
   diagnostic evidence to [forecasting](../forecasting/SKILL.md). Send target
   transforms, Fourier, or date features to [preprocessing](../preprocessing/SKILL.md).
   Send leakage-safe holdouts and temporal cross-validation to
   [model-selection](../model-selection/SKILL.md). Persistence and update
   belong to the sibling persistence route. This sub-skill does not fit the
   primary ARIMA model, choose final orders, compare folds, or persist models.

## Minimum handoff record

```text
loader/as_series, type/shape/length/dtype, index or date evidence,
missing count and policy, calendar evidence and m, ndiffs/nsdiffs tests and
bounds, d/D and differenced lengths, decomposition type and endpoint NaNs,
ACF/PACF methods/lags/key values, plotting/backend status, warnings/errors,
package/runtime version and import/build status, unresolved assumptions
```

The evidence anchor is pmdarima v2.1.1 commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. Runtime files resolve imports from
the installed, successfully built pmdarima distribution and do not require a
source checkout.
