# Anomaly troubleshooting

## Score series is shorter than input

Windowed scorers use rolling windows. For `window=3`, a score series commonly has `len(series) - 3 + 1` points. Align labels and raw series to the score time index before plotting or evaluating.

## Detector output is not binary

You may be looking at scorer output, not detector output. Scorers produce continuous anomaly scores. Detectors convert scores to binary flags. Use a detector and inspect `set(binary.values().flatten())`.

## Detector raises because it was not fit

Fittable detectors such as `QuantileDetector` need normal training scores:

```python
detector.fit(train_scores)
binary = detector.detect(val_scores)
```

Do not fit thresholds on validation data containing anomalies unless the user explicitly wants an adaptive/contaminated threshold.

## Probabilistic input rejected

Some detectors/scorers expect deterministic series. If a forecast is stochastic, convert to a point summary or use a scorer designed for probabilistic outputs.

## Residual anomaly wrapper gives confusing results

Check whether the underlying forecasting model is fit, whether target/covariates are aligned, and whether the residual scorer direction matches the user's anomaly definition. Route forecast model setup back to the owning forecasting sub-skill.

## Multivariate anomalies

Decide whether the user wants component-wise anomalies or aggregated anomalies. Configure scorer/detector component behavior accordingly and document how labels are shaped.
