# Dataset loaders

Fairlearn dataset loaders largely follow `sklearn.datasets.fetch_openml`: they can cache downloads, return a Bunch, or return `(X, y)` directly.

## Common parameters

| Parameter | Meaning |
| --- | --- |
| `cache=True` | Use joblib/OpenML-style cache behavior. |
| `data_home=None` | Cache root; default is a `.fairlearn-data` directory under the user's home. Use an explicit path for reproducibility. |
| `as_frame=True` | Return pandas objects with feature names/dtypes when possible. |
| `return_X_y=False` | When true, return `(data, target)` instead of a Bunch. |

Common return fields for Bunch output include `data`, `target`, `feature_names`, `DESCR`, `categories`, and usually `frame` when `as_frame=True`.

## Loader table

| Loader | Task / target | Size and features | Extra parameters and caveats |
| --- | --- | --- | --- |
| `fetch_adult` | Binary classification: income `>50K` vs `<=50K` | 48,842 samples, 14 numeric/categorical features | Good default tutorial dataset; often use `sex` or `race` as sensitive features after loading. |
| `fetch_bank_marketing` | Binary classification: whether a client subscribes a term deposit | 45,211 samples, 16 numeric/categorical features | Marketing campaign data; target values are `yes`/`no`. |
| `fetch_credit_card` | Binary classification: default of credit-card clients | 30,000 samples, 23 real-valued features | Credit/lending-style allocation harm examples. |
| `fetch_diabetes_hospital` | Binary classification: readmitted within 30 days | 101,766 samples, 24 numeric/categorical/string features | The loader always fetches as a DataFrame internally before converting for `as_frame=False`. |
| `fetch_boston` | Regression: median house value | 506 samples, 13 features | Has known fairness issues and raises `DataFairnessWarning` by default; columns `B` and `LSTAT` require special care. |
| `fetch_acs_income` | Regression-style annual income target; can be thresholded for binary tasks | 1,664,500 rows, 10 features | `states` filters to two-letter abbreviations for 50 states plus `PR`; target column is income (`PINCP`). Large download. |

## ACSIncome columns

For `fetch_acs_income(as_frame=True)`, the inspected source's expected data columns are:

```text
AGEP, COW, SCHL, MAR, OCCP, POBP, RELP, WKHP, SEX, RAC1P
```

`states=None` returns all 50 states and Puerto Rico. Invalid state codes raise a `ValueError` explaining that codes must be two-letter abbreviations.

## Boston fairness warning

`fetch_boston(warn=True)` emits `DataFairnessWarning` with the message that the dataset has known fairness issues. Keep the warning visible. If a task uses Boston housing as an educational example, document the problematic `B` column and `LSTAT` caveat and avoid treating the dataset as a neutral benchmark.

## Example use

```python
from fairlearn.datasets import fetch_adult

X, y = fetch_adult(return_X_y=True, as_frame=True, data_home="/tmp/fairlearn-data")
A = X["sex"]
```

Then pass `A` to `MetricFrame` or mitigation estimators as `sensitive_features`. Keep `X`, `y`, and `A` aligned if you split or filter the data.

## Download discipline

- Use the script in this sub-skill without `--download` to inspect signatures without network access.
- Download one dataset at a time when disk or network limits matter.
- Use explicit `data_home` in CI, notebooks, or reproducibility reports.
- Cache invalidation and OpenML parser behavior can differ by scikit-learn version; record package versions when a loader behaves unexpectedly.
