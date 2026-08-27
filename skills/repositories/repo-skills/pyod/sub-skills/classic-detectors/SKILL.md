---
name: classic-detectors
description: "Operate PyOD's classic tabular detector API for numeric arrays:
  detector selection, fit/predict/score workflows, synthetic data utilities,
  score interpretation, and CPU smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Classic PyOD Detectors

Use this sub-skill when the user wants classic PyOD anomaly/outlier detection on tabular or numeric array data and already has, or can produce, a 2D numeric feature matrix `X` shaped `(n_samples, n_features)`.

## Best-fit tasks

- Start a novice on the common `fit` -> `decision_function` -> `predict` workflow.
- Choose a reasonable classic detector family for tabular data.
- Explain fitted detector attributes such as `decision_scores_`, `labels_`, and `threshold_`.
- Generate synthetic numeric data with `pyod.utils.data` and evaluate scores with ROC-AUC / precision @ rank n.
- Run a deterministic CPU smoke check with a bundled synthetic-data script.

## Route elsewhere

- ADEngine, `pyod` CLI, MCP server, and agent lifecycle orchestration -> `automated-lifecycle`.
- Time series, graph, embedding, text, image, audio, and deep optional-backend workflows -> `specialized-modalities`.
- Model persistence, trusted load/save, score thresholding via PyThresh, score combination, SUOD/XGBOD operational extras -> `model-operations`.
- Repository source layout, tests, docs, package metadata, or packaged skill maintenance -> `repo-maintenance`.

## Quick operating default

For an unlabeled numeric table, prefer a simple, defensible baseline first:

```python
from pyod.models.ecod import ECOD

clf = ECOD(contamination=0.1)
clf.fit(X_train)
train_scores = clf.decision_scores_        # higher means more abnormal
train_labels = clf.labels_                 # 0=inlier, 1=outlier
test_scores = clf.decision_function(X_test)
test_labels = clf.predict(X_test)
```

If the user cares about high-dimensional scalability, try `IForest` or `COPOD`; for local-density anomalies on moderate-size, scaled numeric data, try `KNN` or `LOF`. Do not report raw scores as calibrated probabilities; convert to ranks/percentiles, binary labels, or `predict_proba` outputs.

## References and bundled scripts

Load these local files as needed:

- [API reference](references/api-reference.md): BaseDetector methods/attributes, common detector signatures, and `pyod.utils.data` helper contracts.
- [Workflows](references/workflows.md): novice quick-start, detector-selection flow, preprocessing/validation steps, score interpretation, and multi-detector comparison recipes.
- [Model overview](references/model-overview.md): detector-family routing table for probabilistic, linear, proximity, ensemble, and neural-at-routing-level choices.
- [Troubleshooting](references/troubleshooting.md): concrete symptoms and recovery actions for input validation, contamination, scaling, optional imports, slow detectors, and score interpretation.
- [Classic detector smoke script](scripts/classic_detector_smoke.py): deterministic synthetic-data train/evaluate helper adapted from PyOD's basic KNN example; use it to sanity-check `IForest`, `KNN`, `ECOD`, or `COPOD` in the current Python environment.
