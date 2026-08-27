# Prediction algorithms troubleshooting

Use this when a built-in algorithm, custom `AlgoBase` subclass, or neighbor lookup does not behave as expected.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| A prediction for an unknown user or item falls back to the global mean | `estimate()` raised `PredictionImpossible`, or the algorithm intentionally returns a fallback for missing ids | Check `pred.details['was_impossible']` and `pred.details['reason']`. If you want a different fallback, override `default_prediction()` in the custom class. |
| `KNNBasic` / `KNNWithMeans` / `KNNWithZScore` cannot predict with missing ids | Those algorithms expect both ids to be known before they can aggregate neighbors | Use raw ids that exist in the fitted trainset, or expect the fallback path and inspect `Prediction.details`. |
| `NameError: Wrong sim name ...` | `sim_options['name']` is misspelled or unsupported | Use `cosine`, `msd`, `pearson`, or `pearson_baseline`. Remember that `pearson_baseline` needs baselines. |
| `ValueError: Invalid method ... for baseline computation` | `bsl_options['method']` is misspelled | Use `als` or `sgd`. Keep the per-method keys consistent with the chosen method. |
| `actual_k` is smaller than `k` | Some neighbors had zero or negative similarity, or too few positives survived `min_support` / `min_k` | Lower `min_k`, use a different similarity, or inspect the fitted similarity matrix. `Prediction.details['actual_k']` tells you how many neighbors were really used. |
| `KNNBaseline` behaves oddly with Pearson-baseline similarity | Baseline and similarity settings are misaligned, or `bsl_options` are too weak for the dataset | Configure both `sim_options` and `bsl_options` deliberately. For `pearson_baseline`, baselines are computed first and then reused in the similarity computation. |
| `NMF` raises on construction | `init_low` is negative | Keep `init_low >= 0`. Use a small positive value if you want strictly positive initial factors. |
| Factor models differ across runs | `random_state` was omitted or changed | Set `random_state` for `SVD`, `SVDpp`, `NMF`, and `CoClustering` when you need repeatable smoke checks. |
| `SVDpp` is slow or memory-heavy | `cache_ratings` trades memory for speed | Turn `cache_ratings=True` when memory is available and you want faster training. Leave it `False` when memory is tighter. |
| `NormalPredictor` changes every time | It samples from NumPy's RNG on each prediction | Seed NumPy if you need a reproducible smoke run, or avoid exact-value assertions. |
| `get_neighbors()` returns ids that look wrong | It returns inner ids, not raw ids, and the `user_based` flag changes the entity domain | Convert with `to_raw_uid()` / `to_raw_iid()` before displaying them, and verify the algorithm is using the domain you intended. |
| `Prediction.details` is empty | `estimate()` returned a bare scalar | Return `(est, details)` from `estimate()` when you want metadata to survive into the `Prediction`. |
| `clip=True` hides the raw estimate | The default clipping is bounding the prediction to the rating scale | Pass `clip=False` while debugging raw estimates, especially for factor models. |

## Smoke script pointers

- `scripts/predict_single_rating_smoke.py` exercises `predict()` and `test()` with `Prediction.details`.
- `scripts/baseline_similarity_smoke.py` exercises baseline configuration, similarity configuration, and the invalid-method/name failures.
- `scripts/get_neighbors_smoke.py` exercises `get_neighbors()` and the invalid similarity-name failure.
- `scripts/custom_algorithm_smoke.py` exercises a custom `AlgoBase` subclass and the default-prediction fallback.
