---
name: conditional_flow_matching_objective
description: Build conditional flow matching interpolation states, target velocities, and squared regression losses for bounded CNF recovery experiments.
---

# Conditional Flow Matching Objective

Use this skill when a recovery experiment or implementation needs the simulation-free CFM training target from the paper. Do not use it as an ODE sampler or as a replacement for evaluating a trained continuous normalizing flow.

## Inputs
- Matched source and target point arrays `x0` and `x1` with the same shape.
- One scalar time or one time per sample in `[0, 1]`.
- A candidate vector-field prediction array with the same shape when computing loss.

## Outputs
- Interpolated states `x_t = (1 - t) x0 + t x1`.
- Target velocities `u_t = x1 - x0` for the deterministic linear path.
- Mean squared velocity-regression loss and per-sample losses.

## Workflow
1. Validate that source and target arrays have identical batch and feature dimensions.
2. Broadcast scalar time values or validate one time per sample.
3. Construct linear conditional path samples and displacement targets.
4. Compare predicted velocities against targets with squared error.
5. Log whether smoothing/noise was omitted when using a reduced deterministic proxy.

## Validation
Run `python tests/test_cfm_objective.py` from this skill directory, or validate the tree with the Distiller `validate_skill_tree.py --run-tests` command.

## Limitations
This skill implements the deterministic mean-path target used by I-CFM and OT-CFM proxy experiments. It does not perform neural ODE integration, density evaluation, or stochastic Gaussian path sampling.
