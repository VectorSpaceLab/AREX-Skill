---
name: detection-distances
description: "Use sktime detection, distance, kernel, and alignment APIs for
  anomaly, changepoint, segmentation, and pairwise similarity workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Detection, Distances, Kernels, and Alignment

Use this sub-skill for anomaly/outlier detection, changepoints, segmentation,
detector outputs, pairwise distances/kernels, DTW-style choices, and alignment.

## Route here

- Detect point anomalies, segment anomalies, changepoints, or segmentation boundaries.
- Use detector baselines such as `ThresholdDetector` or zero/dummy detectors.
- Construct pairwise distance or kernel matrices with `ScipyDist`, DTW wrappers,
  `AggrDist`, `FlatDist`, `KernelFromDist`, or alignment-derived distances.
- Diagnose sparse detector output, interval semantics, distance matrix shape,
  optional DTW dependencies, or kernel-vs-distance confusion.

## Route away

Detection metrics route to `evaluation-benchmarking`; raw container validation to
`data-interfaces`; panel classification/regression/clustering to `panel-learning`.

## References and helper

- [API reference](references/api-reference.md) for detector and pairwise transformer signatures.
- [Workflows](references/workflows.md) for detector and distance recipes.
- [Troubleshooting](references/troubleshooting.md) for output interpretation and optional backend fallbacks.
- Run [scripts/detection_distance_smoke.py](scripts/detection_distance_smoke.py)
  for a tiny CPU check.
