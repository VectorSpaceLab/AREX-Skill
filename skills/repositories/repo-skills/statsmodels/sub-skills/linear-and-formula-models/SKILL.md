---
name: linear-and-formula-models
description: "Use statsmodels linear, generalized linear, robust, mixed, GEE,
  GAM, and formula APIs for model fitting, prediction, summaries, missing data,
  robust covariance, and design-matrix troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Linear and formula models

Use this sub-skill for OLS/WLS/GLS/GLSAR, RollingOLS/RollingWLS, QuantReg, RLM, GLM, GEE, GAM, MixedLM, variance components, formula workflows, design matrices, missing-data handling, robust covariance, prediction, and summary interpretation.

## Start here

1. Choose interface:
   - DataFrame plus formula: `import statsmodels.formula.api as smf`; call `smf.ols(...)`, `smf.glm(...)`, `smf.mixedlm(...)`, or `smf.gee(...)`.
   - Prepared arrays: `import statsmodels.api as sm`; add an intercept with `sm.add_constant` when required and call model classes such as `sm.OLS(endog, exog)` or `sm.GLM(endog, exog, family=...)`.
2. Validate data before fitting: shape, missing values, categorical encoding, constant column, rank, and domain restrictions for the chosen family.
3. Fit once, inspect result attributes (`params`, `bse`, `pvalues`, `conf_int()`, `summary()`), and only then add robust covariance, predictions, or diagnostics.
4. For residual diagnostics, ANOVA/contrasts, or outlier influence details, cross-route to [statistical-tests-and-diagnostics](../statistical-tests-and-diagnostics/SKILL.md). For result export and plotting, cross-route to [datasets-results-graphics](../datasets-results-graphics/SKILL.md).

## Read or run

- Read [references/api-reference.md](references/api-reference.md) for constructors, formula wrappers, families, covariance choices, and result methods.
- Read [references/workflows.md](references/workflows.md) for formula and matrix recipes, prediction, robust covariance, mixed models, and GLM/GEE patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing-data, rank, convergence, perfect fit, robust covariance, and formula errors.
- Run [scripts/smoke_linear_models.py](scripts/smoke_linear_models.py) for a deterministic local OLS/GLM/robust-covariance smoke check.

## Boundaries

- Route binary choice, multinomial choice, ordered models, count-model-specific marginal effects, zero-inflated, hurdle, and truncated count workflows to [discrete-and-count-models](../discrete-and-count-models/SKILL.md).
- Route ARIMA/SARIMAX/VAR/forecasting and time-index problems to [time-series-analysis](../time-series-analysis/SKILL.md).
- Route general hypothesis tests, influence/outlier procedures, and multiple testing to [statistical-tests-and-diagnostics](../statistical-tests-and-diagnostics/SKILL.md), but keep model-specific fit setup here.
- Do not recommend `statsmodels.sandbox` implementations for production linear modeling unless the user explicitly asks about sandbox code.

## Quality checks before answering

- State whether the snippet uses formula or matrix API.
- Show how the intercept is handled.
- Mention missing-data policy when inputs may contain `NaN`.
- Keep new prediction data aligned with training columns and categorical levels.
- Explain convergence/rank warnings as statistical identification issues, not only software failures.
