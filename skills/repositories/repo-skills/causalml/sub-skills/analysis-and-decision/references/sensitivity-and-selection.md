# Sensitivity analysis, feature selection, and interpretation

This reference covers causalml 0.17.0 robustness checks, uplift feature filters, and interpretation helpers for fitted CATE/uplift models.

## Sensitivity analysis data contract

Imports:

```python
from causalml.metrics.sensitivity import (
    Sensitivity,
    SensitivityPlaceboTreatment,
    SensitivityRandomCause,
    SensitivityRandomReplace,
    SensitivitySubsetData,
    SensitivitySelectionBias,
    SensitivityMSM,
    one_sided,
    alignment,
    one_sided_att,
    alignment_att,
)
```

Common constructor shape:

```python
sens = Sensitivity(
    df=df,
    inference_features=feature_names,
    p_col="p",
    treatment_col="w",
    outcome_col="y",
    learner=learner,
)
```

Required columns:

- `inference_features`: feature columns used by the learner.
- `p_col`: propensity score in `(0, 1)` for each row.
- `treatment_col`: treatment assignment.
- `outcome_col`: observed outcome.

Learner requirements:

- For standard sensitivity summaries, the learner must support `fit_predict(X=..., p=..., treatment=..., y=...)` or `fit_predict(X=..., treatment=..., y=...)`.
- The learner must support `estimate_ate(X=..., p=..., treatment=..., y=...)`; if it supports `return_ci=True`, the sensitivity summary will use that path.
- `TMLELearner` exposes `estimate_ate` but not `fit_predict`, so it is not a drop-in learner for the base `Sensitivity` summary path.

Treatment labels:

- Numeric `0`/`1` treatment is safest for all sensitivity classes.
- String labels can work for learner-driven placebo/random-cause/random-replace/subset workflows when the learner has the correct `control_name`.
- `SensitivitySelectionBias` confounding functions perform arithmetic with `treatment`; use numeric `0`/`1` treatment there.
- `SensitivityMSM` converts raw treatment to an indicator using `learner.control_name` when present, but still passes raw treatment into the learner for potential-outcome fitting.

## Standard robustness/refutation methods

The dispatcher accepts exact method names:

```python
summary = sens.sensitivity_analysis(
    methods=[
        "Placebo Treatment",
        "Random Cause",
        "Subset Data",
        "Random Replace",
        "Selection Bias",
        "MSM",
    ],
    sample_size=0.5,
    confound="one_sided",
    alpha_range=None,
)
```

| Method name | Class | What changes |
| --- | --- | --- |
| `Placebo Treatment` | `SensitivityPlaceboTreatment` | Randomly permutes treatment assignment |
| `Random Cause` | `SensitivityRandomCause` | Adds one irrelevant random covariate |
| `Subset Data` | `SensitivitySubsetData` | Samples a fraction of rows; requires `sample_size` |
| `Random Replace` | `SensitivityRandomReplace` | Replaces one feature with random noise; pass `replaced_feature` for determinism |
| `Selection Bias` | `SensitivitySelectionBias` | Adjusts outcome using a specified unobserved-confounding function |
| `MSM` | `SensitivityMSM` | Reports marginal sensitivity model ATE bounds over Gamma values |

`SensitivityRandomFeature` is not a public class in causalml 0.17.0. Use `SensitivityRandomCause` to add a random feature or `SensitivityRandomReplace` to replace an existing feature.

## Selection-bias workflow

```python
sel = SensitivitySelectionBias(
    df,
    feature_names,
    p_col="p",
    treatment_col="w",
    outcome_col="y",
    learner=learner,
    confound="alignment",
    alpha_range=None,
    sensitivity_features=feature_names,
)
sens_df, partial_rsqs_df = sel.causalsens()
summary = sel.summary(method="Selection Bias")
SensitivitySelectionBias.plot(sens_df, partial_rsqs_df, type="r.squared", ci=True, partial_rsqs=True)
```

Confounding functions:

- `one_sided(alpha, p, treatment)`: one-sided confounding for ATE.
- `alignment(alpha, p, treatment)`: alignment confounding for ATE.
- `one_sided_att(alpha, p, treatment)`: one-sided confounding for ATT.
- `alignment_att(alpha, p, treatment)`: alignment confounding for ATT.

If `alpha_range` is not supplied, it is built from the outcome interquartile range and sorted with zero included. Selection-bias summaries return the standard columns `Method`, `ATE`, `New ATE`, `New ATE LB`, and `New ATE UB`.

The implementation logs that selection-bias partial-R-squared interpretation currently targets linear outcome-model behavior. Treat it as a fragility diagnostic rather than a proof of no hidden bias.

## Marginal sensitivity model bounds

```python
msm = SensitivityMSM(
    df=df,
    inference_features=feature_names,
    p_col="p",
    treatment_col="w",
    outcome_col="y",
    learner=learner,
    gamma=[1.0, 1.5, 2.0, 3.0],
)
bounds = msm.get_msm_bounds(gamma=[1.0, 2.0, 4.0])
```

`SensitivityMSM` returns a DataFrame with `gamma`, `ate_lower`, and `ate_upper`. All gamma values must be at least `1.0`; Gamma 1 should collapse to the point estimate.

Supported learner families are S-learner, T-learner, and DR-learner objects whose `fit_predict(return_components=True)` exposes potential-outcome regressions. X-learner and R-learner are rejected because their components are not the required `mu0_hat` and `mu1_hat` potential-outcome regressions.

## Uplift feature selection with `FilterSelect`

Import:

```python
from causalml.feature_selection.filters import FilterSelect
```

Main API:

```python
importance = FilterSelect().get_importance(
    data=df,
    features=feature_names,
    y_name="conversion",
    method="KL",                       # "F", "LR", "KL", "ED", or "Chi"
    experiment_group_column="treatment_group_key",
    control_group="control",
    treatment_group="treatment1",
    n_bins=5,
    null_impute=None,
    order=1,
    disp=False,
)
```

Return columns are `method`, `feature`, `rank`, `score`, `p_value`, and `misc`, sorted with the largest score first.

### Method contracts

| Method | Outcome requirement | Treatment scope | Notes |
| --- | --- | --- | --- |
| `F` | Binary or continuous | One treatment group vs control | OLS F-test for treatment-feature interactions; `order` must be 1, 2, or 3 |
| `LR` | Binary `{0, 1}` | One treatment group vs control | Logistic likelihood-ratio test; `disp=True` shows statsmodels convergence output |
| `KL` | Binary `{0, 1}` | Multi-treatment relative to `control_group` | Bin-based uplift divergence; numeric feature bins via quantiles |
| `ED` | Binary `{0, 1}` | Multi-treatment relative to `control_group` | Euclidean-distance divergence |
| `Chi` | Binary `{0, 1}` | Multi-treatment relative to `control_group` | Chi-square-style divergence |

For `F` and `LR`, `get_importance` filters `data` to `control_group` and `treatment_group`, then creates a temporary binary treatment indicator. For `KL`/`ED`/`Chi`, it keeps all treatment groups and compares each non-control treatment against the specified control group.

`null_impute` can be `"mean"`, `"median"`, `"most_frequent"`, or `None`. If it is `None` and a selected feature has nulls, the divergence filters raise an exception asking for imputation.

## Meta-learner importances and SHAP interpretation

Most meta-learner classes expose interpretation methods after CATE estimation, including common `LRSRegressor`/S-, T-, X-, R-, and DR-style learners that inherit the shared base interpretation helpers:

```python
tau = learner.fit_predict(X=X, treatment=treatment, y=y)
importance = learner.get_importance(
    X=X,
    tau=tau,
    model_tau_feature=None,      # defaults to LightGBM regressor when available
    features=feature_names,
    method="auto",              # "auto" or "permutation"
    normalize=True,
    random_state=42,
)
shap_values = learner.get_shap_values(X=X, tau=tau, features=feature_names)
learner.plot_importance(X=X, tau=tau, features=feature_names, method="auto")
learner.plot_shap_values(X=X, shap_dict=shap_values, features=feature_names)
learner.plot_shap_dependence(
    treatment_group="treatment1",
    feature_idx="feature_0",
    X=X,
    tau=tau,
    shap_dict=shap_values,
    features=feature_names,
    interaction_idx="auto",
)
```

Contracts:

- `X`, `tau`, and treatment-group class metadata must be available.
- A one-dimensional `tau` is reshaped internally to `(n, 1)`; multi-treatment `tau` should have one column per non-control treatment group in learner class order.
- `method="auto"` uses the fitted `model_tau_feature.feature_importances_` values, normalized when requested.
- `method="permutation"` uses held-out permutation importance; in causalml 0.17.0 the common explainer checks that the tau model has `feature_importances_` after fitting, so a tree-based tau model is the least surprising choice even for permutation.
- SHAP uses `shap.TreeExplainer`, so choose a tree-compatible tau model.

`FeatureEffectExplainer` is not present as a public causalml 0.17.0 API. Use meta-learner `get_importance`/SHAP helpers, the internal `Explainer` path exposed by learners, or `FilterSelect` for uplift feature screening.

## Uplift tree importances

For fitted `UpliftTreeClassifier` and `UpliftRandomForestClassifier` models, use their `feature_importances_` array with the feature names supplied at fit time. Tree fitting, fill/prune, save/load, and tree plotting are handled by the tree-models sub-skill; this sub-skill consumes those importances when interpreting targeting decisions or combining tree results with metric scores.
