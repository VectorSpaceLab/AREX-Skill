# Optional EconML, CausalML, and TabPFN CATE Boundaries

Use this reference when the user asks for heterogeneous treatment effects,
conditional average causal effects, or optional third-party estimators through
DoWhy's `CausalModel.estimate_effect` API.

## First decision: built-in conditional estimates or external CATE?

Use built-in DoWhy regression conditional estimates when:

- the user needs a quick grouped CACE table by effect modifiers;
- a linear or GLM outcome model is scientifically acceptable;
- optional EconML/CausalML/TabPFN packages are unavailable or outside budget;
- the data are small and interpretability is more important than flexible
  machine-learning nuisance models.

Use EconML/CausalML when:

- the user needs flexible CATE estimates over effect modifiers;
- the treatment/outcome shapes match a specific third-party estimator;
- the user can install and configure the optional package;
- estimator-specific nuisance models, cross-fitting, inference, or metalearner
  behavior are part of the research question.

Use TabPFN only when:

- the user explicitly wants TabPFN as an outcome-model estimator;
- `tabpfn` and `torch` are installed and model/authentication/cache constraints
  are acceptable;
- the tabular dataset is within TabPFN's practical size/class limits.

## EconML wrapper grammar

DoWhy's EconML wrapper is selected by method-name strings of the form:

```text
backdoor.econml.<econml.module.EstimatorClass>
iv.econml.<econml.module.EstimatorClass>
```

Common examples:

```python
"backdoor.econml.dml.dml.LinearDML"
"backdoor.econml.dml.LinearDML"
"backdoor.econml.dr.LinearDRLearner"
"backdoor.econml.metalearners.SLearner"
"backdoor.econml.orf.DMLOrthoForest"
"iv.econml.iv.dml.DMLIV"
"iv.econml.iv.dr.LinearIntentToTreatDRIV"
```

The part after `econml.` must identify an importable EconML estimator class in
the user's environment. DoWhy records that string in `method_params` and creates
a `dowhy.causal_estimators.econml.Econml` wrapper.

## EconML data mapping

The wrapper maps DoWhy variables to EconML fit arguments by name:

| EconML argument | DoWhy source |
|---|---|
| `Y` | outcome column, `data[outcome[0]]` |
| `T` | treatment columns, `data[treatment]` |
| `X` | effect modifiers, if present |
| `W` | adjustment variables from the identified estimand |
| `Z` | instrumental variables, if present |

The wrapper introspects the estimator's `.fit()` signature and passes only the
arguments accepted by that estimator. This makes method choice important:
metalearners, DML, DR learners, and IV estimators expect different combinations
of `X`, `W`, and `Z`.

## Minimal EconML pattern

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import PolynomialFeatures

estimate = model.estimate_effect(
    estimand,
    method_name="backdoor.econml.dml.dml.LinearDML",
    control_value=0,
    treatment_value=1,
    target_units=lambda data: data["X0"] > 1,
    confidence_intervals=False,
    method_params={
        "init_params": {
            "model_y": GradientBoostingRegressor(random_state=7),
            "model_t": GradientBoostingRegressor(random_state=7),
            "model_final": LassoCV(cv=3),
            "featurizer": PolynomialFeatures(degree=1, include_bias=True),
        },
        "fit_params": {},
    },
)

print(estimate.value)           # ATE over target_units after averaging CATEs.
print(estimate.cate_estimates)  # Pointwise CATEs returned by the wrapper.
```

Rules:

- Put constructor options for the underlying EconML estimator under
  `method_params["init_params"]`.
- Put fit-time options under `method_params["fit_params"]`.
- Provide effect modifiers to `CausalModel(..., effect_modifiers=[...])` or
  `estimate_effect(..., effect_modifiers=[...])`; otherwise many CATE methods
  have no `X` features to condition on.
- Set random seeds on sklearn/EconML nuisance models when reproducibility
  matters.

## EconML target units

For EconML wrappers, `target_units` controls the rows used for effect
prediction/averaging:

| `target_units` value | Behavior |
|---|---|
| `"ate"` | Use the fitted effect-modifier matrix, if present, and average pointwise effects. |
| callable | Apply the callable to the data and keep selected rows for CATE prediction. |
| pandas DataFrame | Treat it as an effect-modifier grid for prediction. |

The returned `CausalEstimate` may include:

- `value`: average effect over selected rows;
- `cate_estimates`: pointwise effects;
- `effect_intervals`: when `confidence_intervals=True` and the underlying
  estimator supports intervals;
- `_estimator_object`: underlying EconML estimator instance;
- `estimate.estimator`: DoWhy wrapper instance.

After fitting once, reuse the same wrapper for a new effect grid:

```python
first = model.estimate_effect(
    estimand,
    method_name="backdoor.econml.metalearners.SLearner",
    method_params={"init_params": {"overall_model": model_obj}, "fit_params": {}},
)

new_grid = df[["X0", "X1"]].sample(frac=0.1, random_state=7)
second = model.estimate_effect(
    estimand,
    method_name="backdoor.econml.metalearners.SLearner",
    fit_estimator=False,
    target_units=new_grid,
)
```

Ensure the new grid contains exactly the effect-modifier columns expected by the
fitted wrapper.

## EconML metalearner caution

When the underlying EconML estimator module ends with `metalearners`, DoWhy
concatenates common causes not already in effect modifiers into the `X` feature
set because EconML metalearners accept a single feature argument. This can change
feature interpretation. State this explicitly when using `SLearner`, `TLearner`,
`XLearner`, or related metalearners.

## EconML IV estimators

Use `iv.econml...` only when the identified estimand has instruments:

```python
iv_estimate = model.estimate_effect(
    estimand,
    method_name="iv.econml.iv.dml.DMLIV",
    control_value=0,
    treatment_value=1,
    method_params={"init_params": {...}, "fit_params": {}},
)
```

Diagnostics:

- Check `estimand.get_instrumental_variables()` before calling the estimator.
- Ensure the selected EconML IV estimator accepts the `Z` argument.
- Some deep IV estimators may require additional optional packages or backends.
  Keep those dependencies user-approved and outside the runtime skill tree.

## CausalML wrapper grammar

CausalML wrapper names have the form:

```text
backdoor.causalml.<causalml.module.EstimatorClass>
```

Examples:

```python
"backdoor.causalml.inference.meta.LRSRegressor"
"backdoor.causalml.inference.meta.XGBTRegressor"
"backdoor.causalml.inference.meta.MLPTRegressor"
"backdoor.causalml.inference.meta.BaseXRegressor"
"backdoor.causalml.inference.meta.BaseRRegressor"
```

The wrapper maps data to CausalML methods roughly as:

| CausalML argument | DoWhy source |
|---|---|
| `X` | adjustment variables plus effect modifiers |
| `y` | outcome column |
| `treatment` | treatment column |

The wrapper calls the underlying estimator's `estimate_ate` and `fit_predict`
methods. Returned estimates can include an ATE value tuple, CATE estimates, and
intervals from CausalML.

Cautions:

- `causalml` is optional and may require extra compiled dependencies.
- The wrapper is primarily a backdoor/CATE integration surface.
- Confirm the selected CausalML estimator supports the treatment encoding and
  outcome type.

## TabPFN estimator boundary

DoWhy includes a `backdoor.tabpfn` estimator module, but it is optional in
practice because it imports `tabpfn` and `torch`.

Minimal pattern:

```python
estimate = model.estimate_effect(
    estimand,
    method_name="backdoor.tabpfn",
    method_params={
        "model_type": "auto",      # "auto", "classifier", or "regressor"
        "n_estimators": 4,
        "use_multi_gpu": False,
        "max_num_classes": 10,
    },
)
```

Operational boundaries:

- `model_type="auto"` chooses classifier for categorical/bool/small-cardinality
  integer outcomes, otherwise regressor.
- Classification mode enforces a maximum number of classes.
- TabPFN performs best on bounded tabular sizes; very large row/feature counts
  should use other estimators or downsampling.
- Multi-GPU support is controlled by `use_multi_gpu` and `device_ids`; do not
  assume a GPU is available.
- Some TabPFN model versions require external model access/authentication. Do
  not start downloads or authentication flows without user approval.

## Optional dependency error handling

When an optional wrapper fails to import:

1. Confirm the user's requested estimator really needs the optional package.
2. Report the missing package and the smallest install extra/package needed.
3. Offer a built-in fallback only if it answers the same causal question.
4. Do not silently switch from CATE to ATE or from IV to backdoor.

Examples of safe fallbacks:

- EconML CATE unavailable → use `backdoor.linear_regression` with effect
  modifiers for a linear conditional-effect baseline.
- CausalML unavailable → use EconML if installed and the estimator family has an
  equivalent; otherwise use a built-in backdoor estimator and state that CATE is
  not covered.
- TabPFN unavailable or too expensive → use `backdoor.linear_regression`,
  `backdoor.generalized_linear_model`, or a user-approved external ML estimator
  through EconML/CausalML.

## Refutation with external estimators

Most refuters clone the DoWhy wrapper and refit it on modified data. For
external estimators, this can be expensive and may have estimator-specific
randomness. Use bounded refuter settings first:

```python
result = model.refute_estimate(
    estimand,
    estimate,
    method_name="data_subset_refuter",
    subset_fraction=0.8,
    num_simulations=10,
    random_state=7,
    n_jobs=1,
)
```

Then increase `num_simulations` and `n_jobs` only if the estimator runtime and
memory use are acceptable.

## What not to do

- Do not use `backdoor.econml...` when the causal graph only identifies an IV
  estimand and no backdoor/general adjustment set.
- Do not omit `effect_modifiers` and then present `cate_estimates` as meaningful
  heterogeneity.
- Do not use `fit_estimator=False` with a different method-name string or a
  different effect-modifier schema.
- Do not route GCM CATE/ACE requests here when the user is already working with
  `dowhy.gcm`; use `graphical-causal-models`.
