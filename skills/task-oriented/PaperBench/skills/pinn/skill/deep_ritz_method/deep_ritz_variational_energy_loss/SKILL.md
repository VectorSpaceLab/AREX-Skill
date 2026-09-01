---
name: deep_ritz_variational_energy_loss
description: Compute Deep Ritz variational energy losses with gradient energy and boundary penalties.
---

# Deep Ritz Variational Energy Loss

## When To Use

Use this skill to turn sampled PDE points and a differentiable trial function into a Ritz objective. It is appropriate for Poisson-type energy minimization and can be extended to Rayleigh quotient eigenvalue objectives.

## Inputs

- Trial model `u(x; theta)`.
- Interior points with input gradients enabled.
- Boundary points and exact boundary values.
- Forcing function values `f(x)`.
- Boundary penalty coefficient `beta`.

## Outputs

- Scalar total loss.
- Interior energy, boundary penalty, and gradient-energy diagnostics.

## Workflow

1. Evaluate the trial function at interior points.
2. Differentiate outputs with respect to coordinates.
3. Estimate `mean(0.5 * |grad u|^2 - f * u)`.
4. Add `beta * mean((u_boundary - g_boundary)^2)`.
5. Backpropagate the resulting scalar during training.

## Validation

Run:

```bash
python tests/test_energy_loss.py
```

## Limitations

Automatic differentiation requires PyTorch or another autograd runtime. Standard-library helpers provide exact-solution functions and numeric diagnostics but cannot replace full gradient-energy training.
