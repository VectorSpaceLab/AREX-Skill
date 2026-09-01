---
name: imagenet_c_corruption_metrics
description: Compute ImageNet-C CE, mCE, relative CE, and relative mCE from clean and corrupted top-1 error tables.
---

# ImageNet-C Corruption Metrics

Use this skill when evaluating corruption robustness from top-1 error rates indexed by corruption type and severity. Use it for ImageNet-C or reduced experiments that preserve the same normalization equations. Do not use it for ImageNet-P perturbation stability metrics.

## Inputs

- Model errors: `{corruption: {severity: top1_error}}`.
- Baseline errors with the same corruption/severity keys.
- Model clean top-1 error.
- Baseline clean top-1 error.
- Optional scale factor, normally `100.0`.

## Outputs

- `ce_by_corruption`.
- `mce`.
- `relative_ce_by_corruption`.
- `relative_mce`.
- Validation diagnostics.

## Workflow

1. Validate matching corruption names and five severity levels.
2. Sum model and baseline errors across severities for each corruption.
3. Compute CE as `scale * model_sum / baseline_sum`.
4. Average CE values to get mCE.
5. Compute relative CE after subtracting clean error from each severity error.
6. Average relative CE values to get relative mCE.

## Validation

Run:

```bash
python tests/test_corruption_metrics.py
```

## Limitations

The script assumes error rates are already computed from predictions and labels. It does not run an image classifier.
