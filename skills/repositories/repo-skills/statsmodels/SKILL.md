---
name: statsmodels
description: "Use statsmodels for statistical modeling, econometrics,
  time-series analysis, statistical tests, diagnostics, result summaries,
  plotting, and maintainer workflows in the statsmodels Python repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# statsmodels Repo Skill

Use this repo skill when a task asks for `statsmodels`, statistical models in Python, econometrics workflows, formulas with `patsy`, time-series modeling, statistical tests/diagnostics, statsmodels result summaries, or maintainer work in a statsmodels checkout. This skill is self-contained: do not send future users back to the source checkout for docs, examples, tests, scripts, or notebooks.

## Quick orientation

`statsmodels` is a CPU Python package for statistical computations and models. The common public imports are:

```python
import statsmodels.api as sm          # broad interactive API
import statsmodels.formula.api as smf # formula interface for DataFrames
import statsmodels.tsa.api as tsa     # time-series API
```

A minimal public install and import check is:

```bash
python -m pip install statsmodels
python - <<'PY'
import statsmodels, statsmodels.api as sm, statsmodels.formula.api as smf
print(statsmodels.__version__)
print(sm.OLS, sm.GLM, sm.Logit)
PY
```

For source checkouts, build tools are required because the project uses Meson and Cython for compiled extensions. For ordinary package use, prefer released wheels or conda packages rather than building from source.

## Route by task

- [linear-and-formula-models](sub-skills/linear-and-formula-models/SKILL.md): OLS/WLS/GLS/GLSAR, QuantReg, RLM, GLM, GEE, GAM, MixedLM, formulas, design matrices, missing-data handling, robust covariance, prediction, and result summaries.
- [discrete-and-count-models](sub-skills/discrete-and-count-models/SKILL.md): Logit, Probit, MNLogit, OrderedModel, Poisson, NegativeBinomial, GeneralizedPoisson, zero-inflated, hurdle, truncated, conditional models, marginal effects, and separation/convergence recovery.
- [time-series-analysis](sub-skills/time-series-analysis/SKILL.md): `statsmodels.tsa`, stationarity tests, AR/ARDL/ARIMA/SARIMAX, state-space models, VAR/VECM, ETS/Holt-Winters, STL/MSTL, filters, forecasting, dynamic factors, Markov switching, and optional X-13/X-12 integration.
- [statistical-tests-and-diagnostics](sub-skills/statistical-tests-and-diagnostics/SKILL.md): descriptive statistics, hypothesis tests, ANOVA/contrasts, residual diagnostics, influence/outliers, multiple testing, contingency tables, effect size, power, mediation, treatment-effect utilities, and meta-analysis.
- [datasets-results-graphics](sub-skills/datasets-results-graphics/SKILL.md): built-in datasets, result objects, predictions, summaries, robust covariance outputs, save/load, graphics, I/O, `webdoc`, local-vs-network data choices, and plot troubleshooting.
- [development-and-testing](sub-skills/development-and-testing/SKILL.md): source build/editable install, Cython/Meson rebuilds, focused pytest selection, docs/examples maintenance, public API checks, docstring validation, warnings, and contributor safety.

## Shared references and helpers

- Read [references/repo-provenance.md](references/repo-provenance.md) before refreshing this skill or deciding whether it matches a newer checkout.
- Read [references/package-orientation.md](references/package-orientation.md) for import style, data terminology, optional dependencies, backend assumptions, and broad workflow boundaries.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, missing-data, convergence, optional dependency, and source-build failures.
- Run [scripts/check_statsmodels_env.py](scripts/check_statsmodels_env.py) to verify a fresh environment can import core APIs, optional plotting support, and a tiny fitted model without network access.

## Decision points

1. **Formula or matrix API?** Use `statsmodels.formula.api` when data is a `pandas.DataFrame` and the model can be expressed with a formula. Use `statsmodels.api` or direct module imports when arrays are already prepared, when avoiding broad imports in production code, or when the target class lacks a formula wrapper.
2. **Endog/exog terminology.** `endog` is the dependent/response variable. `exog` is the design matrix or regressors. Add a constant explicitly with `sm.add_constant` unless the model or formula interface adds one.
3. **Missing data.** Many models default to `missing='none'`, which may propagate `NaN` results. For unknown data quality, use `missing='raise'` during validation or `missing='drop'` deliberately.
4. **Warnings and convergence.** Treat convergence warnings, perfect separation, rank deficiency, and boundary estimates as modeling diagnostics, not just software errors. Route to the owning model sub-skill plus diagnostics guidance.
5. **Optional dependencies.** Matplotlib is needed for plotting; pytest is for tests; joblib can accelerate distributed estimation; X-13/X-12 requires an external executable. Do not claim optional behavior is available without checking it.
6. **No public CLI.** statsmodels is primarily a Python API package. If a user asks for a CLI command, translate the task into a short Python script or notebook-style snippet.

## Do not

- Do not tell future agents to open original source docs, notebooks, examples, tests, or tools; use the bundled references and scripts in this skill tree.
- Do not leak local inspection environment names, Python paths, build directories, or checkout paths into user-facing responses.
- Do not use `statsmodels.sandbox` as production guidance unless the user explicitly asks about experimental sandbox code and accepts that it is not production-ready.
- Do not treat a successful import as evidence that a statistical model is identified, converged, or appropriate for a dataset.
