# Evidence Map for KTR / KTRLite

This sub-skill was distilled from the following Orbit sources.
The paths below are evidence anchors only; future runtime should use the bundled references and script in this
sub-skill tree instead of reaching back into the source checkout.

## Included anchors

| Source anchor | What it contributed |
| --- | --- |
| `docs/tutorials/ktr1.ipynb` | KTR framing, multi-seasonality, decomposition, trend + seasonality visualization, and the Fourier order bound reminder. |
| `docs/tutorials/ktr2.ipynb` | Time-varying regression coefficients, `get_regression_coefs`, `plot_regression_coefs`, and regression-prior usage. |
| `docs/tutorials/ktr3.ipynb` | Level knot placement with segments, knot distance, and knot dates. |
| `docs/tutorials/ktr4.ipynb` | Regressor signs and time-point coefficient priors. |
| `orbit/models/ktr.py` | Public KTR constructor, `pyro-svi` gate, and `ktrlite_optim_args`. |
| `orbit/models/ktrlite.py` | Public KTRLite constructor, `stan-map` gate, and `suppress_stan_log`. |
| `orbit/template/ktr.py` | Verified KTR methods: `fit_wbic`, `get_wbic`, `get_regression_coefs`, `get_regression_coef_knots`, `plot_regression_coefs`, `get_level_knots`, `get_levels`, `plot_lev_knots`. |
| `orbit/template/ktrlite.py` | Verified KTRLite methods: `get_level_knots`, `get_levels`, `plot_lev_knots`. |
| `orbit/utils/knots.py` | Knot/date conversion helpers and the explicit-date filtering behavior. |
| `orbit/utils/features.py` | Fourier and seasonal regressor helpers. |
| `tests/orbit/models/test_ktr.py` | KTR behavior for seasonality, regressors, knot dates, knot distance, regressor signs, and coefficient priors. |
| `tests/orbit/models/test_ktrlite.py` | KTRLite behavior for level knots, seasonality, decomposition, and hourly/daily data. |
| `tests/orbit/diagnostics/test_wbic.py` | KTR WBIC and KTRLite BIC selection hooks. |
| `tests/orbit/utils/test_knots.py` | Knot index/date conversion semantics. |

## Verified runtime facts

- `KTR` signature matches the public wrapper defaults recorded in `references/api-reference.md`.
- `KTRLite` signature matches the public wrapper defaults recorded in `references/api-reference.md`.
- `KTR` methods include `fit_wbic`, `get_wbic`, `get_regression_coefs`, `get_regression_coef_knots`, and
  `plot_regression_coefs`.
- `KTRLite` methods include `get_level_knots`, `get_levels`, and `plot_lev_knots`.
- Importing `orbit.template.ktr` directly can trigger a circular-import issue unless `orbit.models` is imported
  first; use `orbit.models` in runtime skill content.

## Out of scope anchors

The following materials were intentionally not folded into this sub-skill because they belong to other Orbit
workflows:

- ETS, LGT, and DLT fit-predict guidance
- generic backtesting / diagnostics flows
- unrelated utility workflows beyond knot helpers
