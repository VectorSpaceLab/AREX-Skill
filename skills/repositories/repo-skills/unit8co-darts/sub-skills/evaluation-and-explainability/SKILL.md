---
name: evaluation-and-explainability
description: "Use Darts deterministic/probabilistic metrics, reductions,
  anomaly/classification evaluation, and SHAP explainability safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and explainability

Use this sub-skill when the user needs Darts metrics, deterministic vs stochastic forecast evaluation, reduction/aggregation behavior, anomaly/classification metrics, SHAP explainability, or headless plotting safety.

## Read first

- [`references/workflows.md`](references/workflows.md) for deterministic metrics, probabilistic quantile/interval metrics, reductions, and SHAP setup.
- [`references/api-reference.md`](references/api-reference.md) for metric families, `q` vs `q_interval`, and output-shape controls.
- [`references/troubleshooting.md`](references/troubleshooting.md) for metric shape, stochastic sample, SHAP background, unsupported model, and plotting failures.
- [`scripts/evaluation_smoke.py`](scripts/evaluation_smoke.py) for a tiny metrics and optional SHAP-signature smoke.

## Route by task

- **Point forecast metrics**: use deterministic metrics such as `mae`, `rmse`, `mape`, or `r2_score` on actual and deterministic forecast series.
- **Stochastic forecast metrics**: use quantile or interval metrics on forecasts with samples; distinguish `q` from `q_interval`.
- **Keep per-component output**: set reductions deliberately instead of accepting default scalar reductions.
- **Evaluate anomaly outputs**: use continuous-score metrics for scores and binary/classification metrics for detector flags.
- **Explain a fitted model**: use Darts explainers such as `ShapExplainer` only for supported, fitted models with bounded background/foreground data.
- **Need model training first**: route to forecasting, torch, or anomaly sub-skills.

## Safe check

```bash
python scripts/evaluation_smoke.py --check-shap
```

The smoke uses generated data, finite metric assertions, and a SHAP import/signature check. It does not open plots or notebooks.

## Boundaries

This sub-skill evaluates and explains outputs; it does not choose/fit the forecasting model or build covariates. Avoid unconditional plotting in headless environments. Do not use source-repo notebooks as runtime dependencies.
