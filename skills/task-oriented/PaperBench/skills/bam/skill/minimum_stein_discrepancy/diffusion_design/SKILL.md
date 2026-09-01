---
name: diffusion_design
description: Select and validate scalar diffusion factors for robust or heavy-tailed minimum Stein discrepancy estimators.
---

# Diffusion Choice For Robust Estimation

Use this skill when a Minimum Stein Discrepancy recovery needs to choose the diffusion factor used inside a Stein operator. The skill is appropriate for one-dimensional scalar proxies of the paper's diffusion choices, especially Student-t heavy-tail examples and robust decaying factors for outliers.

## Inputs
- Model family or recovery scenario: `ordinary`, `student_t_heavy_tail`, or `robust_decay`.
- Current parameter value and sample points.
- Optional hyperparameters such as scale, degrees of freedom, and decay exponent.

## Outputs
- A diffusion function or JSON table of diffusion values.
- Diagnostics: min, max, positivity, finiteness, and monotonicity checks relevant to the chosen family.
- Metadata explaining why the diffusion is mechanism-faithful for the paper.

## Workflow
1. Use `ordinary` when validating baseline Langevin KSD behavior.
2. Use `student_t_heavy_tail` for Section 4.2-style non-standardised Student-t recovery; values increase with distance from location.
3. Use `robust_decay` for Section 4.3-style corruption recovery; values decay for large absolute observations.
4. Validate all values before passing the function to a Stein-kernel loss.
5. Save the configuration and diagnostics in the recovery logs.

## Validation
Run `python tests/test_diffusion_design.py` or validate the whole skill tree with tests. The tests check positivity, finiteness, and intended directional behavior.

## Limitations
The bundled implementation returns scalar one-dimensional factors. It does not claim to validate all matrix-valued diffusion tensors in the paper.

## Refinement cycle 2 note
Robust-decay ablation confirmed outlier downweighting; recovery logs should preserve `near_value` and `far_value` when validating robust diffusions.
