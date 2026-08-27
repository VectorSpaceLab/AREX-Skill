# Causal API Reference

## Purpose

Use this reference to choose the pgmpy causal API and data layout for an effect-estimation task. It distills the role, identification, inference, and prediction surfaces verified for pgmpy 1.1.2. For step-by-step recipes, read [workflows.md](workflows.md); for failure recovery, read [troubleshooting.md](troubleshooting.md).

## Causal Graph Roles

pgmpy graph classes expose roles through `roles={...}`, `with_role(role, variables)`, `get_role(role)`, `get_roles()`, and `get_role_dict()`.

| Role | Used by | Meaning and constraints |
| --- | --- | --- |
| `exposures` | `Adjustment`, `Frontdoor`, prediction regressors | Treatment/intervention variables. Identification needs at least one; most fitted regressors require exactly one. |
| `outcomes` | `Adjustment`, `Frontdoor`, prediction regressors | Outcome/response variables. Identification needs at least one; most fitted regressors require exactly one. |
| `adjustment` | `Adjustment.validate`, `NaiveAdjustmentRegressor`, `DoubleMLRegressor` | Observed covariates used to block backdoor paths. Missing and empty are treated as an empty role by the prediction helpers, but effect claims require a graph-valid set. |
| `frontdoor` | `Frontdoor.validate` | Mediating variables satisfying the frontdoor criterion. Produced by `Frontdoor().identify(...)` when available. |
| `instrument` | `NaiveIVRegressor` | Singular role name expected by the IV regressor. Do not pass only `instruments` when fitting `NaiveIVRegressor`. |
| `pretreatment` | prediction regressors | Optional extra covariates included with adjustment variables or IV second-stage prediction. |
| `latents` | graph classes, `Adjustment`, `Frontdoor`, `CausalInference` | Unobserved variables. Latent parents can block default `CausalInference.query` adjustment and can make effects non-identifiable. |

`SimpleCausalModel` is convenient for diagrams with exposures, outcomes, confounders, mediators, and instruments, but it assigns plural `instruments`. If the next step is `NaiveIVRegressor`, either build a `DAG` with `roles={"instrument": ...}` or add a separate singular `instrument` role to the instrument nodes.

## Graph and Identification Classes

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `DAG(ebunch=None, latents=None, exposures=None, outcomes=None, roles=None)` | constructor | Directed causal graph with role annotations. | Variable names can be strings or other hashables, but `CausalInference` rejects non-string variable names. |
| `SimpleCausalModel(exposures, outcomes, confounders=None, mediators=None, instruments=None, latents=None)` | constructor | Quickly builds a simple causal diagram. | Instruments are stored under `instruments`, not the singular `instrument` role used by `NaiveIVRegressor`. |
| `Adjustment(variant="minimal")` | `identify(causal_graph)`, `validate(causal_graph)` | Backdoor adjustment identification and validation. | `minimal` and `all` are implemented; `minimal_variance` is not implemented. `minimal` is for single exposure and single outcome. |
| `Frontdoor(variant=None)` | `identify(causal_graph)`, `validate(causal_graph)` | Frontdoor identification for a DAG. | `variant=None` returns the first valid graph; `variant="all"` returns all valid frontdoor graphs. |

`BaseIdentification.identify` returns `(identified_graph, success)`. Check `success` before using new roles. `BaseIdentification.validate` returns a boolean for roles already assigned on the graph.

## `CausalInference`

`CausalInference(model)` accepts DAG-like causal graphs and fitted Bayesian-network-style models. Important methods:

| Method | When to use | Key requirements |
| --- | --- | --- |
| `query(variables, do=None, evidence=None, adjustment_set=None, inference_algo="ve", show_progress=True, **kwargs)` | Compute discrete interventional distributions such as `P(Y | do(X=x), Z=z)` from a fitted model with CPDs. | `variables` must be list-like, `do` and `evidence` must be dictionaries, and state values must match the model's CPD state names. `inference_algo` can be `"ve"`, `"bp"`, or an inference instance. |
| `estimate_ate(X, Y, data, estimand_strategy="smallest", estimator_type="linear", **kwargs)` | Estimate an average treatment effect from data using graph-derived adjustment sets. | Current public estimator type is `"linear"`. Data must contain the variables needed for the path and adjustment sets. |
| `get_minimal_adjustment_set(X, Y)` | Inspect a minimal adjustment set from the graph. | Returns a set or `None`; useful for diagnostics. |
| `is_valid_adjustment_set(X, Y, adjustment_set)` | Validate a proposed adjustment set for a query. | Accepts strings/lists for `X` and `Y`; validate before relying on user-supplied sets. |

Avoid older `get_all_backdoor_adjustment_sets`, `is_valid_backdoor_adjustment_set`, and frontdoor helper methods for new guidance when `Adjustment`/`Frontdoor` can express the task; those legacy helpers warn about future removal.

## Prediction Regressors

All `pgmpy.prediction` regressors follow sklearn-style `fit`, `predict`, and `score` patterns and read variables from graph roles.

| Regressor | Signature | Required roles | Feature `X` columns | Default estimators |
| --- | --- | --- | --- | --- |
| `NaiveAdjustmentRegressor(causal_graph, estimator=None)` | adjustment/prediction baseline | Exactly one `exposures`, exactly one `outcomes`; optional `adjustment`, optional `pretreatment` | exposure + adjustment + pretreatment columns | `LinearRegression()` |
| `DoubleMLRegressor(causal_graph, nuisance_estimators=None, effect_estimator=None, n_folds=5, seed=None)` | cross-fitted partial-linear DML | Exactly one `exposures`, exactly one `outcomes`; adjustment/pretreatment used as covariates | exposure + adjustment + pretreatment columns | `LinearRegression()` for treatment, outcome, and effect models |
| `NaiveIVRegressor(causal_graph, stage1_estimator=None, stage2_estimator=None)` | simple two-stage IV workflow | Exactly one `exposures`, exactly one `outcomes`, at least one singular `instrument`; optional `pretreatment` | fit: exposure + instruments + pretreatment; predict: exposure + pretreatment | `LinearRegression()` for both stages |

Data expectations:

- Pass a pandas `DataFrame` when graph variables are named strings; column names must exactly match graph role variables.
- Extra columns may be present, but required role columns must exist and be numeric.
- If using a NumPy array, pgmpy converts columns to integer names `0, 1, ...`; the DAG roles must use those integer variables.
- These regressors are code-level estimators, not automatic causal validators. Validate the graph and role choices first.
