---
name: moabb
description: "Guide MOABB EEG and BCI benchmarking workflows: choose datasets,
  configure paradigms and sklearn pipelines, run leakage-aware evaluations, and
  analyze reproducible results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MOABB

MOABB (Mother of All BCI Benchmarks) is a Python framework for reproducible EEG
brain-computer-interface experiments. Use this skill when a task involves
MOABB dataset classes, MNE Raw/Epochs, motor imagery, P300/ERP, SSVEP, c-VEP,
scikit-learn pipelines, cross-session or cross-subject scores, benchmark result
stores, or MOABB analysis plots.

## Install and inspect first

Use a supported Python environment (the package metadata for this snapshot
requires Python 3.11 or newer), then install the base distribution:

```bash
python -m pip install moabb
python -c "import moabb; print(moabb.__version__)"
```

The base install includes the core MNE, `mne-bids`, NumPy/SciPy, pandas,
scikit-learn, pyRiemann, YAML, and data-access dependencies used by the routes
below. Optional extras are deliberate: `moabb[deeplearning]`, `moabb[optuna]`,
`moabb[interactive]`, and `moabb[carbonemission]` add separate capability
surfaces; do not install them merely to make a core CPU workflow work. Read
[API overview](references/api-overview.md) for the public object graph and
[troubleshooting](references/troubleshooting.md) before changing an
installation or enabling network data access. Run
[`scripts/check_environment.py`](scripts/check_environment.py) for a read-only
import and optional-dependency diagnosis; use its `--optional` flag only when
checking optional integrations.

## Route by the user's deliverable

- **Dataset discovery, catalog filtering, subjects/sessions, MNE data roots,
  local/BIDS data, FakeDataset, or download/cache recovery:** read
  [dataset-management](sub-skills/dataset-management/SKILL.md).
- **Motor imagery, imagined speech, P300, SSVEP, c-VEP, fixed windows,
  preprocessing, feature extraction, sklearn classifiers, filter banks, or
  YAML pipeline construction:** read
  [paradigms-and-pipelines](sub-skills/paradigms-and-pipelines/SKILL.md).
- **Within-session, within-subject, cross-session, cross-subject, splitters,
  learning curves, benchmark recipes, caching, or leakage checks:** read
  [evaluations-and-benchmarks](sub-skills/evaluations-and-benchmarks/SKILL.md).
- **Result DataFrames/`Results`, chance levels, paired statistics, score or
  distribution plots, timelines, or analysis reports:** read
  [analysis-and-visualization](sub-skills/analysis-and-visualization/SKILL.md).

Most end-to-end tasks use several routes in this order: dataset → paradigm and
pipeline → evaluation → analysis. Keep each boundary explicit so a score's
generalization claim and preprocessing information budget remain auditable.

## Safe operating defaults

1. Start with `FakeDataset` or a caller-provided local/BIDS root for API and
   shape checks. A real dataset's `data_path()`/`get_data()` can download files;
   ask for network, license, storage, and time approval before using it.
2. Set dataset subjects, sessions, event labels, frequency/window parameters,
   and the generalization target explicitly. Inspect `X.shape`, `y`, metadata,
   channel names, sampling rate, and the selected scorer before fitting.
3. Put every fitted transform (scaling, CSP, covariance, feature extraction,
   classifier, or template) inside the sklearn pipeline passed to the
   evaluation. Never fit on all trials before a split.
4. Begin with `random_state` fixed and `n_jobs=1`; use unique result/cache paths
   and `overwrite=False`. Increase data, workers, and optional features only
   after the tiny path is correct.
5. Treat results as metric-specific. Two-class paradigms commonly score ROC-AUC;
   multiclass accuracy uses a different chance reference. Preserve the
   evaluation protocol, metric, dataset selection, cache settings, and pipeline
   name beside any reported result.

## Bundled checks

The root diagnostic is linked above. For offline workflow checks, use the
helpers linked by each sub-skill: they create only synthetic data or temporary
caller-owned output and never download a dataset.

## Provenance and staleness

Read [repository provenance](references/repo-provenance.md) before applying
this skill to a checkout or deciding whether to refresh it. This graph was
extracted from a specific MOABB revision; public dataset catalogs, signatures,
optional dependencies, and evaluation behavior can change. Refresh when the
source revision, package version, public imports, or major evidence paths
change.
