---
name: orbit-ml
description: "Use Orbit's Bayesian time-series models, diagnostics, utilities,
  and custom-model internals for forecasting, backtesting, and
  model-construction tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Orbit-ML

Use this repo skill when the task is about the public `orbit` package, the
`orbit-ml` distribution, or the Orbit time-series workflows built on top of
those APIs.

## Install and verify

Install the package into the active Python environment with one of the public
package routes:

```bash
pip install orbit-ml
# or
conda install -c conda-forge orbit-ml
```

Then run the lightweight install check:

```bash
python scripts/check_install.py
```

Use the subskill smoke scripts for workflow-specific validation after you have
a working environment.

## Route map

- **`forecasting`**: use `ETS`, `LGT`, or `DLT` to fit, forecast, nowcast, add
  regressors, and inspect intervals or decompositions.
- **`ktr`**: use `KTR` or `KTRLite` for multi-seasonality, knot placement,
  time-varying coefficients, and coefficient inspection.
- **`evaluation`**: run `TimeSeriesSplitter`, `BackTester`, forecast metrics,
  plots, residual diagnostics, and model-level WBIC/BIC checks.
- **`utilities`**: load sample data, generate synthetic series, build Fourier or
  seasonal features, compute knots, expand panels, tune grids, or make EDA
  plots.
- **`custom-models`**: inspect `ModelTemplate`, forecasters, estimators, Stan / Pyro
  backend wiring, and build-your-own-model internals.

## Read these first when needed

- `references/model-overview.md` for the short model-family map.
- `references/troubleshooting.md` when install, import, backend, or runtime
  failures appear.
- `references/repo-provenance.md` to check whether this skill matches the
  current checkout before asking for a refresh.

## Quick selection rules

- Start with `forecasting` for ordinary single-series fit/predict tasks.
- Switch to `ktr` when the task mentions multiple seasonalities, knots, or
  time-varying coefficients.
- Switch to `evaluation` when the task is about backtesting or comparing
  forecast quality.
- Switch to `utilities` when the task is about sample data, features, knots,
  simulation, or tuning helpers.
- Switch to `custom-models` when the task asks about the architecture or how to
  extend Orbit with a new model / backend integration.

## Runtime helpers

- `scripts/check_install.py` for the cross-cutting import and backend check.
- `sub-skills/forecasting/scripts/smoke_forecasting.py` for a tiny ETS / LGT
  smoke path.
- `sub-skills/ktr/scripts/smoke_ktr_ktrlite.py` for a tiny KTR / KTRLite smoke
  path.
- `sub-skills/evaluation/scripts/smoke_backtest.py` for a tiny backtest smoke
  path.
- `sub-skills/utilities/scripts/smoke_utilities.py` for a tiny helper-only
  smoke path.
- `sub-skills/custom-models/scripts/inspect_custom_models.py` for the bundled
  architecture snapshot and safe import probes.

## Notes

- This skill is router-like by design; long API tables and recipes live in the
  subskill references.
- Orbit does not expose a public CLI in this package surface; use Python APIs or
  the bundled smoke scripts.
- If the repository changes, compare the current checkout against
  `references/repo-provenance.md` before using the skill as-is.
