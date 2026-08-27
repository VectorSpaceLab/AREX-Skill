---
name: ml-decoding-connectivity
description: "Use Nilearn supervised decoding, searchlight, SpaceNet/FREM,
  connectivity, decomposition, parcellation handoffs, and mass-univariate
  permutation workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# ML Decoding and Connectivity

Use this sub-skill when a Nilearn task involves machine-learning models over
brain images or extracted signals: supervised decoding/regression, searchlight
maps, sparse/structured decoders, connectome features, decomposition maps,
parcellation-to-connectome handoffs, or mass-univariate permutation tests.

## Start Here

1. Identify whether the inputs are images, maskers, extracted time series, or
   precomputed feature matrices.
2. Route mask choice and signal extraction details to `maskers-regions`; route
   image cleaning/resampling to `data-io-signal`; route dataset/cache setup to
   `datasets-interfaces`; route final matrix/connectome plots to
   `plotting-reporting`.
3. Use [references/api-reference.md](references/api-reference.md) to choose the
   Nilearn estimator/function and verify expected shapes.
4. Use [references/workflows.md](references/workflows.md) for leakage-safe
   recipes and handoffs between maskers, connectomes, decoders, and statistics.
5. Use [references/troubleshooting.md](references/troubleshooting.md) before
   changing masks, CV objects, `n_jobs`, or expensive structured estimators.

## Route by Task

- **Supervised image decoding**: use `Decoder` or `DecoderRegressor` for
  image-like samples with automatic masking, screening, CV, and model maps.
- **Local information maps**: use `SearchLight` when the question is spatially
  local; keep `radius`, `process_mask_img`, CV, and `n_jobs` intentionally small
  while prototyping.
- **Structured sparse models**: use `SpaceNetClassifier`,
  `SpaceNetRegressor`, `FREMClassifier`, or `FREMRegressor` only when spatial
  regularization, clustering, or ensembling is part of the analysis goal.
- **Connectome features**: use `ConnectivityMeasure` on one 2D time-series
  array per subject, then feed vectorized outputs to scikit-learn pipelines.
- **Group covariance structure**: use `GroupSparseCovariance` or
  `GroupSparseCovarianceCV` for shared sparse precision patterns across
  subjects; expect cubic scaling in the number of regions/features.
- **Unsupervised maps/parcels**: use `CanICA`, `DictLearning`, or
  `Parcellations` to learn components/parcels before extracting region signals
  and building connectomes.
- **Voxelwise association tests**: use `permuted_ols` for massively univariate
  OLS with permutation-based family-wise control; keep `n_perm` low for smoke
  checks and high only for final inference.

## Bundled Smoke Check

Run the no-network smoke script to check a local Nilearn environment and shape
contracts without downloading data:

```bash
python scripts/smoke_ml_connectivity.py --help
python scripts/smoke_ml_connectivity.py
```

The script builds tiny synthetic subject time series, computes vectorized
tangent and correlation connectomes, trains a light classifier, and optionally
checks a small `Decoder` path when nibabel image support is available.
