---
name: posterior_two_sample_metrics
description: Compute deterministic posterior two-sample diagnostics including C2ST-style accuracy for SBI benchmark recovery.
---

# Posterior Two-Sample Metrics

Use this skill when an SBI benchmark recovery needs a lightweight distributional comparison between reference posterior samples and approximate posterior samples. It is meant for bounded runs where `sklearn` is unavailable but C2ST-style evidence is still needed.

Do not use this skill to reproduce the exact paper MLP C2ST when the full `sklearn` and benchmark runtime is available. In that case, run the official metric or an equivalent library implementation and record it as the stronger evidence.

## Inputs

- JSON file with reference posterior samples.
- JSON file with approximate posterior samples.
- Optional acceptance threshold.

## Outputs

- Metric JSON with `c2st_accuracy`, `c2st_distance_to_ideal`, `mmd2`, counts, dimension, and interpretation.

## Workflow

1. Load both sample sets and validate shapes.
2. Z-score using reference-sample statistics.
3. Build a deterministic nearest-centroid classifier and evaluate it with balanced held-out folds.
4. Report balanced accuracy and its absolute distance to the ideal value `0.5`. Interpret this metric by closeness to `0.5`, not as either a larger-is-better or lower-is-better score.
5. Report squared distance between sample means as a small MMD-style diagnostic.

## Validation

Run:

```bash
python scripts/posterior_two_sample_metrics.py self-test
python tests/test_posterior_two_sample_metrics.py
```

## Limitations

The C2ST helper uses a deterministic nearest-centroid classifier, not the paper's MLP. It preserves the two-sample testing mechanism and interpretive scale for reduced recovery.
