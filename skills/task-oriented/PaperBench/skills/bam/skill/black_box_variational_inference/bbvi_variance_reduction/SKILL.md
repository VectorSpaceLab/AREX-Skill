---
name: bbvi_variance_reduction
description: Compute BBVI Rao-Blackwellized and score-function control-variate gradient estimators with variance diagnostics.
---

# BBVI Variance Reduction

## When To Use

Use this skill after forming BBVI score-function terms when you can identify local model terms for a variational factor or want to apply the paper's score-function control variate. It preserves black-box behavior because it requires only local log-density values and score functions.

Do not use it to update parameters or to claim variance reduction without numeric diagnostics.

## Inputs

- `score`: sample-by-parameter score values for one variational factor.
- `local_signal`: per-sample local learning signal for that factor.
- `full_signal`: optional per-sample full learning signal for naive comparison.

## Outputs

- `rao_blackwell_terms` and `rao_blackwell_estimate`.
- `control_variate_scale` and `control_variate_estimate`.
- `variance`: naive, Rao-Blackwellized, and control-variate empirical variances.
- `variance_reduction_ratio`: naive variance divided by control-variate variance when available.

## Workflow

1. Normalize scores and validate sample counts.
2. Compute Rao-Blackwellized local terms as `score * local_signal`.
3. Estimate the control-variate scale by aggregated covariance divided by aggregated score variance.
4. Compute corrected terms as local terms minus `a_hat * score`.
5. Report variance diagnostics over per-sample term norms.

## Validation

Run:

```bash
python tests/test_variance_reduction.py
```

## Limitations

The caller must supply valid local terms. This skill does not infer a Markov blanket from an arbitrary model graph.
