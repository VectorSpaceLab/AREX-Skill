---
name: proxy_training_recovery
description: Run bounded proxy PINN training comparisons that exercise residual construction, NTK weighting, and optimizer updates.
---

# Proxy Training Recovery

Use this skill to produce executable recovery evidence for the NTK-PINN paper when full large-scale experiments are blocked or out of scope under soft recovery mode. The skill compares equal weighting with adaptive NTK weighting on a deterministic Poisson-style proxy.

## Inputs

- Problem item from `pinn_residual_problem`.
- NTK diagnostics from `ntk_block_spectrum`.
- Adaptive weights from `adaptive_ntk_weighting`.
- Initial scalar parameters and optimizer settings.

## Outputs

- Training trace with `params_before`, `params_after`, `loss_before`, and `loss_after`.
- Numeric comparison metric `adaptive_loss_ratio_improvement`.
- Mechanism checks showing residual loss, boundary loss, NTK traces, adaptive weights, and optimizer updates all ran.

## Workflow

1. Use the problem item to define separated boundary and residual losses.
2. Use deterministic Jacobians to compute NTK block traces and Algorithm 1 weights.
3. Run equal-weight and adaptive-weight gradient steps from the same initial parameters.
4. Measure how close the component-loss ratio is to one after training.
5. Save logs that downstream Distiller validators can inspect.

## Validation

Run:

```bash
python tests/test_proxy_training.py
```

The tests assert parameter updates, numeric losses, and improved adaptive component balance.

## Limitations

This is a soft-mode proxy and must be declared as such. It is not a full reproduction of all paper figures, but it executes the core mechanism in a bounded way.
