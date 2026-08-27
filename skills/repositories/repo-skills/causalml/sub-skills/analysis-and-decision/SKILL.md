---
name: analysis-and-decision
description: "Score, validate, interpret, and optimize causalml treatment-effect
  outputs for uplift analysis and treatment decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# causalml analysis and decision router

Use this sub-skill when the task is about evaluating or acting on treatment-effect estimates rather than fitting the primary estimator.

## Route here for

- Uplift/CATE ranking metrics: AUUC, Qini, cumulative lift/gain/Qini curves, TOC/RATE, bootstrap intervals, and plotting. See [metrics-and-validation](references/metrics-and-validation.md).
- CATE validation losses and validation summaries: doubly robust pseudo-outcome loss, plug-in T loss, R-loss, TMLE-based segment gain/Qini, and propensity balance diagnostics. See [metrics-and-validation](references/metrics-and-validation.md).
- Sensitivity and robustness checks: placebo treatment, random cause, subset data, random replace, selection bias, marginal sensitivity model bounds, and confounding-function summaries. See [sensitivity-and-selection](references/sensitivity-and-selection.md).
- Feature selection and interpretation: `FilterSelect`, meta-learner importances, SHAP summaries/dependence plots, and tree/importances interpretation handoff. See [sensitivity-and-selection](references/sensitivity-and-selection.md).
- Treatment decision optimization: `PolicyLearner`, `CounterfactualUnitSelector`, `CounterfactualValueEstimator`, cost/value utilities, uplift-best recommendations, and probability-of-causation bounds. See [optimization](references/optimization.md).

## Before using an API

1. Identify the data orientation: outcome column, treatment column, propensity column if any, true treatment-effect column if available, and one or more model prediction columns.
2. Confirm treatment coding. Most metric and policy APIs assume binary `0`/`1` treatment with `1` as treated and `0` as control; string-labeled or multi-arm data usually needs explicit one-vs-control conversion or APIs with `control_name`/`treatment_names` contracts.
3. Decide whether the task is about effect magnitude accuracy or targeting quality:
   - Use DR/T/R losses for CATE magnitude accuracy.
   - Use AUUC/Qini/TOC/RATE for ranking or treatment prioritization.
   - Use value/policy APIs when decisions have costs, benefits, or allowable treatment assignments.
4. If the request requires fitting causal estimators first, route to the estimation, tree, or deep-model sub-skill, then return here for scoring, interpretation, or optimization.

## Related sub-skills

- Classical meta-learners, IV/DRIV, TMLE API limits, and serialization: `../causal-estimation/SKILL.md`.
- Uplift tree fitting, pruning/fill/save/load, visualization primitives, and tree-specific import issues: `../tree-models/SKILL.md`.
- Neural DragonNet/CEVAE backend setup and fit/predict workflows: `../deep-models/SKILL.md`.
- Synthetic data, matching, propensity models, and data-contract preparation: `../data-preparation/SKILL.md`.

## Troubleshooting first stop

For wrong treatment labels, reversed prediction orientation, missing model columns, feature-selection method constraints, optimization shape/order issues, stale API names, or optional plotting/SHAP dependency errors, start with [troubleshooting](references/troubleshooting.md).
