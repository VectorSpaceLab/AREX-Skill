---
name: anomaly-detection
description: "Use Darts anomaly scorers, detectors, aggregators, and forecasting
  anomaly wrappers with correct score and label semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Anomaly detection

Use this sub-skill when the user needs Darts anomaly scores, binary anomaly detection, anomaly model wrappers around forecasts/filters, score alignment, or anomaly evaluation boundaries.

## Read first

- [`references/workflows.md`](references/workflows.md) for scorer + detector patterns, window effects, and forecasting residual wrappers.
- [`references/api-reference.md`](references/api-reference.md) for key scorer/detector classes and verified constructor notes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for window length, fitting order, score-vs-binary confusion, and label alignment.
- [`scripts/anomaly_smoke.py`](scripts/anomaly_smoke.py) for a tiny KMeansScorer + QuantileDetector smoke.

## Route by task

- **Raw value anomaly scoring**: choose a scorer such as `KMeansScorer` or another Darts scorer, fit on normal training data where required, then score validation/test.
- **Binary anomaly flags**: fit a detector such as `QuantileDetector`, `ThresholdDetector`, or `IQRDetector` on normal score behavior, then detect validation scores.
- **Forecast residual anomalies**: use `ForecastingAnomalyModel` or related wrapper around a Darts forecasting model; route model training to `../forecasting-workflows/` or `../torch-and-foundation-models/`.
- **Evaluate anomaly outputs**: separate continuous score evaluation from binary detector outputs; route metric details to `../evaluation-and-explainability/` when needed.

## Safe check

```bash
python scripts/anomaly_smoke.py --json
```

The smoke uses generated normal/spike series and asserts scorer/detector output types, binary values, and window-shortened score length.

## Boundaries

This sub-skill does not own time-series construction, forecasting model selection, or metric aggregation. It owns Darts anomaly API semantics and alignment. Do not treat anomaly scores as calibrated probabilities unless the chosen scorer/detector explicitly supports that interpretation.
