# Cross-cutting statsmodels troubleshooting

## Import or install failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: statsmodels` | Package not installed in the active environment | Install with `python -m pip install statsmodels` or `conda install -c conda-forge statsmodels`; verify with `python -c "import statsmodels"`. |
| Source checkout import fails with missing `_version` or compiled modules | The checkout is being imported without a built editable/install step | For source work, install the checkout in editable mode with Meson/Cython build requirements; for users, install a release wheel instead. |
| Build fails on C compiler, Meson, Cython, NumPy/SciPy headers | Source build prerequisites missing or incompatible | Prefer binary wheels/conda; otherwise install compiler, Meson, Cython, and documented build dependencies before `pip install -e .`. |
| Plot functions fail in headless CI | Matplotlib missing or GUI backend selected | Install matplotlib and set `MPLBACKEND=Agg` or call `matplotlib.use("Agg")` before importing pyplot. |
| X-13/X-12 functions fail | External Census executable missing or not discoverable | Treat this as optional; install/configure X-13/X-12 and verify the executable separately. |

## Data and model specification failures

- **All parameter estimates are `NaN`**: check missing data. Many models default to `missing='none'`. Use `missing='raise'` while validating or `missing='drop'` deliberately.
- **Rank deficiency or multicollinearity**: linear-like models may use a generalized inverse instead of raising. Check matrix rank, condition number, variance inflation, or remove redundant columns.
- **Perfect or quasi-perfect prediction**: binary and count models may raise or warn, fail to converge, or produce extreme estimates. Revisit predictors, regularization, collapsed categories, or model family.
- **Convergence warnings**: inspect `mle_retvals`, iteration counts, Hessian/information matrix, starting values, scaling, and whether parameters are near a boundary.
- **Wrong intercept**: array APIs do not always add a constant. Use `sm.add_constant`; formula APIs usually add an intercept unless `0` or `-1` is included.
- **Unexpected categorical encoding**: formula workflows use patsy. Use `C(var)` for categorical treatment and inspect the design matrix names.

## Result and prediction confusion

- Prediction shape depends on the model and the shape/index of new `exog`. Preserve column order and constant handling.
- Robust covariance is usually requested through fit options or result methods such as `get_robustcov_results(cov_type=...)`; do not overwrite original estimates without documenting covariance choice.
- For time series, date/frequency information affects forecasting indexes. Ensure the input Series/DataFrame has a usable index or pass explicit dates/frequency.
- Summary tables are presentation objects. Use numeric attributes such as `params`, `bse`, `pvalues`, and `conf_int()` for downstream computation.

## Debugging workflow

1. Reproduce with a tiny deterministic subset.
2. Verify imports and optional dependencies with `scripts/check_statsmodels_env.py`.
3. Print model constructor arguments, `endog`/`exog` shapes, missing counts, column names, and constant handling.
4. Fit once per model instance when comparing fit options; do not rely on stale result objects after refitting the same model object with different parameters.
5. Route to the nearest sub-skill for workflow-specific warnings and recovery.
