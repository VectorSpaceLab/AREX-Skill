# Metrics and validation

This reference covers causalml 0.17.0 APIs for scoring fitted treatment-effect predictions, validating CATE estimates, and plotting prioritization curves.

## Core input orientation

Most metrics accept a `pandas.DataFrame` with reserved columns plus one or more model prediction columns.

- Reserved defaults: `outcome_col="y"`, `treatment_col="w"`, `treatment_effect_col="tau"`.
- All non-reserved columns are treated as model prediction columns and scored independently.
- Prediction columns are sorted in descending order. Larger predicted uplift/CATE means higher treatment priority. If a model emits a lower-is-better risk score, multiply by `-1` or transform it before scoring.
- Do not include feature columns in the scoring frame unless they are intentional prediction columns.
- Avoid nulls in the reserved columns used by the selected metric; the curve helpers assert non-null required inputs.

Treatment coding for metric functions is binary: use `1` for treated and `0` for control. For string labels, create a metric column such as:

```python
df["w"] = (df["treatment_group_key"] != "control").astype(int)
```

For multi-treatment uplift, score one treatment-vs-control contrast at a time, or use one prediction column per treatment contrast with a binary treatment indicator for that contrast.

## Uplift, gain, Qini, AUUC, and plotting

Imports:

```python
from causalml.metrics import (
    get_cumlift, get_cumgain, get_qini,
    plot_lift, plot_gain, plot_qini, plot,
    auuc_score, qini_score,
)
```

### Data cases

1. **Known treatment effects** from simulations or validated pseudo-outcomes:
   - Supply `tau` (or pass `treatment_effect_col="your_tau_col"`).
   - For Qini functions, also keep a binary treatment column because the current Qini implementation uses cumulative treated counts.
2. **Observed outcomes from randomized experiments**:
   - Supply `y` and binary `w`.
   - Curve values are difference-in-means estimates within prioritized subsets.
3. **Observational data**:
   - Naive observed-outcome curves can be confounded within ranked subsets.
   - Prefer cross-fitted pseudo-outcomes from `compute_dr_pseudo_outcomes(...)` and pass them as `treatment_effect_col` when using ranking curves or RATE.

### Main functions

| Function | Purpose | Return |
| --- | --- | --- |
| `get_cumlift(df, ...)` | Average uplift among cumulative top-ranked population | DataFrame indexed by population count |
| `get_cumgain(df, normalize=False, ...)` | Cumulative gain = cumulative lift times population count | DataFrame |
| `get_qini(df, normalize=False, ...)` | Qini curve against treatment/control outcomes or true effect | DataFrame |
| `plot_lift`, `plot_gain`, `plot_qini` | Matplotlib curve plotting | Axes or plotted figure depending on helper |
| `plot(df, kind="lift"|"gain"|"qini", tmle=False, ...)` | Generic plotting dispatcher | `matplotlib.axes.Axes` |
| `auuc_score(df, normalize=True, return_ci=False, ...)` | Area under uplift/gain curve | Series, or DataFrame with interval columns |
| `qini_score(df, normalize=True, return_ci=False, ...)` | Area between Qini model curve and random baseline | Series, or DataFrame with interval and `p_value` |

Bootstrap interval options for `auuc_score` and `qini_score` are `return_ci=True`, `n_bootstrap`, `alpha`, and `random_state`. `n_bootstrap` must be at least 2 and `0 < alpha < 1`.

`qini_score(..., return_ci=True)` reports a two-sided p-value against the random-ranking null. `auuc_score(..., return_ci=True)` reports interval columns but no p-value because AUUC is not centered at a zero random baseline.

## TOC and RATE

Imports:

```python
from causalml.metrics.rate import get_toc, rate_score, plot_toc
```

`get_toc(df, ...)` computes the Targeting Operator Characteristic: the excess ATE in the top-`q` fraction ranked by a model compared with the overall ATE. The index is quantile `q`; by definition TOC starts and ends at zero.

`rate_score(df, weighting="autoc"|"qini", normalize=False, return_ci=False, ...)` summarizes TOC with RATE:

- `weighting="autoc"` emphasizes the highest-priority units.
- `weighting="qini"` gives Qini-style weighting across the population.
- `return_ci=True` adds standard error, confidence interval, and p-value columns using half-sample bootstrap.
- `normalize=True` divides by maximum absolute TOC, not TOC at `q=1`, to avoid division by zero.

`plot_toc(df, n=100, ax=None, ...)` returns a Matplotlib `Axes` and draws a zero random baseline.

## CATE model-selection losses

Imports:

```python
from causalml.metrics.cate_scoring import (
    compute_dr_pseudo_outcomes,
    dr_score,
    plug_in_t_score,
    rlearner_score,
)
```

These score effect-magnitude accuracy rather than ranking quality. Lower is better for all three losses.

### Doubly robust pseudo-outcomes and DR loss

```python
phi = compute_dr_pseudo_outcomes(
    X=X,
    treatment=df["w"],
    y=df["y"],
    p=propensity_scores,              # optional
    learner=outcome_model,            # or separate control/treatment learners
    n_folds=5,
    p_clip_bounds=(0.02, 0.98),
    random_state=42,
)
score_df = pd.DataFrame({"model_a": tau_a, "model_b": tau_b, "phi": phi})
dr = dr_score(score_df, pseudo_outcome_col="phi")
```

If `pseudo_outcome_col` is not supplied, `dr_score` requires `X`, `treatment_col`, `outcome_col`, and either `learner` or both `control_outcome_learner` and `treatment_outcome_learner`. Supplying pseudo-outcomes is faster and makes repeated model comparisons deterministic.

### Plug-in T loss

`plug_in_t_score(df, X, learner=..., n_folds=5, ...)` cross-fits treatment and control outcome models and scores each prediction column against `mu_1(X) - mu_0(X)`. It is useful as a simple companion to DR loss but is not doubly robust.

### R-loss

`rlearner_score(df, ...)` uses residualized outcomes and treatments:

- Provide `y_residual_col` and `w_residual_col` to reuse precomputed residuals, or
- Provide `X`, `outcome_learner`, `treatment_col`, and `outcome_col` so residuals can be computed internally.

The returned score is the mean squared R-loss per model column, optionally with bootstrap interval columns.

## TMLE-based validation curves

Imports:

```python
from causalml.metrics import get_tmlegain, get_tmleqini, plot_tmlegain, plot_tmleqini
```

Use these when skewed treatment assignment or outliers make segment-level ATE estimates unstable. The helpers use `TMLELearner.estimate_ate` internally. In causalml 0.17.0, `TMLELearner` exposes `estimate_ate`; do not expect a `fit_predict` method.

Required columns:

- outcome column such as `y`
- binary treatment column such as `w`
- propensity column such as `p`
- inference feature columns listed in `inference_col`
- one or more model prediction columns to segment and score

`get_tmlegain(..., ci=True)` and `get_tmleqini(..., ci=True)` can return lower/upper confidence columns. `auuc_score(..., tmle=True, return_ci=True)` and `qini_score(..., tmle=True, return_ci=True)` are intentionally unsupported because each bootstrap draw would refit TMLE.

## Propensity balance diagnostics

Imports:

```python
from causalml.metrics.visualize import plot_ps_diagnostics, get_std_diffs, get_simple_iptw
```

- `plot_ps_diagnostics(df, covariate_col, treatment_col="w", p_col="p", bal_tol=0.1)` plots pre/post standardized differences after inverse probability weighting.
- `get_std_diffs(X, W, weight=None, weighted=False, numeric_threshold=5)` accepts continuous and binary numeric covariates. Variables with too few unique values or categorical dtype may be dropped.
- `get_simple_iptw(W, propensity_score)` returns binary-treatment IPTW weights `W / p + (1 - W) / (1 - p)`.

## Synthetic benchmark helpers

Imports:

```python
from causalml.dataset import (
    get_synthetic_preds,
    get_synthetic_summary,
    get_synthetic_preds_holdout,
    get_synthetic_summary_holdout,
    get_synthetic_auuc,
)
```

- `get_synthetic_preds(synthetic_data_func, n=1000, estimators={})` fits/evaluates a standard set of learners on generated data.
- `get_synthetic_summary(synthetic_data_func, n=1000, k=1, estimators={})` repeats simulations and summarizes learner metrics.
- Holdout variants split training and validation predictions with `valid_size`.
- `get_synthetic_auuc(synthetic_preds, drop_learners=[], outcome_col="y", treatment_col="w", treatment_effect_col="tau", plot=True)` summarizes AUUC from synthetic prediction dictionaries.

Use these helpers for fast sanity checks and model-comparison examples, not as evidence for a real dataset unless the synthetic mechanism matches the application assumptions.
