---
name: tslearn
description: "Routes tslearn users to data preparation, metrics/backends,
  clustering, supervised models, forecasting, and analysis/persistence
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# tslearn

Use this skill for the tslearn time-series machine-learning toolkit.

Start here when the task names `tslearn`, a tslearn example, a tslearn doc page, a tslearn error message, or a tslearn class/function such as `TimeSeriesKMeans`, `dtw`, `LearningShapelets`, `VARIMA`, or `MatrixProfile`.

## Install and quick check

Public install:

```bash
python -m pip install tslearn
```

If you are working from a checkout and want an editable install instead:

```bash
python -m pip install -e .
```

Optional workflows may need extra packages:

- `pandas` for sktime / pyflux / tsfresh conversions
- `stumpy` for MatrixProfile `stump`
- `h5py` for HDF5 round-trips
- `torch` for the PyTorch metric backend and shapelet backend setup
- `keras` for `LearningShapelets`

Minimal import check:

```bash
python -c "import tslearn; print(tslearn.__version__)"
```

For a tiny environment check that also probes common optional packages, run:

```bash
python scripts/check_tslearn_env.py
```

## Route map

| If the user wants... | Go here |
| --- | --- |
| Load, shape, clean, resample, synchronize, symbolize, or convert time-series data | `sub-skills/data-preparation/SKILL.md` |
| DTW / Soft-DTW / GAK / LCSS / Fréchet / CTW, PyTorch backend choice, performance metrics, or barycenters | `sub-skills/metrics-backends/SKILL.md` |
| Cluster time series or score a clustering result | `sub-skills/clustering/SKILL.md` |
| Fit a k-NN, SVM, early-classification, shapelet, or time-series MLP model | `sub-skills/supervised-models/SKILL.md` |
| Fit or debug VARIMA / AutoVARIMA forecasting | `sub-skills/forecasting/SKILL.md` |
| Compute MatrixProfile or round-trip fitted estimators through JSON / Pickle / HDF5 | `sub-skills/analysis-and-persistence/SKILL.md` |

## What this skill owns

tslearn uses dense time-series arrays shaped `(n_ts, sz, d)` and allows variable-length datasets by padding shorter series with trailing `NaN`s. The package spans:

- data utilities and interoperability helpers
- distance metrics and differentiable time-series losses
- barycenters and scoring helpers
- clustering estimators
- supervised models
- forecasting
- matrix profile
- fitted-estimator persistence

The module map and common optional dependencies live in `references/overview.md`.

## When to read the root references

- `references/overview.md` — module ownership map and common dependency picture.
- `references/troubleshooting.md` — cross-cutting install/import/shape/backend/download/persistence failures.
- `references/repo-provenance.md` — check whether the skill still matches the current checkout.
- `references/repo-routing-metadata.json` — router metadata used during import/update.

## Root-level guidance

1. If the request is broad or ambiguous, read `references/overview.md` first.
2. If the task crosses multiple workflow families, start with the most upstream sub-skill, then hand off downstream.
3. Prefer the bundled smoke helper only for a tiny environment sanity check.
4. Keep plotting gallery examples out of the runtime path; use the bundled smoke scripts instead.
5. Do not assume CUDA, stumpy, pandas, h5py, Keras, or torch are installed unless the task needs them.

## Common handoffs

- Data shaping before modeling → `data-preparation`
- Metric choice before clustering or supervised modeling → `metrics-backends`
- Clustering after scaling / metric choice → `clustering`
- Supervised fitting after preprocessing and metric choice → `supervised-models`
- Forecasting after shaping the series → `forecasting`
- Analysis / persistence after fitting a model → `analysis-and-persistence`

## Refresh check

Before using this skill on a different checkout, compare that checkout with `references/repo-provenance.md`. If the commit, branch, dirty state, package version, or evidence roots changed, refresh the skill instead of assuming it is current.
