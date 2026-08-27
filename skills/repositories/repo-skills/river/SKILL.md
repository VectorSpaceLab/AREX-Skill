---
name: river
description: "Use River for online machine learning with streaming estimators,
  pipelines, datasets, progressive evaluation, drift, anomaly, clustering,
  forecasting, bandits, and recommender workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# River repo skill

Use this skill when a task involves River, online machine learning, one-sample-at-a-time estimators, dictionary feature streams, progressive validation, concept drift, or River package maintenance.

## First checks

- Normal package install: `pip install river`.
- Mini-batch/DataFrame workflows: `pip install "river[pandas]"`.
- Source checkout installs build a Rust extension through maturin; prefer released wheels unless the task is repository maintenance.
- Minimal import check:

```python
import river
from river import compose, linear_model, metrics, preprocessing
model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
metric = metrics.Accuracy()
```

Run `scripts/check_river_environment.py` when installation, Rust-extension import, or quickstart behavior is uncertain.

## Route map

| Task | Read |
| --- | --- |
| Estimator lifecycle, `learn_one`, `predict_one`, `transform_one`, base classes, tags, cloning, mutation, generic checks, new-estimator compatibility. | `sub-skills/online-core-api/SKILL.md` |
| Pipelines, `|`, `+`, `*`, selectors, feature unions, preprocessing, feature extraction, online statistics, target aggregation, `learn_during_predict`, pipeline debugging. | `sub-skills/pipelines-and-features/SKILL.md` |
| Built-in datasets, stream adapters, CSV/array/dataframe ingestion, progressive validation, delayed labels, sample weights, metrics, metric/model compatibility. | `sub-skills/streaming-evaluation/SKILL.md` |
| Supervised classification/regression model families, linear models, optimizers/losses, trees, forests, ensembles, naive Bayes, neighbors, multiclass/multioutput/model-selection/compat wrappers. | `sub-skills/supervised-models/SKILL.md` |
| Concept drift, anomaly detection, clustering, forecasting/time series, bandits, recommenders, factorization machines in sparse interaction workflows, imbalanced learning, probability utilities. | `sub-skills/specialized-workflows/SKILL.md` |

## Shared references

- Read `references/api-map.md` for public module-family routing and task-to-sub-skill mapping.
- Read `references/troubleshooting.md` for installation, import, Rust extension, optional dependency, and cross-cutting runtime failures.
- Read `references/development-and-verification.md` when editing a River checkout or choosing focused tests.
- Read `references/repo-provenance.md` before deciding whether this generated skill is stale for a checkout.

## Common workflow skeleton

```python
from river import compose, linear_model, metrics, preprocessing

model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
metric = metrics.Accuracy()

for x, y in stream:
    y_pred = model.predict_one(x)
    if y_pred is not None:
        metric.update(y, y_pred)
    model.learn_one(x, y)
```

Use `evaluate.progressive_val_score` instead of a manual loop when the task is standard online evaluation or delayed progressive validation.

## Important constraints

- River's core `*_one` API is dictionary-based and does not require pandas.
- Optional pandas support is needed for mini-batch `*_many` APIs and some dataframe workflows.
- River generally avoids heavy input validation; bad feature/target types may fail inside the model.
- Predict before learning when evaluating a stream, including clustering and anomaly workflows when a score/assignment is compared before state update.
- No primary package CLI exists; use Python APIs and bundled smoke scripts.
- Do not use original River notebooks or tests as runtime dependencies for this skill; the bundled scripts provide safe reusable checks.

## Smoke scripts

From this skill directory, run only the scripts that match the task:

```sh
python scripts/check_river_environment.py
python sub-skills/online-core-api/scripts/estimator_contract_smoke.py
python sub-skills/pipelines-and-features/scripts/pipeline_feature_smoke.py
python sub-skills/streaming-evaluation/scripts/stream_evaluation_smoke.py
python sub-skills/supervised-models/scripts/supervised_model_smoke.py
python sub-skills/specialized-workflows/scripts/specialized_workflows_smoke.py
```
