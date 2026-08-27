# Data-preparation workflows

This reference covers the CausalML 0.17.0 data-preparation surface for synthetic data, feature encoders, propensity models, matching, and balance checks. See `data-contracts.md` for accepted column contracts and `troubleshooting.md` for failure modes.

## Synthetic data workflows

### Binary-treatment regression simulations

Use `causalml.dataset.synthetic_data` or one of its named simulation helpers when an estimator workflow needs arrays with known treatment effects.

```python
import numpy as np
from causalml.dataset import synthetic_data

np.random.seed(42)
y, X, treatment, tau, baseline, propensity = synthetic_data(
    mode=1,
    n=1000,
    p=5,
    sigma=1.0,
    adj=0.0,
)
```

Return contract:

- `y`: shape `(n,)`, observed outcome.
- `X`: shape `(n, p)`, numeric features.
- `treatment`: shape `(n,)`, binary treatment indicator with values `0` and `1`.
- `tau`: shape `(n,)`, true individual treatment effect.
- `baseline`: shape `(n,)`, expected baseline outcome.
- `propensity`: shape `(n,)`, true treatment probability.

`synthetic_data(mode=...)` dispatches to these helpers:

| mode | Helper | Intended stress test |
| --- | --- | --- |
| `1` | `simulate_nuisance_and_easy_treatment` | difficult nuisance functions, easier treatment effect |
| `2` | `simulate_randomized_trial` | randomized treatment with propensity `0.5` |
| `3` | `simulate_easy_propensity_difficult_baseline` | easier propensity, harder baseline |
| `4` | `simulate_unrelated_treatment_control` | separated treatment/control response surfaces |
| `5` | `simulate_hidden_confounder` | hidden-confounder binary outcome setup |

Use `p >= 5` for a portable default across modes. The helper uses NumPy global randomness; set `np.random.seed(...)` before calling when exact reproducibility matters.

### Synthetic uplift-classification data

Use `make_uplift_classification` for multi-arm uplift classification examples with a string treatment column.

```python
from causalml.dataset import make_uplift_classification

conditions = ["control", "email", "coupon"]
df, feature_names = make_uplift_classification(
    n_samples=1000,
    treatment_name=conditions,
    y_name="conversion",
    n_classification_features=10,
    n_classification_informative=5,
    n_uplift_increase_dict={"email": 2, "coupon": 2},
    n_uplift_decrease_dict={"email": 0, "coupon": 1},
    delta_uplift_increase_dict={"email": 0.03, "coupon": 0.08},
    delta_uplift_decrease_dict={"email": 0.0, "coupon": -0.02},
    random_seed=42,
)

X = df[feature_names]
y = df["conversion"]
treatment = df["treatment_group_key"]
```

The returned dataframe includes `treatment_group_key`, the requested outcome column, generated feature columns, and `treatment_effect`. For model training, exclude columns such as treatment labels, outcome, true effects, and generated probability columns from `feature_names` unless the task is explicitly an oracle simulation.

Use `make_uplift_classification_logistic` when the requested simulation should use logistic-response mechanics and per-treatment probability/effect columns.

```python
from causalml.dataset import make_uplift_classification_logistic

df, feature_names = make_uplift_classification_logistic(
    n_samples=1000,
    treatment_name=["control", "treatment1", "treatment2"],
    y_name="conversion",
    delta_uplift_dict={"treatment1": 0.02, "treatment2": -0.03},
    random_seed=42,
)
```

CausalML 0.17.0 does not expose `make_uplift_regression` from `causalml.dataset`. For continuous synthetic outcomes, use `synthetic_data(...)` and construct a dataframe around its array outputs if needed.

### Synthetic benchmarking helpers

For quick estimator comparisons on generated data:

```python
from causalml.dataset import (
    simulate_nuisance_and_easy_treatment,
    get_synthetic_preds,
    get_synthetic_summary,
    get_synthetic_preds_holdout,
    get_synthetic_summary_holdout,
    get_synthetic_auuc,
)

preds = get_synthetic_preds(simulate_nuisance_and_easy_treatment, n=1000)
summary = get_synthetic_summary(simulate_nuisance_and_easy_treatment, n=1000, k=3)
train_preds, valid_preds = get_synthetic_preds_holdout(
    simulate_nuisance_and_easy_treatment,
    n=1000,
    valid_size=0.2,
)
train_valid_summary = get_synthetic_summary_holdout(
    simulate_nuisance_and_easy_treatment,
    n=1000,
    valid_size=0.2,
    k=3,
)
auuc = get_synthetic_auuc(preds, plot=False)
```

The default prediction helpers may instantiate estimator classes and can be slower than plain data generation. For data-only preparation, call `synthetic_data` or the named simulation helper directly.

## Feature-matrix and encoding workflows

CausalML provides rare-level grouping encoders and a convenience loader in `causalml.features`.

### Numeric matrix from a pandas dataframe

```python
from causalml.features import load_data

feature_columns = ["age", "tenure", "region", "is_mobile"]
X = load_data(
    data=df,
    features=feature_columns,
    transformations={"tenure": lambda value: max(value, 0)},
)
```

`load_data` behavior:

- Converts boolean feature columns to integers.
- Applies optional per-column transformation functions before type detection.
- Treats non-numeric pandas columns as categorical.
- One-hot encodes categorical columns with `OneHotEncoder(min_obs=df.shape[0] * 0.001)` and converts the resulting sparse matrix to a dense NumPy array.
- Returns a `numpy.ndarray`, not a `numpy.matrix`.
- If all categorical levels are too rare or a categorical column is constant, it can drop that categorical encoding and return numeric columns only.

Use the lower-level encoders when train/test encoder consistency matters:

```python
from causalml.features import LabelEncoder, OneHotEncoder

label_encoder = LabelEncoder(min_obs=10).fit(train_df[categorical_columns])
train_labels = label_encoder.transform(train_df[categorical_columns])
test_labels = label_encoder.transform(test_df[categorical_columns])

ohe = OneHotEncoder(min_obs=10).fit(train_df[categorical_columns])
train_sparse = ohe.transform(train_df[categorical_columns])
test_sparse = ohe.transform(test_df[categorical_columns])
```

Rare or unseen labels map to the grouped label `0` in `LabelEncoder`; `OneHotEncoder` drops that grouped label from explicit dummy columns.

The CausalML 0.17.0 data-preparation module exposes `LabelEncoder`, `OneHotEncoder`, and `load_data`. A class named `FeatureEffectExplainer` is not available from `causalml.features`; route feature-selection or interpretation tasks to the analysis-and-decision sub-skill.

## Propensity-score workflows

### Elastic-net logistic propensity

```python
from causalml.propensity import ElasticNetPropensityModel

pm = ElasticNetPropensityModel(
    n_fold=5,
    random_state=42,
    calibrate=True,
    clip_bounds=(1e-3, 1 - 1e-3),
)
propensity = pm.fit_predict(X, treatment)
```

`ElasticNetPropensityModel` is a `LogisticRegressionPropensityModel` specialization. It uses a cross-validated elastic-net logistic model and returns clipped probabilities through `fit_predict(X, y)`.

### Gradient-boosted propensity

```python
from causalml.propensity import GradientBoostedPropensityModel

pm = GradientBoostedPropensityModel(
    random_state=42,
    early_stop=False,
    calibrate=True,
    clip_bounds=(1e-3, 1 - 1e-3),
)
propensity = pm.fit_predict(X, treatment)
```

Set `early_stop=True` to split an internal validation set and pass it to the XGBoost classifier. This path requires the optional XGBoost dependency to import successfully.

### Function wrapper

```python
from causalml.propensity import compute_propensity_score

p_hat, fitted_model = compute_propensity_score(
    X=train_X,
    treatment=train_treatment,
    X_pred=score_X,
    calibrate_p=True,
    clip_bounds=(1e-3, 1 - 1e-3),
)
```

If `p_model` is omitted, the wrapper fits an `ElasticNetPropensityModel`. If a custom `p_model` is supplied, it must support either `predict_proba` or `predict` after `fit`.

### R-loss residuals for downstream learners

```python
from sklearn.ensemble import RandomForestRegressor
from causalml.propensity import compute_r_residuals

y_residual, w_residual = compute_r_residuals(
    X=X,
    treatment=treatment,
    y=y,
    outcome_learner=RandomForestRegressor(random_state=42),
    n_folds=5,
    random_state=42,
)
```

Use `method="predict_proba"` for classifier outcome learners where the positive-class probability is the desired outcome prediction. Set `compute_w_residual=False` when a caller only needs the outcome residual.

## Nearest-neighbor matching workflows

### Match on a propensity score

```python
import pandas as pd
from causalml.match import NearestNeighborMatch

work = df.copy()
work["treatment"] = work["treatment"].astype(int)
work["propensity"] = propensity

matcher = NearestNeighborMatch(
    caliper=0.2,
    replace=False,
    ratio=1,
    shuffle=True,
    treatment_to_control=True,
    random_state=42,
    n_jobs=-1,
)
matched = matcher.match(
    data=work,
    treatment_col="treatment",
    score_cols=["propensity"],
)
pair_index = matcher.matched_indexes_
```

Important behavior:

- `treatment_col` is interpreted as `1` for treatment and `0` for control.
- `treatment_to_control=True` matches treated units to controls; `False` reverses the direction.
- `replace=False` supports one score column only.
- `replace=True` supports multiple score columns, scales them internally, and may return duplicate matched controls.
- `ratio` controls how many opposite-arm units are selected per source-arm unit.
- `caliper` is a standardized distance threshold; tighter calipers improve similarity but can reduce retained sample size.
- After `match(...)`, `matched_indexes_` is a dataframe with `from` and `to` original indices for accepted pairs.

### Exact group-stratified matching

```python
matched = matcher.match_by_group(
    data=work,
    treatment_col="treatment",
    score_cols=["propensity"],
    groupby_col="country",
)
```

`match_by_group` runs matching independently inside each exact group stratum and combines the matched rows. Use it when a column must not cross-match, such as experiment cell, region, platform, or time cohort. Every group should contain both treatment values and enough controls for the requested ratio.

### Multi-column matching

```python
matcher = NearestNeighborMatch(
    caliper=0.2,
    replace=True,
    ratio=2,
    random_state=42,
)
matched = matcher.match(
    data=work,
    treatment_col="treatment",
    score_cols=["propensity", "age", "tenure"],
)
```

Only use multiple `score_cols` with `replace=True`. Include numeric, scaled, non-leaky covariates; avoid outcome, post-treatment, or target-leakage columns.

## Balance-table workflow

```python
from causalml.match import create_table_one

balance_before = create_table_one(
    data=work,
    treatment_col="treatment",
    features=["age", "tenure", "propensity"],
    with_std=True,
    with_counts=True,
)

balance_after = create_table_one(
    data=matched,
    treatment_col="treatment",
    features=["age", "tenure", "propensity"],
)
```

`create_table_one` returns a dataframe with `Control`, `Treatment`, and `SMD` columns. `SMD` is the standardized mean difference between treated and control values. Lower absolute SMD indicates better balance; a common review threshold is `abs(SMD) < 0.1`, but user or domain criteria should override that default.

## MatchOptimizer workflow

`MatchOptimizer` searches caliper and propensity-threshold settings to reduce imbalance under retention constraints.

```python
import numpy as np
from causalml.match import MatchOptimizer

optimizer = MatchOptimizer(
    treatment_col="treatment",
    ps_col="propensity",
    matching_covariates=["propensity", "age", "tenure"],
    max_smd=0.1,
    max_deviation=0.1,
    caliper_range=(0.01, 0.5),
    max_pihat_range=(0.95, 0.999),
    max_iter_per_param=5,
    min_users_per_group=100,
    smd_cols=["propensity"],
    dev_cols_transformations={"propensity": np.mean},
    verbose=True,
)
matched = optimizer.search_best_match(work)
```

Use this when a fixed caliper has poor common support or unacceptable standardized mean differences. It still assumes binary `0/1` treatment and numeric matching covariates.

## CSV matching workflow

Use the bundled helper for quick file-based matching from the `causalml` skill root:

```bash
python sub-skills/data-preparation/scripts/match_csv.py \
  --input input.csv \
  --output matched.csv \
  --treatment-column treatment \
  --feature-columns age tenure region \
  --matching-covariates age tenure propensity \
  --score-column propensity \
  --groupby-column market \
  --caliper 0.2 \
  --replace \
  --ratio 1 \
  --random-state 42
```

If the score column is already present, the helper reuses it by default. If it is absent, or if `--force-propensity` is supplied, the helper fits an `ElasticNetPropensityModel` from `--feature-columns` and writes the result into `--score-column` before matching.
