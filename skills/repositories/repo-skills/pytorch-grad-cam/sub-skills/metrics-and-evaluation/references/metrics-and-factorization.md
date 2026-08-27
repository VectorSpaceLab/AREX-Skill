# Confidence Metrics and Factorization

## Confidence-change metrics

`CamMultImageConfidenceChange` multiplies the normalized input tensor by the CAM
mask and measures how model confidence changes.

Related helpers:

- `DropInConfidence` returns the positive drop in confidence after masking.
- `IncreaseInConfidence` returns whether the score increased.

Typical use:

```python
from pytorch_grad_cam.metrics.cam_mult_image import CamMultImageConfidenceChange
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

metric = CamMultImageConfidenceChange()
scores = metric(input_tensor, grayscale_cams, targets, model)
```

## ROAD metrics

ROAD stands for Remove and Debias. It removes the most or least relevant
regions and re-evaluates the model with a noisy linear imputer.

Important classes:

- `ROADMostRelevantFirst(percentile=80)`
- `ROADLeastRelevantFirst(percentile=20)`
- `ROADMostRelevantFirstAverage(percentiles=[...])`
- `ROADLeastRelevantFirstAverage(percentiles=[...])`
- `ROADCombined(percentiles=[...])`

The `ROADCombined` score is `(least-relevant-first - most-relevant-first) / 2`
across the chosen percentiles.

## Deep Feature Factorization

DFF decomposes activations into non-negative concept components and visualizes
per-concept explanation maps.

```python
from pytorch_grad_cam.feature_factorization.deep_feature_factorization import (
    DeepFeatureFactorization,
    dff,
    run_dff_on_image,
)
```

Use DFF when the user wants concept discovery rather than a class score. It
expects a target layer, optional concept classifier, and a tensor/image pair.
The helper returns concept embeddings and explanation maps scaled to the input
image size.

## Safe smoke script

```bash
python sub-skills/metrics-and-evaluation/scripts/tiny_metric_smoke.py
```

This script uses a tiny in-memory classifier and a synthetic CAM mask so it can
validate metric wiring without pretrained weights.
