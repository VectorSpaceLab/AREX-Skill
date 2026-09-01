---
name: imagenet_p_perturbation_metrics
description: Compute ImageNet-P-style prediction flip probability over ordered perturbation sequences.
---

# ImageNet-P Perturbation Metrics

Use this skill when evaluating prediction stability along ordered perturbation trajectories. Do not use it for corruption top-1 error or mCE calculations.

## Inputs

- Prediction sequences grouped by perturbation type, where each sequence has at least two labels.
- Optional baseline flip probabilities for normalized reporting.

## Outputs

- Flip count and transition count per sequence.
- Flip probability per perturbation type.
- Mean flip probability.
- Optional normalized flip probability.

## Workflow

1. Validate each sequence has at least two predictions.
2. Count adjacent prediction changes.
3. Divide flips by adjacent transitions for each group.
4. Average group flip probabilities.
5. Preserve per-sequence diagnostics.

## Validation

Run:

```bash
python tests/test_perturbation_metrics.py
```

## Limitations

This skill measures prediction stability only. It does not decide whether predictions are correct labels.
