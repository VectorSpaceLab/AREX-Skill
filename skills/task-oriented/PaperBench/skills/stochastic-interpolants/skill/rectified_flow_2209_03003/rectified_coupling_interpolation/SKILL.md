---
name: rectified_coupling_interpolation
description: Build rectified-flow coupling interpolation records with endpoint displacement targets for velocity regression.
---

# Rectified Coupling Interpolation

Use this skill when a recovery or implementation needs supervised training tuples for rectified flow. Do not use it to fit the velocity model or evaluate transport quality.

## Inputs
- Equal-length source samples `x0` and target samples `x1`, each a list of numeric vectors.
- One scalar time per pair in `[0, 1]`.

## Outputs
- Records containing `x0`, `x1`, `t`, `xt`, and `target_velocity`.
- Validation errors for mismatched counts, dimensions, or invalid times.

## Workflow
1. Validate equal sample counts and vector dimensions.
2. Compute `xt = (1 - t) * x0 + t * x1` for each pair.
3. Compute `target_velocity = x1 - x0`.
4. Preserve endpoint provenance for transport-cost diagnostics.

## Validation
Run `python tests/test_interpolation.py` or the Distiller skill-tree validator with `--run-tests`.

## Limitations
This skill prepares the regression dataset only; it does not sample real image data, train a model, or claim recovery success.
