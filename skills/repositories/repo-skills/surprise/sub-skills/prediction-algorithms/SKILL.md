---
name: prediction-algorithms
description: "Choose, configure, fit, and extend Surprise prediction algorithms,
  including baselines, similarities, prediction details, neighbor retrieval, and
  custom AlgoBase subclasses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Prediction Algorithms

Use this sub-skill when you need to choose a Surprise predictor, tune baseline or similarity options, inspect `Prediction` details, retrieve neighbors, or implement a custom `AlgoBase` subclass.

## Route here

- Pick a built-in algorithm: `NormalPredictor`, `BaselineOnly`, `KNNBasic`, `KNNWithMeans`, `KNNWithZScore`, `KNNBaseline`, `SVD`, `SVDpp`, `NMF`, `SlopeOne`, or `CoClustering`.
- Configure `bsl_options` and `sim_options` for baseline-centric or neighborhood methods.
- Work with `predict()`, `test()`, `Prediction`, and `PredictionImpossible`.
- Call `get_neighbors()` on similarity-based algorithms and convert inner ids back to raw ids when you need to display them.
- Extend `AlgoBase` when the built-ins do not match the target behavior.

## Stay out

- Dataset loading, reader formats, `Trainset` construction, and raw/inner id basics belong in the data-loading sub-skill.
- `cross_validate`, `GridSearchCV`, iterator strategy, and metric orchestration belong in evaluation-and-search.
- Top-N recommendation, precision/recall@k, and dump/load workflows belong in recommendation-and-analysis.

## Start fast

1. Choose the family:
   - `BaselineOnly` if biases are the target.
   - `KNN*` if you want neighborhood aggregation and `actual_k`.
   - `SVD`, `SVDpp`, or `NMF` if you want latent factors.
   - `SlopeOne` or `CoClustering` if you want their specialized rules.
2. Decide whether the algorithm uses `bsl_options`, `sim_options`, both, or neither.
3. Fit on a `Trainset`, then inspect `Prediction.details` from `predict()` or `test()`.
4. Pass inner ids to `get_neighbors()` and expect inner ids back.
5. For custom algorithms, subclass `AlgoBase`, call the base `__init__` and `fit`, then implement `estimate()`.

## Smoke checks

- `python scripts/predict_single_rating_smoke.py`
- `python scripts/baseline_similarity_smoke.py`
- `python scripts/get_neighbors_smoke.py`
- `python scripts/custom_algorithm_smoke.py`

## References

- `references/algorithms.md` covers algorithm families, constructor knobs, fit/predict/test semantics, `Prediction` details, and custom subclass patterns.
- `references/troubleshooting.md` maps common option, neighbor, randomness, and fallback failures to fixes.
