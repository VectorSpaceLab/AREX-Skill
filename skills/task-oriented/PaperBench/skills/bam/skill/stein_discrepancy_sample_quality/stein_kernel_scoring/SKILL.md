---
name: stein_kernel_scoring
description: Compute Kernelized Stein Discrepancy pairwise Stein kernels and U/V-statistic estimates from samples, model scores, and an RBF kernel.
---

# Stein Kernel Scoring

Use this skill when implementing a goodness-of-fit or sample-quality check from Liu, Lee, and Jordan's Kernelized Stein Discrepancy paper. It is appropriate when samples are available from an unknown distribution and the candidate model can provide score values `∇ log q(x)`, but likelihood normalizers should not be evaluated.

Do not use this skill for two-sample MMD tests, likelihood-ratio tests, or cases where no differentiable score function is available.

## Inputs

- `samples`: numeric array-like data with shape `(n, d)` or one-dimensional shape `(n,)`.
- `scores`: score vectors for the same samples, or a Python callable that returns them.
- `bandwidth`: positive RBF bandwidth, or `None` to use median pairwise distance.

## Outputs

- Pairwise Stein kernel matrix for the RBF kernel.
- Unbiased U-statistic KSD estimate, excluding diagonal entries.
- V-statistic KSD diagnostic, including diagonal entries.
- Diagnostics for finite values, symmetry, and bandwidth.

## Workflow

1. Convert samples and scores to two-dimensional numeric arrays.
2. Select a positive RBF bandwidth; median-distance selection falls back to `1.0` for degenerate samples.
3. Compute the RBF Stein kernel
   `k * [s_x·s_y + s_x·(x-y)/h² + (y-x)·s_y/h² + d/h² - ||x-y||²/h⁴]`.
4. Compute U-statistic and V-statistic estimates from the pairwise matrix.
5. Report diagnostics rather than silently correcting invalid scores.

## Validation

Run:

```bash
python tests/test_stein_kernel_scoring.py
```

The tests check shape, symmetry, diagonal handling, and stronger KSD under a shifted model score.

## Limitations

- The deterministic script implements the RBF kernel only.
- The score function must already be differentiable and correctly evaluated by the caller.
- Median bandwidth is a practical experiment heuristic, not a theorem requirement.
