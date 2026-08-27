---
name: causal-estimation
description: "Classical CausalML causal estimators covering meta-learners, TMLE,
  IV/DRIV, serialization, and estimator API contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# causal-estimation

Use this sub-skill for classical causal effect estimation with CausalML 0.17.0:
S/T/X/R/DR meta-learners, TMLE ATE estimation, instrumental-variable estimators,
propensity-score contracts, argument-order migration, DataFrame/Polars handling,
and joblib-backed learner serialization.

## Route by question type

- **Meta-learners and CATE/ATE**: use [references/meta-learners.md](references/meta-learners.md).
  This includes `BaseSRegressor`, `BaseSClassifier`, `BaseTRegressor`,
  `BaseTClassifier`, `BaseXRegressor`, `BaseXClassifier`, `BaseRRegressor`,
  `BaseRClassifier`, `BaseDRRegressor`, `BaseDRClassifier`, `LRSRegressor`,
  `XGBTRegressor`, `XGBTClassifier`, `MLPTRegressor`, `XGBRRegressor`,
  `XGBRClassifier`, and `XGBDRRegressor`.
- **TMLE, IV, DRIV, and persistence**: use
  [references/iv-tmle-serialization.md](references/iv-tmle-serialization.md).
  The current IV entry point is `IVRegressor`; the current DRIV entry points are
  `BaseDRIVLearner`, `BaseDRIVRegressor`, and `XGBDRIVRegressor`.
- **Input contracts and migration details**: use
  [references/api-contracts.md](references/api-contracts.md) before writing code
  that passes `treatment`, `y`, `p`, `assignment`, `w`, or `pZ`.
- **Error diagnosis**: use [references/troubleshooting.md](references/troubleshooting.md).

## Cross-route to sibling sub-skills

- Use [../tree-models/](../tree-models/) for `CausalTreeRegressor`,
  `CausalRandomForestRegressor`, `UpliftTreeClassifier`,
  `UpliftRandomForestClassifier`, tree fill/prune, and tree visualization.
- Use [../deep-models/](../deep-models/) for TensorFlow, Torch/Pyro, or JAX
  neural estimators such as DragonNet and CEVAE.
- Use [../analysis-and-decision/](../analysis-and-decision/) for AUUC/Qini/gain
  curves, validation scoring, sensitivity analysis, feature selection, policy
  learning, and counterfactual value optimization.
- Use [../data-preparation/](../data-preparation/) for synthetic data,
  propensity-model construction, matching, feature utilities, and matched-data QA.

## Always apply these defaults

1. Prefer keyword arguments for all public estimator calls:
   `fit(X=X, treatment=treatment, y=y, ...)`, not positional
   `fit(X, treatment, y, ...)`.
2. Check `control_name` and treatment labels before fitting. Output columns are
   ordered as `learner.t_groups`, which is the sorted set of non-control
   treatment groups.
3. Treat `p` as a strict probability contract: values must be inside `(0, 1)`,
   arrays/Series are only for a single non-control group, and multi-treatment
   runs need dictionaries keyed by treatment group.
4. Use `fit_predict` only on learners that expose it. `TMLELearner` exposes
   `estimate_ate` but not `fit_predict`; `IVRegressor` exposes `fit` and
   `predict`; DRIV learners expose both `fit_predict` and `estimate_ate`.
5. Keep persistence on fitted learners: `learner.save(path)`,
   `ClassName.load(path)`, or generic `load_learner(path)`. Do not assume
   `save_model` or `load_model` functions exist for these classical estimators.
