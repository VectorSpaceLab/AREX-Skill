# PyFlux GAS troubleshooting

## Symptom: `No latent variables estimated!`

**Likely cause**: `predict`, `predict_is`, plotting, or posterior predictive methods were called before `fit()`.

**Fix**:

1. Fit the model first with `model.fit("MLE")` or the method you need.
2. Re-run the forecast or plot.

---

## Symptom: `KeyError`, Patsy lookup failure, or missing-column error in `GASX` / `GASReg`

**Likely cause**: `oos_data` does not contain every column referenced by the formula, or the column names changed between fit and forecast.

**Fix**:

- Keep the response placeholder and all exogenous columns in the out-of-sample DataFrame.
- Use the exact same formula terms at fit and forecast time.
- If you renamed a column, rename it back before calling `predict`.

---

## Symptom: `GASRank` fit fails on local data or prediction lookup fails for a team

**Likely cause**: the training DataFrame does not contain the exact `team_1`, `team_2`, or `score_diff` column names, or a predicted team name was never seen during fitting.

**Fix**:

- Rename the local DataFrame columns so they exactly match the constructor arguments.
- Include all teams you want to predict in the training fixture.
- For second-component ranking, include all second-component labels in the same training DataFrame before calling `add_second_component(...)`.

---

## Symptom: `GASRank` still points at the old remote CSV workflow

**Likely cause**: a notebook or legacy test was copied from the original online example.

**Fix**:

- Replace the remote download with a local synthetic DataFrame.
- Keep a few teams repeated across multiple games so the ranking path can actually update.
- Use `neutral=True` for a clean offline sanity check.

---

## Symptom: Count or intensity forecasts become negative, `NaN`, or unstable

**Likely cause**: the family does not match the support of the data.

**Fix**:

- Use `Poisson` only for nonnegative counts.
- Use `Exponential` only for positive/nonnegative intensities or durations.
- If the series can go negative, use `Normal`, `t`, `Laplace`, `Skewt`, or `Cauchy` instead.
- Validate `data.min() >= 0` before choosing a count/intensity family.

---

## Symptom: Prediction intervals look odd or are expensive to compute

**Likely cause**: interval estimation is simulation-based, and non-MH intervals do not include full latent-variable uncertainty.

**Fix**:

- Use `intervals=False` for quick smoke checks.
- Use `M-H` only when you need Bayesian predictive uncertainty.
- Expect longer runtimes on larger GASRank or Bayesian fits.

---

## Symptom: `GASRank` second-component forecasts look suspicious

**Likely cause**: the second-component workflow is more fragile than the one-component workflow in this PyFlux release.

**Fix**:

- Always call `add_second_component(...)` before refitting.
- Verify the effect of the second component on a tiny synthetic fixture before trusting the forecast.
- If you only need paired comparison scores, keep the one-component model.

---

## Symptom: `plot_predict` or `predict` returns the wrong horizon length

**Likely cause**: the wrong `h` or `oos_data` length was supplied.

**Fix**:

- Pass at least `h` future rows for `GASX` and `GASReg`.
- For all models, confirm `result.shape[0] == h` before using the forecast downstream.

---

## Symptom: `GASRank` is slow

**Likely cause**: the ranking model is not cythonized in this version.

**Fix**:

- Use a small synthetic fixture for validation.
- Start with `MLE` before trying Bayesian inference.
- Prefer one-component ranking unless you truly need the second component.
