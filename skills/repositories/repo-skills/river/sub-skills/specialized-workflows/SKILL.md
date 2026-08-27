---
name: specialized-workflows
description: "River workflows for drift detection, anomaly scoring, clustering,
  forecasting, bandits, recommendation, imbalanced learning, factorization, and
  probability distributions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Specialized Workflows

Use this sub-skill when a River task goes beyond ordinary supervised prediction and needs a specialized online workflow: drift detection and retraining, anomaly scoring and filtering, clustering, forecasting, bandits, recommendation/ranking, imbalanced streaming wrappers, factorization machines for recommendation or CTR-style data, or streaming probability distributions.

## Route here

- Monitor drift detectors, interpret drift/warning state, or wrap an existing classifier with `drift.DriftRetrainingClassifier`.
- Score anomalies, threshold or quantile-filter anomaly scores, or decide whether anomalies should update the detector.
- Train clustering models, keep cluster centers or micro-clusters current, and choose internal or external clustering metrics.
- Forecast time series with `time_series.Forecaster` APIs and horizon-aware evaluation metrics.
- Run bandit policy loops with `pull` and `update`, or replay logged bandit history without requiring a Gym environment.
- Rank candidate items with `reco` models or model user/item/context interactions with `facto` factorization machines.
- Add `imblearn` sampling wrappers around classifiers or regressors and decide where the sampling boundary belongs.
- Use `proba` distributions as online state, reward objects, density estimates, or rolling uncertainty summaries.

## Reroute

- Shared stream adapters, built-in datasets, delayed labels, progressive validation, and generic metric compatibility: use `../streaming-evaluation/SKILL.md`.
- Ordinary supervised classification/regression model family selection, optimizer/loss choice, ensembles, multiclass, multioutput, and model-selection wrappers: use `../supervised-models/SKILL.md`.
- Feature construction, pipeline operators, selectors, unions, rolling feature extraction, parameter routing, and pipeline debugging: use `../pipelines-and-features/SKILL.md`.

## Start fast

1. Drift detectors are state machines updated one observation at a time. Read `drift_detected` and, when supported, `warning_detected` immediately after each `update`.
2. `DriftRetrainingClassifier` wraps the classifier that should be reset or swapped. With background training enabled, use a warning-capable drift detector such as the binary DDM-family detectors.
3. Anomaly detectors return scores, not class labels. Use `ThresholdFilter.classify(score)` or `QuantileFilter.classify(score)` when a boolean anomaly decision is required.
4. Clustering models learn from `x` only. Internal metrics such as `Silhouette` need `x`, `y_pred`, and current `centers`; external metrics compare predicted clusters with known labels.
5. Forecasters learn with `learn_one(y, x=None)` and return one forecast per requested horizon step. Use `evaluate.evaluate` or `evaluate.iter_evaluate` for horizon metrics.
6. Bandit policies can be controlled directly with `pull`/`update`; use `bandit.evaluate_offline` for replay-style evaluation when no interactive environment is available.
7. Recommenders use hashable user/item IDs and rank a candidate item set. Factorization machines treat string features as categorical variables and are useful for CTR-style interaction features.

Run the bundled synthetic smoke check in an environment where `import river` succeeds:

```bash
python scripts/specialized_workflows_smoke.py
```

Select a subset when validating one workflow:

```bash
python scripts/specialized_workflows_smoke.py --section drift --section anomaly --json
```

## References

- `references/drift-anomaly.md` covers detector update patterns, retraining wrapper placement, anomaly score semantics, filters, and anomaly evaluation caveats.
- `references/clustering-forecasting-bandits-reco.md` covers clustering loops and metrics, forecasting horizon metrics, bandit online/offline evaluation, recommendation/ranking, factorization machines, imbalanced learning, and probability distributions.
- `references/troubleshooting.md` maps common state, threshold, metric, horizon, bandit history, recommender ID, sampler placement, and optional dependency failures to checks and fixes.
- `scripts/specialized_workflows_smoke.py` runs tiny deterministic checks with synthetic data and skips optional pieces gracefully when unsupported.
