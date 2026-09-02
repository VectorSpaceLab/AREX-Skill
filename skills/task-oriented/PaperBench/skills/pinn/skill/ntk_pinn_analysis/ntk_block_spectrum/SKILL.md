---
name: ntk_block_spectrum
description: Compute PINN neural tangent kernel block traces, eigenvalue summaries, and dominance diagnostics from empirical Jacobians.
---

# NTK Block Spectrum

Use this skill when a PINN recovery task needs to diagnose convergence-rate imbalance between boundary and residual loss components. It implements the paper's block-kernel view with small deterministic arrays.

## Inputs

- Boundary Jacobian `J_u` as rows over boundary observations and columns over parameters.
- Residual Jacobian `J_r` as rows over residual observations and columns over the same parameters.
- Optional dominance tolerance.

## Outputs

- `trace_kuu`, `trace_krr`, and `trace_full`.
- Eigenvalue lists for `Kuu` and `Krr`.
- Dominance label: `residual_dominates`, `boundary_dominates`, or `balanced`.

## Workflow

1. Validate that both Jacobians are non-empty matrices with equal parameter dimension.
2. Compute Gram blocks `Kuu = J_u J_u^T` and `Krr = J_r J_r^T`.
3. Compute traces and symmetric eigenvalues.
4. Compare block traces and record which loss component is expected to converge faster.
5. Pass the diagnostics to the adaptive weighting skill.

## Validation

Run:

```bash
python tests/test_ntk_spectrum.py
```

The tests use residual-dominant Jacobians and check trace, eigenvalue, and label behavior.

## Limitations

This skill computes empirical finite-width diagnostics. It does not prove infinite-width convergence; it preserves the operational recovery mechanism needed for bounded experiments.
