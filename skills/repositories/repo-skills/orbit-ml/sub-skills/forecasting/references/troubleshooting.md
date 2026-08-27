# Forecasting Troubleshooting

Use this when ETS/LGT/DLT construction, fitting, prediction, intervals,
decomposition, regressors, or backend selection fails.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'orbit'` | `orbit-ml` is not installed in the active Python environment | Install `orbit-ml` with package-managed dependencies, then verify `python -c "from orbit.models import ETS, LGT, DLT"` |
| `ModuleNotFoundError: No module named 'cmdstanpy'` | Stan backend dependency missing | Install package dependencies that include `cmdstanpy`; verify `python -c "import cmdstanpy"` |
| `ModuleNotFoundError: No module named 'pyro'` | Pyro backend missing | Use `LGT(..., estimator="stan-map"|"stan-mcmc")` instead, or install Pyro/PyTorch dependencies before using `estimator="pyro-svi"` |
| Import works from a repo checkout but fails elsewhere | The package was not installed, and Python was only seeing a local source tree | Install `orbit-ml` in the environment where the skill will run; do not rely on source checkout paths |

Quick check:

```bash
python - <<'PY'
from orbit.models import ETS, LGT, DLT
print("forecasting imports ok")
PY
```

## Missing CmdStan or Stan compile/runtime failures

Stan estimators (`"stan-map"` and `"stan-mcmc"`) require CmdStan through
`cmdstanpy`. Symptoms include CmdStan-not-found errors, Stan model compilation
errors, or optimization/sampling failures before `fit()` returns.

Recovery steps:

1. Verify Python can import `cmdstanpy`.
2. Verify CmdStan is installed and discoverable:
   ```bash
   python - <<'PY'
   import cmdstanpy
   print(cmdstanpy.cmdstan_path())
   PY
   ```
3. If no CmdStan installation is available, install CmdStan using your normal
   environment policy (for example, `cmdstanpy.install_cmdstan()` in an
   authorized setup step). This may require network access and should not be
   hidden inside a forecasting run.
4. Re-run a tiny `ETS(..., estimator="stan-map", seasonality=1, verbose=False)`
   fit/predict before attempting large MCMC jobs.
5. Set `suppress_stan_log=False` to expose `cmdstanpy` logs when debugging.

## Estimator compatibility mistakes

| Mistake | Result | Fix |
| --- | --- | --- |
| `ETS(estimator="pyro-svi")` | `IllegalArgument` invalid estimator | Use `"stan-map"` or `"stan-mcmc"` |
| `DLT(estimator="pyro-svi")` | `IllegalArgument` invalid estimator | Use `"stan-map"` or `"stan-mcmc"`; Pyro-SVI is LGT-only |
| Unknown estimator string | `IllegalArgument` invalid estimator | Use exact strings: `"stan-map"`, `"stan-mcmc"`, or LGT-only `"pyro-svi"` |
| `pyro-svi` without Pyro installed | import/backend failure | Install Pyro/PyTorch dependencies or use a Stan estimator |

## Ordered-date validation

Orbit converts `date_col` to pandas datetimes and validates order.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ForecasterException: Datetime index must be ordered and not repeat` | Dates are unsorted or duplicated | Sort by `date_col`, drop/aggregate duplicate timestamps, and reset the index before `fit()` or `predict()` |
| Warning: datetime index is not evenly distributed | Irregular time gaps | Decide if irregular gaps are intended; otherwise reindex to a regular frequency and handle missing responses/covariates explicitly |
| `ForecasterException: Prediction start must be after training start.` | Prediction dataframe starts before training start | Trim prediction data or refit with an earlier training window |
| `IllegalArgument: Periods need to be greater than or equal to 1.` | `make_future_df(periods < 1)` | Pass `periods >= 1` |
| `make_future_df()` gives unusable dates | Training frequency cannot be inferred or data are irregular | Build the future dataframe manually with `pd.date_range(..., freq=...)` |

Prediction can start within the training range, at the training end, or after
training. It cannot start before the first training timestamp.

## Missing required columns

| Missing column | Where detected | Fix |
| --- | --- | --- |
| `date_col` in training data | `ForecasterException: DataFrame does not contain date_col` | Add/rename the date column and ensure it is parseable as datetime |
| `response_col` in training data | `ForecasterException: DataFrame does not contain response_col` | Add/rename the response column |
| `date_col` in prediction data | prediction metadata access fails | Include the same date column used for training |
| regressor column in training data | `ModelException: DataFrame does not contain specified regressor column(s).` | Ensure `set(regressor_col).issubset(train_df.columns)` |
| regressor column in prediction data | pandas key error or prediction failure | Prediction data must contain every trained regressor column, even for future dates |

Future prediction data does not need the response column, but it must contain
all regressors when the model was trained with `regressor_col`.

## Invalid regressor settings

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `IllegalArgument: Wrong dimension length in Regression Param Input` | `regressor_sign`, `regressor_beta_prior`, or `regressor_sigma_prior` length differs from `regressor_col` | Make every supplied list exactly the same length as `regressor_col` |
| Unexpected coefficient sign | Wrong `regressor_sign` ordering | Keep signs in the same order as `regressor_col`; valid signs are `"+"`, `"-"`, `"="` |
| Invalid/unknown `regression_penalty` | Misspelled penalty name | Use exact names: `"fixed_ridge"`, `"lasso"`, `"auto_ridge"` |
| DLT `ModelException` / `PredictionException`: regressors must be finite | NaN or infinite values in train or prediction regressors | Impute or remove invalid regressor values before `fit()`/`predict()` |
| LGT with regressors emits a deprecation warning | LGT regression support is slated for deprecation | Prefer `DLT` for new regressor workflows unless `LGT`/Pyro is required |

For DLT logistic global trend, `global_cap` must be greater than `global_floor`.
Invalid `global_trend_option` values must be replaced with `"linear"`,
`"loglinear"`, `"logistic"`, or `"flat"`.

## Missing-response behavior

ETS/LGT/DLT support missing response values during training, except for the very
first response value.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `DataInputException: The first value of response column ... cannot be missing` | The first training response is NaN | Start training at the first non-missing response or impute the initial value before fitting |
| LGT `DataInputException: LGT model does not allow negative response values` | Non-missing LGT response is negative | Transform the target, use a non-negative scale, or choose ETS/DLT if negative responses are valid for the task |
| Forecast output contains unexpected gaps | Missing responses were used for training but prediction dataframe is incomplete | Predict over the full date range you want returned; Orbit returns one row per prediction input row |

Missing response support applies to the response column, not to regressors. Keep
regressors finite whenever a model uses them.

## Bootstrap and percentile behavior

| Symptom | Explanation | Fix |
| --- | --- | --- |
| MAP output has only `prediction` | MAP is a point estimate and bootstrap is disabled by default | Set `n_bootstrap_draws > 0` and request interval percentiles |
| `prediction_percentiles=[]` still returns `prediction` | Orbit always adds the 50th percentile/point prediction | This is expected; use it to suppress interval columns |
| Full MCMC output has intervals without `n_bootstrap_draws` | Full posterior samples are used directly | This is expected; use `prediction_percentiles` to control reported columns |
| MCMC/SVI with `point_method="mean"` or `"median"` has only `prediction` | Posterior samples were aggregated before prediction | Add `n_bootstrap_draws > 0` if interval columns are needed |
| Bootstrap with too few draws fails or is unstable | Full Bayesian/SVI bootstrap requires at least 2 draws; tiny draw counts give noisy intervals | Use `n_bootstrap_draws >= 2`, and use much larger values for real interval estimates |
| Percentile columns appear in unexpected order | Orbit sorts percentiles and always inserts 50 | Build expected columns from the sorted set of requested percentiles plus 50 |

## Decomposition surprises

- `decompose=False` returns only prediction columns.
- `decompose=True` returns component columns as well.
- ETS components are `trend` and `seasonality`.
- LGT/DLT components are `trend`, `seasonality`, and `regression`.
- If a model has no regressors, the `regression` component for LGT/DLT is zero.
- If intervals are active, each component follows the same percentile suffix
  convention as `prediction`.

## Slow or expensive fits

- Start with `stan-map` and `seasonality=1` to validate data and columns.
- For MCMC, reduce `num_warmup`, `num_sample`, `chains`, and `cores` only for
  smoke/debug checks; increase them for real inference.
- For Pyro-SVI, reduce `num_steps`, `num_sample`, and `num_particles` only for
  smoke/debug checks; inspect `get_training_metrics()["loss_elbo"]` for real
  training quality.
- Do not run notebooks or native repository tests as a forecasting smoke check;
  use the bundled `scripts/smoke_forecasting.py` first.
