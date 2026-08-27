# Anomaly workflows

## Workflow: windowed KMeans scorer plus quantile detector

```python
from darts.ad import KMeansScorer, QuantileDetector

scorer = KMeansScorer(k=2, window=3)
scorer.fit(train_normal)
train_scores = scorer.score(train_normal)
val_scores = scorer.score(val_with_possible_spikes)

assert len(val_scores) == len(val_with_possible_spikes) - 3 + 1

detector = QuantileDetector(high_quantile=0.99)
detector.fit(train_scores)
binary = detector.detect(val_scores)
assert set(binary.values().flatten()).issubset({0.0, 1.0})
```

Use score time indices for alignment:

```python
labels_aligned = labels.slice_intersect(val_scores)
```

## Workflow: threshold/IQR detector on scores

If the user has domain thresholds:

```python
from darts.ad import ThresholdDetector

detector = ThresholdDetector(high_threshold=threshold)
binary = detector.detect(scores)
```

If the threshold should be learned from normal scores, use `QuantileDetector` or `IQRDetector` and fit on normal score series.

## Workflow: forecasting residual anomaly model

Use this when anomalies are deviations from a forecast rather than unusual raw values:

1. Train or provide the Darts forecasting model in `forecasting-workflows` or `torch-and-foundation-models`.
2. Choose a residual scorer such as a norm/difference scorer.
3. Wrap with `ForecastingAnomalyModel` following the installed Darts API.
4. Fit/score on aligned target/covariate data.
5. Evaluate continuous scores and binary outputs separately.

## Evaluation boundary

- Continuous scores answer “how anomalous?” and support threshold-free ranking or score-based metrics.
- Binary detector outputs answer “is anomalous?” and support precision/recall/F1-style metrics when labels exist.
- Route detailed metric and reduction handling to `evaluation-and-explainability`.
