---
name: streaming-evaluation
description: "Ingest River-compatible streams, validate models online, handle
  delayed labels, and choose evaluation metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# River streaming evaluation

Use this sub-skill when the task is to turn a River-compatible data stream into online evaluation, delayed-label scoring, or checkpointed metric tracking.

## Load order

1. Read `references/data-streams.md` to normalize dataset shapes, adapters, target handling, and delayed-label streams.
2. Read `references/evaluation-and-metrics.md` before choosing metrics, progressive validation APIs, active learning behavior, or forecasting evaluation.
3. Read `references/troubleshooting.md` when stream parsing, moment/delay alignment, weights, metric compatibility, or optional adapters fail.
4. Use `scripts/stream_evaluation_smoke.py` for a tiny offline smoke test of CSV ingestion, delayed labels, and sample-weight routing.

## Route elsewhere

- Feature construction, encoders, target transforms, rolling feature engineering, and pipeline composition belong to `pipelines-and-features`.
- Base estimator contracts, cloning, tags, and check-estimator work belong to `online-core-api`.
- Supervised model family choice, optimizer/loss tuning, and model wrappers belong to `supervised-models`.
- Drift, anomaly, clustering, forecasting model design, active learning strategy design, bandits, recommenders, and other specialized model families belong to `specialized-workflows`.
- If the task is only about a particular model class or family, do not turn this into a stream-evaluation task.

## Fast routing cues

- Use `stream.iter_csv` for files, `stream.iter_array` for arrays, `stream.iter_frame` for eager dataframes, `stream.iter_libsvm` for sparse numeric text, and `stream.iter_sql` / `stream.iter_sklearn_dataset` when the source is already an SQLAlchemy query or scikit-learn `Bunch`.
- Use `Dataset.take(k)` to cap built-in or synthetic datasets when you need a bounded sample.
- Use `evaluate.progressive_val_score` for the standard predict-then-learn loop, `evaluate.iter_progressive_val_score` for checkpoints, and a manual loop only when you need custom control.
- Use `moment` and `delay` when labels arrive late or the stream should be replayed in arrival order.
- Use `simulate_qa` directly when you need to inspect the question/answer timeline before scoring.
- Use `metrics.Silhouette` for unlabeled clustering, `metrics.ROCAUC` / `metrics.RollingROCAUC` / `metrics.RollingPRAUC` for anomaly-style scores, and regression metrics such as `MAE`, `RMSE`, `R2`, or `SMAPE` for forecasting.
