# Anomaly API reference

## Verified constructor notes for Darts 0.46.1

```text
KMeansScorer(window=1, k=8, component_wise=False, window_agg=True, diff_fn=ae, **kwargs)
QuantileDetector(low_quantile=None, high_quantile=None)
```

## Main concepts

| Concept | Examples | Output |
| --- | --- | --- |
| Scorer | `KMeansScorer`, PyOD-based scorers, norm/difference scorers | continuous Darts `TimeSeries` of anomaly scores |
| Detector | `QuantileDetector`, `ThresholdDetector`, `IQRDetector` | binary Darts `TimeSeries` of anomaly flags |
| Aggregator | Darts anomaly aggregators | combined score/detection behavior across components/windows |
| Anomaly model wrapper | `ForecastingAnomalyModel`, filtering anomaly wrappers | scores derived from residuals or model predictions |

## Fitting order

For a fittable scorer plus fittable detector:

```python
from darts.ad import KMeansScorer, QuantileDetector

scorer = KMeansScorer(k=2, window=3)
scorer.fit(normal_train)
train_scores = scorer.score(normal_train)
val_scores = scorer.score(validation)

detector = QuantileDetector(high_quantile=0.99)
detector.fit(train_scores)
binary = detector.detect(val_scores)
```

Fit on anomaly-free or representative normal behavior when the use case is unsupervised thresholding.

## Window effects

Windowed scorers often produce fewer score points than input points. With `window=3`, expect approximately `len(series) - window + 1` score points. Align labels and validation series to `scores.time_index` before computing metrics.

## Forecasting anomaly wrappers

Use a forecasting anomaly wrapper when anomalies should be residual-based rather than raw-value based:

```python
from darts.ad import ForecastingAnomalyModel, NormScorer

# forecasting_model should be a compatible fitted or fit-ready Darts forecasting model.
am = ForecastingAnomalyModel(model=forecasting_model, scorer=NormScorer())
# Follow the installed Darts API for fit/score parameters and route model setup elsewhere.
```

Keep underlying model choice/training outside this sub-skill. Evaluate continuous scores and binary flags separately.
