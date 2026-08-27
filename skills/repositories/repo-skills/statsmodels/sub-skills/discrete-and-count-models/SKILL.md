---
name: discrete-and-count-models
description: "Use statsmodels discrete choice and count model APIs for Logit,
  Probit, MNLogit, OrderedModel, Poisson, NegativeBinomial, zero-inflated,
  hurdle, truncated, conditional models, marginal effects, and convergence
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Discrete and count models

Use this sub-skill for binary choice, multinomial choice, ordered outcomes, count models, zero-inflated/hurdle/truncated counts, conditional models, marginal effects, post-estimation prediction, and failures such as perfect separation or non-convergence.

## Workflow

1. Identify the outcome type: binary, ordered categorical, unordered multinomial, nonnegative count, overdispersed count, zero-inflated/hurdle, truncated, or grouped conditional.
2. Build `endog` and `exog`, adding a constant for array APIs. Formula wrappers exist for common classes through `statsmodels.formula.api`.
3. Fit the simplest defensible model first; only then add overdispersion, inflation, truncation, or conditional structure.
4. Inspect convergence, parameter magnitudes, predicted probabilities/means, and marginal effects. For broad hypothesis tests or residual diagnostics, cross-route to [statistical-tests-and-diagnostics](../statistical-tests-and-diagnostics/SKILL.md).

## Read or run

- Read [references/api-reference.md](references/api-reference.md) for model classes, signatures, and result surfaces.
- Read [references/workflows.md](references/workflows.md) for binary, multinomial/ordered, and count recipes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for perfect prediction, separation, overdispersion, zero inflation, convergence, and prediction shape issues.
- Run [scripts/smoke_discrete_models.py](scripts/smoke_discrete_models.py) to check binary Logit and Poisson workflows on deterministic local data.

## Boundaries

- Use [linear-and-formula-models](../linear-and-formula-models/SKILL.md) for GLM setup unless the task explicitly needs discrete-model-specific post-estimation, marginal effects, zero inflation, truncation, or choice-model classes.
- Use [time-series-analysis](../time-series-analysis/SKILL.md) for time-indexed discrete models only when the time-series structure is the core request.
- Use [datasets-results-graphics](../datasets-results-graphics/SKILL.md) for result export, tables, or plots after fitting.
