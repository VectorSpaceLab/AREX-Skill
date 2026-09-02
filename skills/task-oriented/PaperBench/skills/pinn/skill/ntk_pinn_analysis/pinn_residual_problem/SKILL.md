---
name: pinn_residual_problem
description: Build deterministic PINN residual problem fixtures with boundary and PDE residual targets for NTK recovery experiments.
---

# PINN Residual Problem

Use this skill when a recovery task needs an explicit physics-informed neural network problem item rather than a generic regression dataset. It is appropriate for small Poisson-style probes, source-boundary checks, and module tests that need separated boundary and residual loss contracts.

Do not use this skill to claim a full paper benchmark. The default fixture is a declared synthetic proxy designed to exercise the paper mechanism.

## Inputs

- `frequency`: positive integer or float for `u(x)=sin(frequency*pi*x)`.
- `residual_points`: interior collocation points in `[0, 1]`.
- Optional boundary points, defaulting to `[0, 1]`.

## Outputs

- A JSON-compatible problem dictionary with `boundary_points`, `boundary_targets`, `residual_points`, `residual_targets`, and `operator`.
- Residual targets follow the Poisson second-derivative convention `u_xx(x) = -(frequency*pi)^2 sin(frequency*pi*x)`.

## Workflow

1. Choose a deterministic set of boundary and residual points.
2. Compute exact solution values and second-derivative forcing values.
3. Validate that arrays are non-empty, finite, and aligned.
4. Pass the problem dictionary to NTK diagnostics or proxy training.

## Validation

Run:

```bash
python tests/test_poisson_problem.py
```

The tests verify endpoint boundary values, residual sign, finite values, and metadata needed by downstream recovery.

## Limitations

The fixture is intentionally small and synthetic. It preserves the paper's residual-plus-boundary loss mechanism but does not reproduce full-width neural network training or all numerical experiments.
