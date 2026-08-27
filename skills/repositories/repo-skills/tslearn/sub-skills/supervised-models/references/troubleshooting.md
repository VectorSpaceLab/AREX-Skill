# Troubleshooting: Supervised Models

Use this checklist when supervised tslearn estimators fail to import, fit, predict, or handle variable-length inputs.

## Shapelets import or backend order failure

Symptoms:

- `tslearn.shapelets` or `keras` imports fail.
- Keras uses an unexpected backend.
- Setting `KERAS_BACKEND` after an import does not change the backend.

Action:

1. Start a fresh Python process or notebook kernel.
2. Set the backend before any Keras import:

   ```python
   import os
   os.environ["KERAS_BACKEND"] = "torch"
   from tslearn.shapelets import LearningShapelets
   ```

3. Do not rely on `~/.keras/keras.json` for this tslearn shapelet path.
4. Re-run the tiny check:

   ```bash
   python scripts/supervised_smoke.py --mode shapelets
   ```

## Missing `keras` or backend package

Symptoms:

- `ModuleNotFoundError: No module named 'keras'`
- `ModuleNotFoundError: No module named 'torch'`
- `ImportError: No Keras backend installed`

Action:

1. Install Keras 3 and at least one backend package (`torch`, `tensorflow`, or `jax`).
2. Prefer `KERAS_BACKEND=torch` when torch is installed and has already been verified.
3. Import `LearningShapelets` only after the backend is set.
4. If shapelets remain blocked, use non-shapelet supervised estimators (`KNeighborsTimeSeriesClassifier`, `TimeSeriesSVC`, or `TimeSeriesMLPClassifier`) until the dependency gate is fixed.

## Variable-length incompatibility

Symptoms:

- `ValueError` from `check_dims`.
- `Sizes in X do not match maximum shapelet size`.
- `Sizes in X do not match maximum allowed size`.
- MLP or non-GAK SVM workflows fail on ragged inputs.

Action:

1. Convert ragged lists with `to_time_series_dataset(...)`.
2. For variable-length supervised tasks, use:
   - k-NN with time-series metrics such as `dtw`, `softdtw`, `ctw`, or `frechet`;
   - `TimeSeriesSVC(kernel="gak")` or `TimeSeriesSVR(kernel="gak")`;
   - `LearningShapelets` when every series is at least as long as the longest requested shapelet and `max_size` is large enough.
3. For `TimeSeriesMLPClassifier` or `TimeSeriesMLPRegressor`, resample or otherwise make all series equal-sized before fitting.
4. For early classification, keep inference partial series within the timestamp range used at fit time.

## Estimator fit failures

Symptoms and fixes:

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `RuntimeError` about GAK `gamma` being close to 0 | Constant or nearly constant data, or invalid explicit gamma | Scale the data, choose a positive explicit `gamma`, or avoid degenerate training series. |
| `ValueError` for invalid neighbor metric | Unsupported `metric` string | Use a documented metric such as `dtw`, `softdtw`, `ctw`, `frechet`, `sax`, `euclidean`, `sqeuclidean`, or `cityblock`. |
| `Classifier can't train when only one class is present` | Shapelet classifier received one class | Provide at least two target classes. |
| Shapelet length errors | Requested shapelet longer than the shortest series | Reduce `n_shapelets_per_size` lengths, resample data, or increase the shortest training length. |
| Early classifier split/cluster failures | Too few samples for `n_clusters`, class stratification, or `min_t` | Reduce `n_clusters`, add samples, or lower `min_t` within the fitted timestamp budget. |
| MLP convergence warnings | Tiny `max_iter` or hard optimization | Increase `max_iter`, scale inputs, or accept the warning for a smoke-only fit. |

## Prediction API surprises

- `TimeSeriesSVC.predict_proba()` and `predict_log_proba()` exist only when `probability=True` was set before `fit()`.
- SVM probability estimates are cross-validation estimates and may not match `predict()` exactly.
- `NonMyopicEarlyClassifier.early_predict(...)` can return `nan` predictions when the partial series is shorter than `min_t`.
- Early prediction raises if a partial input has more timestamps than the fitted training data.
- `TimeSeriesMLP*` flattens equal-sized series; ragged input should be routed to a variable-length estimator or resampled first.

## Route away

If the task is clustering, forecasting, serialization/persistence, or matrix profile, leave this sub-skill and use the root router.
