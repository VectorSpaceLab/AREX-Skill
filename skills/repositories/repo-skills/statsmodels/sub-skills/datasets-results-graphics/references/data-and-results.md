# Datasets and result objects

## Built-in datasets vs remote datasets

Built-in datasets live under `statsmodels.datasets` and are suitable for offline examples:

```python
import statsmodels.api as sm

data = sm.datasets.longley.load()
endog = data.endog
exog = sm.add_constant(data.exog)
res = sm.OLS(endog, exog).fit()
```

Many built-in dataset loaders expose `load()` and `load_pandas()`. `load_pandas()` is often more convenient for formula/DataFrame workflows.

`sm.datasets.get_rdataset(...)` downloads from an external source and can fail without network access, cache, or a changed remote dataset. Use it only when the user explicitly accepts network dependence; otherwise build a tiny local DataFrame or use a bundled dataset.

## Result attributes for computation

Use numeric attributes for downstream work:

| Attribute/method | Use |
| --- | --- |
| `params` | Coefficients or model parameters. |
| `bse` | Standard errors. |
| `pvalues` | Parameter p-values. |
| `conf_int(alpha=...)` | Confidence intervals. |
| `fittedvalues`, `resid` | Fitted values and residuals where available. |
| `aic`, `bic`, `llf` | Model comparison metrics where appropriate. |
| `get_prediction(...).summary_frame()` | Prediction mean/interval table for many models. |
| `summary()`, `summary2()` | Human-readable presentation tables. |

Do not parse `summary()` text for computation. Prefer structured attributes.

## Prediction frames

For formula models, pass a DataFrame with original variable names:

```python
pred = res.get_prediction(new_dataframe).summary_frame(alpha=0.05)
```

For matrix models, pass a design matrix with the same constant and column order used during fitting.

## Robust covariance result objects

Robust covariance methods often return a new result object. Keep both the base result and robust-covariance result if the user needs both classical and robust standard errors.

```python
robust = res.get_robustcov_results(cov_type="HC3")
print(robust.bse)
```

## Saving and loading

Statsmodels supports pickle-based result persistence through package helpers and result methods in many result classes. Pickle files are Python-version/package-version sensitive and should not be treated as a stable interchange format. For durable interchange, export parameters, standard errors, confidence intervals, and predictions to CSV/JSON/Parquet using pandas.
