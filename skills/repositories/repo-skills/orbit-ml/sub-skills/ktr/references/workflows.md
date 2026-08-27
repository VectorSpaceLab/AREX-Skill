# KTR / KTRLite Workflows

## 1. Decide between KTRLite and KTR

Use **KTRLite** when you need:

- a fast level + seasonality fit
- level knot inspection
- MAP-only selection with `get_bic()`
- no exogenous time-varying regressors

Use **KTR** when you need:

- time-varying regression coefficients
- regressor sign constraints (`=`, `+`, `-`)
- coefficient priors on a time window
- regression knot controls
- coefficient-path inspection or WBIC

## 2. KTRLite recipe

```python
from orbit.models import KTRLite

model = KTRLite(
    response_col="y",
    date_col="ds",
    level_segments=4,
    seasonality=[7, 14],
    seasonality_fs_order=[2, 3],
    seasonality_segments=1,
    date_freq="D",
    estimator="stan-map",
)
model.fit(train_df)
pred = model.predict(test_df, decompose=True)
level_knots = model.get_level_knots()
levels = model.get_levels()
bic = model.get_bic()
```

Notes:

- Use `decompose=True` when you want trend and seasonality columns in the output.
- Add `n_bootstrap_draws > 0` if you want pseudo-intervals from the point estimate.
- Prefer explicit `date_freq` when working with short or irregular series.

## 3. KTR recipe

```python
from orbit.models import KTR

model = KTR(
    response_col="y",
    date_col="ds",
    regressor_col=["promo"],
    regressor_sign=["="],
    regressor_init_knot_loc=[0.0],
    regressor_init_knot_scale=[1.0],
    regressor_knot_scale=[0.1],
    regression_segments=1,
    seasonality=[7, 14],
    seasonality_fs_order=[2, 3],
    level_segments=3,
    seasonality_segments=1,
    date_freq="D",
    estimator="pyro-svi",
)
model.fit(train_df)
pred = model.predict(test_df, decompose=True)
coef_mid, coef_lo, coef_hi = model.get_regression_coefs(include_ci=True)
coef_knots = model.get_regression_coef_knots()
level_knots = model.get_level_knots()
```

Notes:

- `predict(..., decompose=True)` is the quickest way to inspect trend, regression, and seasonality together.
- `get_regression_coefs(include_ci=True)` is the main inspection hook for dynamic coefficient paths.
- `get_regression_coef_knots()` is the direct knot table for plotting or QA.
- `fit_wbic(train_df)` reruns KTR at `sampling_temperature=log(n)` and returns the WBIC value.

## 4. Regression priors and signs

- `regressor_sign`: `"="` means unconstrained, `"+"` means strictly positive, `"-"` means strictly negative.
  Mixed sign lists are allowed.
- `coef_prior_list` entries must include `name`, `prior_start_tp_idx`, `prior_end_tp_idx`, `prior_mean`,
  `prior_sd`, and `prior_regressor_col`.
- `prior_end_tp_idx` is exclusive.
- The prior arrays are expanded over the requested time window during fit.
- Leave `flat_multiplier=True` unless you specifically want knot scales to vary with local regressor volume.

Example prior payload:

```python
coef_prior_list = [
    {
        "name": "promo_window",
        "prior_start_tp_idx": 10,
        "prior_end_tp_idx": 20,
        "prior_mean": [0.2],
        "prior_sd": [0.05],
        "prior_regressor_col": ["promo"],
    }
]
```

## 5. Knot placement

Choose one of the following per component:

- `*_segments` for evenly spaced knots
- `*_knot_distance` for fixed-distance knots
- `*_knot_dates` for explicit date control

Where `*` is `level`, `regression`, or the seasonality coefficient knot controls.

Use `orbit.utils.knots.get_knot_idx(...)` when you need to turn dates or segment counts into knot indices, and
`orbit.utils.knots.get_knot_dates(...)` when you need to map the indices back to dates.

## 6. Smoke check

Run `python scripts/smoke_ktr_ktrlite.py --model ktrlite` first; use `--model ktr` only after Pyro and CmdStan
are available. The script uses a short daily series with periods 7 and 14 so the Fourier order bound stays valid.
