---
name: ktr
description: "Fit and inspect KTR/KTRLite models, knots, seasonality, and
  time-varying coefficients."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# KTR and KTRLite

Use this sub-skill when the user asks about KTR or KTRLite fitting, forecasting, knot placement,
time-varying regressors, coefficient inspection, or deciding between the two estimators.

Start here:

- `references/api-reference.md` for verified wrapper signatures, estimator gates, and method names.
- `references/workflows.md` for copyable routing and fit/inspect recipes.
- `references/troubleshooting.md` for import, knot, seasonality, estimator, and frequency failures.
- `references/evidence-map.md` for the source anchors behind this sub-skill.
- `scripts/smoke_ktr_ktrlite.py` for a tiny network-free synthetic fit/predict check.

Operating rules:

1. Use `orbit.models.KTR` when the request needs time-varying regression coefficients, regressor signs,
   coefficient priors, regression knot controls, coefficient-path inspection, or WBIC. KTR is `pyro-svi` only.
2. Use `orbit.models.KTRLite` when the request needs the lighter level/seasonality fit, knot inspection, or
   MAP-only model selection. KTRLite is `stan-map` only.
3. KTR internally fits KTRLite first to recover level and seasonality before the Pyro-SVI regression fit.
   Tune that inner step with `ktrlite_optim_args` when necessary.
4. Keep `seasonality` and `seasonality_fs_order` aligned, and respect the Fourier bound `2 * order < period`
   for every seasonality entry.
5. Prefer explicit `date_freq` for reproducible knot placement and when `pd.infer_freq` may be ambiguous or
   unavailable.
6. Use the bundled knot helpers when turning dates into knot indices or back again; do not hand-count knots.
7. Import through `orbit.models`. Direct `orbit.template.ktr` imports can trigger a circular-import issue.
8. Do not use this sub-skill for ETS, LGT, DLT, generic backtesting, or unrelated utility workflows beyond
   knot helpers.
