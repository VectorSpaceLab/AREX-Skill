---
name: imbalanced-learn
description: "Router for imbalanced-learn samplers, workflows, metrics,
  datasets, and balanced batch generators."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# imbalanced-learn

Use this repo skill for the `imbalanced-learn` package when the task is about
class imbalance, resampling, imbalance-aware pipelines, evaluation metrics, or
balanced mini-batches for Keras/TensorFlow.

The import root is `imblearn`. The package is scikit-learn compatible and is
centered on `fit_resample` workflows for tabular and scientific-python style
data.

## Quick start

- If you need the package API, start with this router and then read the relevant
  sub-skill.
- If you need a fast sanity check, run `scripts/package_smoke.py`.
- If you need live API names or signatures from the installed environment, run
  `scripts/inspect_signatures.py`.

### Minimal import check

```python
from imblearn import FunctionSampler
from imblearn.over_sampling import RandomOverSampler
```

If that import fails, read `references/troubleshooting.md` before assuming the
repo skill is stale.

## How to choose a sub-skill

### `sampling-algorithms`
Use this when the request mentions:

- `RandomOverSampler`, `SMOTE`, `ADASYN`, `SMOTENC`, `SMOTEN`
- `RandomUnderSampler`, `TomekLinks`, `EditedNearestNeighbours`, `NearMiss`
- `ClusterCentroids`, `SMOTEENN`, `SMOTETomek`
- `FunctionSampler`, `sampling_strategy`, `check_sampling_strategy`
- sparse, pandas, heterogeneous, or categorical feature handling during
  resampling

Read `sub-skills/sampling-algorithms/SKILL.md` first.

### `model-workflows`
Use this when the request mentions:

- `Pipeline` or `make_pipeline`
- leakage-safe resampling with classifiers
- `BalancedBaggingClassifier`, `BalancedRandomForestClassifier`
- `EasyEnsembleClassifier`, `RUSBoostClassifier`
- `InstanceHardnessCV`

Read `sub-skills/model-workflows/SKILL.md` first.

### `evaluation-and-data`
Use this when the request mentions:

- `make_imbalance`, `fetch_datasets`
- `classification_report_imbalanced`, `geometric_mean_score`
- sensitivity/specificity metrics, MA-MAE, or `ValueDifferenceMetric`
- data-leakage pitfalls and dataset-balancing examples

Read `sub-skills/evaluation-and-data/SKILL.md` first.

### `optional-batch-generators`
Use this when the request mentions:

- `balanced_batch_generator`
- `BalancedBatchGenerator`
- Keras or TensorFlow mini-batch workflows for imbalanced data

Read `sub-skills/optional-batch-generators/SKILL.md` first.

## Cross-cutting rules

- Resample only the training split, not the entire dataset, when the user is
  trying to avoid leakage.
- Preserve sparse inputs as CSR-compatible workflows where possible, but know
  that many samplers return dense output.
- Treat pandas support as first-class when the user provides DataFrames.
- Treat TensorFlow/Keras support as optional: useful, but not required for the
  core CPU package.
- When a workflow needs the exact constructor or signature of a public class or
  function, consult the nearest reference file or run
  `scripts/inspect_signatures.py`.

## Read these files when needed

- `references/api-overview.md` for the compact module and symbol map.
- `references/troubleshooting.md` for install, import, dtype, sparse, leakage,
  network, and optional-backend issues.
- `references/repo-provenance.md` for the source snapshot that produced this
  skill.
- `references/repo-routing-metadata.json` for managed-router placement data.

## Root scripts

- `scripts/package_smoke.py` for a small end-to-end CPU and optional-backend
  smoke check.
- `scripts/inspect_signatures.py` for live API introspection from the installed
  environment.

## What this skill does not do

- It does not replace the sub-skill-level workflow guides.
- It does not ask you to run the original repository examples as runtime skill
  instructions.
- It does not claim GPU-specific functionality; the package is CPU-oriented,
  with optional TensorFlow/Keras dependencies.
