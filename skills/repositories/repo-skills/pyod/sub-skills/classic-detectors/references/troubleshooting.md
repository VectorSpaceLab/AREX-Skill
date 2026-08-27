# Classic Detector Troubleshooting

Read this when a direct PyOD detector fit, score, or evaluation flow fails or
produces suspicious results.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `contamination must be in (0, 0.5]` | Contamination is zero, negative, above 0.5, a string, or an invalid object | Use a float in `(0, 0.5]` or a valid PyThresh object; if anomaly rate is unknown, start with `0.05` or `0.1` and report uncertainty. |
| `NotFittedError` or missing `decision_scores_`/`threshold_`/`labels_` | Called `predict`, `decision_function`, or probability methods before `fit` | Fit the detector first, then access fitted attributes. |
| `could not convert string to float` or sklearn validation errors | Raw categorical/text/date columns passed to numeric detectors | Encode categorical columns, parse dates into numeric features, or route text/image/audio tasks to `specialized-modalities`. |
| Many false positives or too few anomalies | Contamination/threshold mismatch, score distribution has ties, or domain anomaly rate differs from default | Refit with a better contamination, evaluate scores against labels if available, and report ranks/top-k when threshold is uncertain. |
| Distance methods produce nonsensical neighbors | Feature scales differ strongly or units are mixed | Fit a scaler on training features and transform train/test consistently before `KNN`, `LOF`, `OCSVM`, `CBLOF`, `COF`, and similar methods. |
| Scores from two detectors have incompatible magnitudes | Raw detector scores are not calibrated across methods | Compare ranks/percentiles, standardize score columns before combination, or use ADEngine consensus guidance. |
| `ImportError` for `combo`, `suod`, `xgboost`, `torch`, or `pythresh` | Optional extra not installed | Install the exact extra (`pyod[combo]`, `pyod[suod]`, `pyod[xgboost]`, `pyod[torch]`, `pyod[pythresh]`) only if that workflow is selected. |
| Training is slow or memory-heavy | Detector complexity unsuitable for data size | Switch to fast baselines (`ECOD`, `HBOS`, `IForest`), subsample for exploration, or use ADEngine to route. |
| `evaluate_print` errors on labels/scores | Shape mismatch or passed labels instead of raw scores | Ensure `y_true` and raw anomaly scores have equal length; evaluate raw scores, not binary labels, for ROC/precision-at-n. |
| Probabilities seem overconfident | `predict_proba` is a score transformation, not supervised calibration | Explain that probabilities are derived from unsupervised scores; validate with labels or domain review. |

## Debug checklist

1. Confirm `X_train` is a numeric 2D array with finite values.
2. Confirm `contamination` is plausible and valid.
3. Fit once, then inspect `decision_scores_.shape`, `threshold_`, and
   `labels_.sum()`.
4. For test data, confirm `X_test.shape[1] == X_train.shape[1]` and apply the
   same preprocessing.
5. If a detector import fails, classify it as base vs optional-extra before
   installing anything.
6. If detector choice is unclear, route to `automated-lifecycle` for ADEngine.
