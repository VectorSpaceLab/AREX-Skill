---
name: gated_pinn_architecture
description: Build a lightweight gated PINN-style scalar model that exposes trainable parameters and gradient paths for reduced recovery experiments.
---

# Gated PINN Architecture

Use this skill when a PINN recovery wants to exercise the paper's improved architecture idea or compare it with a plain parameterization. The standard-library implementation is intentionally small for bounded recovery; full experiments may replace it with a neural-network library implementation.

## Inputs

- Basis feature count or hidden width.
- Initialization seed.
- Whether to use gated feature mixing.

## Outputs

- Trainable model parameters.
- Forward predictions for coordinate points.
- Parameter count and serializable state.

## Workflow

1. Create sinusoidal Helmholtz-like basis functions.
2. Add trainable weights and optional gate scalars that mix coordinate transforms.
3. Expose prediction and finite-difference/free analytic derivatives needed by the loss module.
4. Return parameter snapshots before and after optimization.

## Validation

Run `python scripts/gated_model.py --self-test` or the skill-tree tests.
