---
name: statistical-tests-and-diagnostics
description: "Use statsmodels statistical tests, diagnostics, ANOVA, contrasts,
  influence, multiple testing, contingency tables, power, effect-size,
  mediation, treatment, and meta-analysis utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Statistical tests and diagnostics

Use this sub-skill when the task is selecting or running statistical tests, model diagnostics, ANOVA/contrasts, residual checks, influence/outlier analysis, contingency tables, multiple comparisons, power/effect size, mediation, treatment-effect utilities, or meta-analysis.

## Workflow

1. Identify the design: one sample, two sample, paired/grouped, regression residuals, categorical table, time-series residuals, multiple hypotheses, or power calculation.
2. Check assumptions and input shapes before selecting a test: independence, normality, equal variance, stationarity, group sizes, missing data, and fitted result class.
3. Run the focused function and preserve the statistic, p-value, degrees of freedom, correction method, and null/alternative interpretation.
4. Route model fitting back to the owning model sub-skill if the user has not yet fit the model.

## Read or run

- Read [references/api-reference.md](references/api-reference.md) for major modules and functions.
- Read [references/workflows.md](references/workflows.md) for residual diagnostics, ANOVA/contrasts, multiple testing, contingency tables, and power recipes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for test selection, missing assumptions, singular designs, and multiple-testing interpretation.
- Run [scripts/smoke_stats_diagnostics.py](scripts/smoke_stats_diagnostics.py) for a tiny OLS diagnostics and multiple-testing smoke check.

## Cross-routes

- Use [linear-and-formula-models](../linear-and-formula-models/SKILL.md) or [discrete-and-count-models](../discrete-and-count-models/SKILL.md) to fit the model before diagnostics.
- Use [time-series-analysis](../time-series-analysis/SKILL.md) when the diagnostic is a time-series model choice or forecasting problem.
- Use [datasets-results-graphics](../datasets-results-graphics/SKILL.md) for diagnostic plots and table export.
