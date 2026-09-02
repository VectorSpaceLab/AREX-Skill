---
name: integrated_gradient_computation
description: Compute Integrated Gradients with Riemann-summed path gradients and completeness diagnostics for attribution recovery.
---

# Integrated Gradient Computation

Use this skill to compute feature attributions from a differentiable scalar function or from an injected gradient callable. Do not use plain input gradients as a substitute for Integrated Gradients when the function may be saturated at the input.

## Inputs
- `gradient_fn(point)`: returns one gradient value per feature.
- `input_vector` and `baseline_vector`: equal-length numeric vectors.
- `steps`: Riemann approximation count, typically 20 to 300 for real models.
- Optional `output_fn` for completeness diagnostics.

## Outputs
- `attributions`: one attribution per input feature.
- `attribution_sum`: sum of feature attributions.
- Optional `output_difference` and `completeness_error`.

## Workflow
1. Generate the straight-line path from baseline to input.
2. Evaluate gradients at each interpolation point.
3. Average gradients per feature.
4. Multiply averaged gradients by the input-baseline feature deltas.
5. If an output function is provided, compare the attribution sum to `F(x)-F(baseline)`.

## Validation
Run `python tests/test_integrated_gradients.py` or the Distiller skill-tree validator with tests enabled.

## Limitations
The script expects deterministic Python callables. Framework-specific autograd wrappers should adapt their tensors to this callable interface.
