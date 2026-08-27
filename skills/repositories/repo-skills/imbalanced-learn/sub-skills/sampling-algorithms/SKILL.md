---
name: sampling-algorithms
description: "Router for imbalanced-learn over-sampling, under-sampling, combine
  samplers, and custom resampling primitives."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# sampling-algorithms

Use this sub-skill when the task is about choosing, configuring, or debugging
an imbalanced-learn sampler.

This sub-skill owns the package families that directly change class counts or
sample composition:

- over-sampling: `RandomOverSampler`, `ADASYN`, `SMOTE`, `SMOTENC`, `SMOTEN`,
  `BorderlineSMOTE`, `KMeansSMOTE`, `SVMSMOTE`
- under-sampling: `RandomUnderSampler`, `TomekLinks`, `EditedNearestNeighbours`,
  `RepeatedEditedNearestNeighbours`, `AllKNN`, `OneSidedSelection`,
  `CondensedNearestNeighbour`, `NeighbourhoodCleaningRule`, `NearMiss`,
  `ClusterCentroids`, `InstanceHardnessThreshold`
- combine samplers: `SMOTEENN`, `SMOTETomek`
- custom resampling: `FunctionSampler`

## What to do first

1. Decide whether the request is about increasing minority support, reducing
   majority support, cleaning borderline samples, or writing a custom sampler.
2. Identify the input shape: dense NumPy array, sparse matrix, pandas DataFrame,
   mixed object array, or all-categorical data.
3. Check whether the workflow needs categorical handling, neighbor-based
   synthesis, or a simple bootstrap-style resampler.
4. Fit only on the training branch; do not resample the full dataset before a
   split.
5. Verify the result with a tiny count check before moving on.

## Typical routing cues

- `sampling_strategy`
- `fit_resample`
- `random_state`, `replacement`, `shrinkage`
- `k_neighbors`, `m_neighbors`, `n_neighbors`
- `SMOTE`, `ADASYN`, `NearMiss`, `TomekLinks`, `SMOTEENN`
- `FunctionSampler`
- pandas or sparse input support during resampling
- categorical features or all-categorical samples

## When to read the bundled references

- `references/workflows.md` for the decision tree from task shape to sampler
  family.
- `references/api-reference.md` for the compact public sampler catalog and key
  signatures.
- `references/troubleshooting.md` when neighbor counts, dtype errors, sparse
  output, or categorical feature handling fail.

## Common choices

- Use `RandomOverSampler` when the request is about a simple, duplicate-based
  bootstrap.
- Use `SMOTE` or one of its variants when the request needs synthetic minority
  samples.
- Use `SMOTENC` for mixed numeric/categorical features.
- Use `SMOTEN` when all features are categorical.
- Use `RandomUnderSampler` when the request needs a fast majority reduction.
- Use `TomekLinks`, `EditedNearestNeighbours`, `RepeatedEditedNearestNeighbours`,
  `AllKNN`, or `NeighbourhoodCleaningRule` when the request is about cleaning
  noisy or borderline observations.
- Use `ClusterCentroids` when the task wants prototype generation rather than
  simply selecting existing samples.
- Use `SMOTEENN` or `SMOTETomek` when the task wants a packaged over/under
  combination.
- Use `FunctionSampler` when the user already knows the exact custom logic and
  only needs a thin sampler wrapper.

## Native evidence to keep in mind

These repo tests are the most relevant later verification anchors for this
sub-skill:

- `imblearn/over_sampling/tests/test_random_over_sampler.py::test_ros_fit_resample`
- `imblearn/over_sampling/_smote/tests/test_smote.py::test_sample_regular`
- `imblearn/over_sampling/_smote/tests/test_smote_nc.py::test_smotenc_pandas`
- `imblearn/under_sampling/_prototype_selection/tests/test_random_under_sampler.py::test_rus_fit_resample`
- `imblearn/under_sampling/_prototype_selection/tests/test_tomek_links.py::test_tl_fit_resample`
- `imblearn/combine/tests/test_smote_enn.py::test_sample_regular`
- `imblearn/tests/test_base.py::test_function_sampler_func`

## Package-specific cautions

- `SMOTE`-family methods need a sensible neighbor configuration and enough
  minority samples.
- `SMOTENC` needs a categorical feature specification that matches the input
  layout.
- `SMOTEN` is for categorical-only data, not mixed numeric/categorical data.
- `RandomOverSampler(shrinkage=...)` is numeric-data only.
- `ClusterCentroids` may densify or become inefficient on sparse data.
- `FunctionSampler` should remain small and explicit; it is not a replacement
  for a full pipeline.

## Use the scripts

- `scripts/sampler_smoke.py` for a tiny representative resampling smoke.
- `scripts/sampling_strategy_demo.py` for small examples of dict and callable
  sampling strategies.
