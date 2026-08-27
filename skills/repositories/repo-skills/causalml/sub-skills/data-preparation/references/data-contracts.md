# Data contracts for CausalML data preparation

Use these contracts before calling the workflows in `workflows.md`.

## Core columns

| Column type | Contract | Notes |
| --- | --- | --- |
| Binary treatment for propensity/matching | One-dimensional array or dataframe column with values `0` and `1` | `0` is control, `1` is treated. Cast booleans to integers before matching. |
| Outcome | One-dimensional array/series, usually numeric for regressors and binary for classifiers | Do not include the outcome in feature columns used for propensity or matching. |
| Feature matrix | `X` with shape `(n_samples, n_features)` | Use numeric arrays/dataframes or encode categorical columns first. |
| Propensity score | Numeric vector/column with values between `0` and `1` | Clipped scores such as `[1e-3, 1 - 1e-3]` are safer for downstream learners. |
| Matching score columns | List of numeric columns | `NearestNeighborMatch(replace=False)` accepts exactly one score column; `replace=True` accepts multiple numeric score columns. |
| Balance covariates | Numeric dataframe columns | `create_table_one` computes means, standard deviations, and SMD, so raw strings are not valid balance inputs. |
| Group stratum | One dataframe column used with `match_by_group` | Each group should contain both treatment arms and enough controls for the requested ratio. |

## Synthetic array contract

`synthetic_data(...)` and the named regression simulation helpers return:

```python
y, X, treatment, tau, baseline, propensity = synthetic_data(...)
```

Required shape checks:

```python
assert X.shape[0] == len(y) == len(treatment) == len(tau) == len(baseline) == len(propensity)
assert set(treatment).issubset({0, 1})
assert X.ndim == 2
```

Use `p >= 5` unless a specific simulation has been reviewed for smaller feature counts. Set `np.random.seed(...)` before `synthetic_data(...)` if deterministic examples are required.

## Synthetic uplift-classification dataframe contract

`make_uplift_classification(...)` and `make_uplift_classification_logistic(...)` return:

```python
df, feature_names = make_uplift_classification(...)
```

Expected columns and values:

- `df["treatment_group_key"]`: string treatment label. The first value in `treatment_name` is the control label by convention.
- `df[y_name]`: generated binary outcome column, default `conversion`.
- `feature_names`: list of generated observed feature columns suitable for model input.
- `make_uplift_classification(...)` also provides `treatment_effect`.
- `make_uplift_classification_logistic(...)` provides probability and true-effect columns per treatment; treat these as oracle/audit columns, not ordinary model features.

For binary propensity or matching APIs, convert a two-arm uplift dataframe into a numeric treatment flag:

```python
control_name = "control"
treatment_name = "treatment1"
subset = df[df["treatment_group_key"].isin([control_name, treatment_name])].copy()
subset["treatment"] = (subset["treatment_group_key"] == treatment_name).astype(int)
X = subset[feature_names]
y = subset["conversion"]
```

Do not pass multi-arm string labels directly to `ElasticNetPropensityModel` or `NearestNeighborMatch`; those APIs are binary-treatment utilities.

## Feature-column contract

Good feature columns are pre-treatment covariates. Exclude:

- treatment labels or treatment-assignment metadata unless intentionally modeling assignment in a propensity model;
- observed outcome columns;
- true effect columns such as `tau`, `treatment_effect`, or `*_true_effect`;
- generated probability columns such as `conversion_prob` or `*_conversion_prob` unless the task is an oracle diagnostic;
- post-treatment variables, future information, leakage flags, row ids, or target-derived columns.

`load_data(data, features, transformations={})` expects a pandas dataframe. It returns a dense `numpy.ndarray`. It fits encoders on the dataframe passed into the call, so for production train/test splits use an explicit encoder fitted on train data when stable category mappings are required.

## Pandas, NumPy, and Polars notes

- `synthetic_data` returns NumPy arrays.
- `make_uplift_classification` and `make_uplift_classification_logistic` return pandas dataframes.
- `load_data` is a pandas-oriented helper and uses pandas dtype inspection.
- `NearestNeighborMatch`, `MatchOptimizer`, `create_table_one`, and the bundled CSV helper expect pandas dataframes because they rely on pandas indexing, grouping, and pivot-table operations.
- Propensity model docstrings accept NumPy arrays, pandas dataframes/series, and Polars dataframes/series when the installed scikit-learn stack supports them. Convert to pandas or NumPy before matching.
- Polars LazyFrame support is not a matching contract; collect or convert before data-preparation matching routines.

## Propensity model input contract

`ElasticNetPropensityModel`, `LogisticRegressionPropensityModel`, and `GradientBoostedPropensityModel` use a classifier-style API:

```python
model.fit(X, treatment)
p = model.predict(X)
p = model.fit_predict(X, treatment)
```

Requirements:

- `X` has one row per treatment value.
- `treatment` has exactly two classes for these binary propensity models.
- Cross-validation folds need both treatment arms; avoid very small or one-sided samples.
- `clip_bounds` should satisfy `0 < lower < upper < 1`.
- Calibrated models require fitted score variation. Disable calibration only when you understand the downstream impact.

## Matching input contract

`NearestNeighborMatch.match(data, treatment_col, score_cols)` expects:

```python
assert treatment_col in data.columns
assert isinstance(score_cols, list)
assert all(col in data.columns for col in score_cols)
assert set(data[treatment_col].dropna().astype(int).unique()).issubset({0, 1})
```

Additional constraints:

- For `replace=False`, `score_cols` length must be `1`.
- For `replace=True`, all score columns are internally standardized before neighbor search.
- Missing score values should be removed or imputed before matching.
- If `ratio > 1`, verify the output counts rather than assuming every treated unit found the requested number of controls; calipers and scarce control pools can reduce matches.
- If matching by group, each group is handled independently, and groups lacking common support can produce few or no matches.

## Balance-table contract

`create_table_one(data, treatment_col, features, with_std=True, with_counts=True)` expects numeric `features` and binary treatment labels. It returns rows for the requested features plus an optional `n` row. The `SMD` column is numeric for feature rows and blank for the count row.

Recommended audit checks:

```python
table = create_table_one(matched, "treatment", ["age", "tenure", "propensity"])
smd = table.loc[table.index != "n", "SMD"].astype(float).abs()
assert (smd < 0.1).all()  # replace with the task's balance criterion
```

## CSV helper contract

`scripts/match_csv.py` expects a delimited file readable by `pandas.read_csv` and writes a CSV with matched rows. The treatment column must be binary or castable to binary integers. If the requested score column is absent or `--force-propensity` is used, `--feature-columns` must be supplied so the helper can estimate a propensity score. Balance tables print only when the requested matching covariates support `create_table_one`.
