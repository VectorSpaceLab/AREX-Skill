---
name: conditional_flow_matching_loss
description: Compute Conditional Flow Matching squared vector-field losses and deterministic one-parameter proxy updates.
---

# Conditional Flow Matching Loss

Use this skill when a recovery or implementation needs the simulation-free CFM objective from Flow Matching: regress a model vector field against conditional target vectors sampled from a conditional path. Do not use it to construct OT path samples or to solve the CNF ODE.

## Inputs

- A batch of predicted vector fields with shape `[batch, dim]`.
- A matching batch of conditional target vectors `u_t`.
- Optional nonnegative sample weights.

## Outputs

- Mean squared CFM loss.
- Per-sample squared errors.
- A deterministic scalar-parameter update log for reduced recovery checks.

## Workflow

1. Validate batch size, dimensionality, finite values, and optional weights.
2. Use `scripts/cfm_loss.py` for loss computation or target-scaled proxy predictions.
3. For reduced recovery, use `one_parameter_update` to show an optimizer-relevant loss decrease without claiming image-scale model training.
4. Keep loss computation separate from path construction and ODE sampling.

## Validation

Run:

```bash
python tests/test_cfm_loss.py
python scripts/cfm_loss.py --targets '[[1, 2]]' --scale 0.5
```

## Limitations

This skill validates the CFM regression mechanism using deterministic vectors. It does not provide neural network layers, image data loaders, or large-scale optimization.

Cycle refinement: reduced recovery should record both loss-before and loss-after so no-update ablations are visible.
