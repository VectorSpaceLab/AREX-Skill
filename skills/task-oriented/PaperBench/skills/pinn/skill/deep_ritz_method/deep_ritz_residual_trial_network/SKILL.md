---
name: deep_ritz_residual_trial_network
description: Build smooth residual trial networks for Deep Ritz variational PDE objectives.
---

# Deep Ritz Residual Trial Network

## When To Use

Use this skill when a variational PDE solver needs a scalar neural trial function `u(x; theta)` whose spatial gradients can be differentiated. Do not use it for mesh-only PDE discretizations.

## Inputs

- Spatial dimension.
- Hidden width and residual block count.
- Activation choice, preferably cubic ReLU for Poisson-style Deep Ritz losses.
- Coordinate batch with gradient tracking enabled when a loss needs `grad_x u`.

## Outputs

- A trainable scalar model.
- Forward values shaped `[batch, 1]`.
- Input-gradient compatibility for energy losses.

## Workflow

1. Project coordinates into hidden width.
2. Apply residual blocks with two affine transformations and smooth activation.
3. Apply a final linear readout.
4. Keep the model independent of any original implementation repository.

## Validation

Run:

```bash
python tests/test_residual_network.py
```

## Limitations

The helper uses PyTorch when available. If PyTorch is unavailable, tests still validate architecture metadata and deterministic parameter counting, but recovery should record that full autograd training is blocked.
