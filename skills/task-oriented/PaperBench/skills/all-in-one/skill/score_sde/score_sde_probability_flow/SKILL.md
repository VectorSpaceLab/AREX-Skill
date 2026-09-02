---
name: score_sde_probability_flow
description: Compute Score SDE probability-flow drift identities and compact likelihood accounting diagnostics.
---

# Score SDE Probability Flow

Use this skill when you need deterministic probability-flow ODE drift checks or lightweight likelihood accounting for Score SDE recovery. It is designed for scalar or low-dimensional fixtures and can cross-check the SDE kernel skill.

Do not use this skill to claim the paper's CIFAR-10 bits/dim unless it is connected to a trained model, data preprocessing, ODE solver, and evaluation pipeline that match the paper.

## Inputs

- Forward drift `f(x, t)`.
- Diffusion `g(t)`.
- Score function.
- Prior log probability at terminal latent.
- Divergence values or a finite-difference divergence callback.
- Data dimension and optional offset for bits/dim.

## Outputs

- Probability-flow drift.
- Divergence estimate.
- Delta log probability.
- Negative log likelihood or bits/dim proxy.
- Identity checks comparing reverse SDE and probability-flow drifts.

## Workflow

1. Compute probability-flow drift as `f - 0.5 * g^2 * score`.
2. Estimate divergence analytically or with finite differences.
3. Accumulate a pathwise delta logp term with the chosen integration direction.
4. Combine terminal prior logp and delta logp.
5. Convert to bits/dim only when the dimensionality and offset are explicitly supplied.

## Validation

Run:

```bash
python scripts/probability_flow.py --self-test
python tests/test_probability_flow.py
```

The tests verify half-correction drift, finite-difference divergence on a linear function, and scalar likelihood accounting.

## Limitations

This skill handles mechanism-faithful diagnostics, not black-box adaptive ODE integration over image batches.
