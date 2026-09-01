---
name: quadratic_velocity_objective
description: Compute and test the simulation-free quadratic velocity objective used by stochastic interpolant flows.
---

# Quadratic Velocity Objective

Use this skill when a recovery experiment must implement the stochastic-interpolant paper mechanism without reading the original repository. Do not use it to claim full CIFAR, ImageNet, or tabular reproduction unless the corresponding real datasets and training stack actually ran.

## Inputs
- Numeric base and target samples, time samples, and velocity parameters.
- A declared full or reduced recovery target from `module_plan.json`.

## Outputs
- Deterministic numeric arrays, losses, gradients, or diagnostics depending on the module.
- JSON-compatible evidence for recovery logs.

## Workflow
1. Build or consume stochastic-interpolant samples from endpoint pairs.
2. Keep objective computation separate from ODE integration.
3. Emit explicit checks that can be validated by `recover-paper`.

## Validation
Run `python -m pytest tests` or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
The scripts are intentionally small and deterministic; they support bounded proxy recovery and are not a replacement for full neural image or tabular training.
