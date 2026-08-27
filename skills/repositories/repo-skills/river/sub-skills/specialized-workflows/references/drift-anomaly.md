# Drift Detection and Anomaly Workflows

## Drift detector update patterns

River drift detectors consume one value at a time through `update(value)`. The state flags describe the result of the most recent update, not a permanent label for the whole stream.

- Numeric detectors such as `drift.ADWIN`, `drift.KSWIN`, and `drift.PageHinkley` monitor scalar values. Those values can be raw measurements, losses, residuals, or another one-dimensional signal.
- Binary detectors in `drift.binary` consume an error/failure stream. For classifier monitoring, pass `0` when the prediction was correct and `1` when it was wrong.
- `drift_detected` is set immediately after `update`. Many detectors reset or trim internal state after a detection, so record the timestamp/index before continuing.
- `warning_detected` exists only on warning-capable detectors. Do not read it from detectors that only expose `drift_detected`.
- `ADWIN` exposes useful numeric state: `width`, `estimation`, `variance`, `total`, and `n_detections`. Treat those as detector state diagnostics, not model accuracy metrics.

Minimal direct detector loop:

```python
from river import drift

sensor = drift.PageHinkley(mode="up")
for i, value in enumerate(values):
    sensor.update(value)
    if sensor.drift_detected:
        handle_drift_at(i)
```

Classifier error-monitoring loop:

```python
from river import drift

detector = drift.binary.DDM()
for x, y in stream:
    y_pred = model.predict_one(x)
    if y_pred is not None:
        detector.update(int(y_pred != y))
        if detector.warning_detected:
            start_shadow_training()
        if detector.drift_detected:
            reset_or_swap_model()
    model.learn_one(x, y)
```

## `DriftRetrainingClassifier` placement

`drift.DriftRetrainingClassifier` is a classifier wrapper. Place it around the classifier or classifier pipeline whose state should be reset or swapped on drift.

```python
from river import drift, preprocessing, linear_model

base_model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
model = drift.DriftRetrainingClassifier(
    model=base_model,
    drift_detector=drift.binary.DDM(),
    train_in_background=True,
)
```

Placement rules:

- Wrap the whole classifier pipeline if preprocessing statistics should reset or shadow-train together with the classifier.
- Wrap only the final classifier if upstream feature transformers should keep their history across drift.
- With `train_in_background=True`, use a detector that has warning state. The warning starts training the background model; the drift event swaps it in.
- With `train_in_background=False`, the wrapped model is cloned/reset on drift instead of being replaced by a warning-trained background model.
- The wrapper internally predicts before learning so it can feed an error bit to the detector. Cold-start predictions can be `None`; this is normal and is skipped by the detector update.

Use explicit manual detector loops when retraining needs custom behavior such as replay buffers, partial reset, human approval, or different drift responses for different model components.

## Anomaly score semantics

River anomaly detectors expose `score_one`, not `predict_one`. A high score means more anomalous and a low score means more normal. The score scale is detector-specific.

Common detector choices:

- `anomaly.HalfSpaceTrees`: unsupervised feature-space detector; features should be in `[0, 1]` or explicit `limits` should be provided. Use an online min-max scaler when limits are not known.
- `anomaly.LODA` and `anomaly.LocalOutlierFactor`: feature-space outlier scoring with window or projection behavior. Score before learn when simulating production.
- `anomaly.OneClassSVM`: online one-class SVM-style scoring.
- `anomaly.GaussianScorer`, `anomaly.StandardAbsoluteDeviation`, and `anomaly.PredictiveAnomalyDetection`: supervised anomaly detectors that score a target `y`, optionally with `x`.

Do not treat raw anomaly scores as class labels:

```python
score = detector.score_one(x)
metric.update(y_true=is_anomaly, y_pred=score)  # ranking metric, not a label metric
```

For binary anomaly decisions, convert scores through a filter or a threshold rule:

```python
from river import anomaly

filtered = anomaly.ThresholdFilter(detector, threshold=0.95)
score = filtered.score_one(x)
is_anomaly = filtered.classify(score)
```

## Filters and detector protection

`anomaly.ThresholdFilter` marks a score as anomalous when `score >= threshold`. `anomaly.QuantileFilter` learns a running score quantile and marks scores above that quantile.

Both filters wrap a detector and can be used as pipeline steps. Their `protect_anomaly_detector` option is the intended control for whether anomalous samples update the wrapped detector:

- `protect_anomaly_detector=True` is safest for sporadic outliers because anomalies do not become part of the normal baseline.
- If disabled protection is important to a workflow, verify the installed filter behavior with a tiny sample or update the wrapped detector manually. `QuantileFilter` explicitly handles disabled protection; `ThresholdFilter` inherits the shared filter learning path.

Filter decisions are still derived from scores. Keep the threshold/quantile rationale explicit and validate it on the intended score distribution.

## Anomaly evaluation caveats

- Use ranking metrics such as ROC AUC when comparing continuous anomaly scores against known anomaly labels.
- Use classification metrics only after converting scores to boolean labels with a threshold or filter.
- Expect warm-up behavior. Some detectors return `0` or uninformative scores until enough samples or windows have been learned.
- Score-before-learn simulates deployment for unsupervised detectors. Learn-before-score answers a different question: how well the detector scores points it has already absorbed.
- Missing feature behavior is estimator-specific. Prefer stable feature schemas or preprocess missing values before the detector when possible.
- A threshold chosen for one detector is not portable to another detector because score ranges are relative to the estimator.
