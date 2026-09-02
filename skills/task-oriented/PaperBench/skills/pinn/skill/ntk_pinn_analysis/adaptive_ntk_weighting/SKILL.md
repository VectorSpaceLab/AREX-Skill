---
name: adaptive_ntk_weighting
description: Compute Algorithm 1 PINN loss weights from NTK trace ratios with degeneracy checks and diagnostics.
---

# Adaptive NTK Weighting

Use this skill after computing PINN NTK block traces. It implements the trace-ratio weighting rule proposed for calibrating convergence rates of different loss components.

## Inputs

- `trace_full`: trace of the combined boundary-plus-residual NTK.
- `trace_kuu`: boundary-output kernel trace.
- `trace_krr`: residual-operator kernel trace.
- Optional epsilon for rejecting degenerate traces.

## Outputs

- `lambda_b = trace_full / trace_kuu`.
- `lambda_r = trace_full / trace_krr`.
- A diagnostic indicating which component receives the stronger weight.

## Workflow

1. Validate traces are finite and nonnegative.
2. Reject component traces below epsilon instead of silently dividing by zero.
3. Compute trace-ratio weights exactly as Algorithm 1 states.
4. Preserve component names so a recovery harness applies weights to the correct losses.

## Validation

Run:

```bash
python tests/test_adaptive_weights.py
```

The tests verify the paper's ratio formulas and that the smaller-trace component receives a larger weight.

## Limitations

The skill does not tune learning rates or batch sizes. It only computes the NTK-based loss weights used by a downstream training loop.
