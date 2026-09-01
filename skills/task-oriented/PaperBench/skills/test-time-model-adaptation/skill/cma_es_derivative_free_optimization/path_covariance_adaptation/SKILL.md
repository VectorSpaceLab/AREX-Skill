---
name: path_covariance_adaptation
description: Update CMA-ES cumulative step-size paths and covariance matrix from selected normalized steps.
---

# CSA and Covariance Adaptation

Use this skill after a CMA-ES generation has produced selected normalized steps. It updates the sigma evolution path, global step-size, covariance evolution path, and covariance matrix.

## Inputs
- Current `p_sigma`, `p_c`, `sigma`, covariance matrix, weighted step `y_w`, selected `y` vectors, selected `z` vectors, and strategy parameters.

## Outputs
- Updated paths, sigma, covariance, eigenvalues, condition number, and booleans showing whether sigma and covariance changed.

## Workflow
1. Update the isotropic path from selected `z` steps.
2. Compare its norm to the expected norm of a standard normal vector and update sigma on the log scale.
3. Update the covariance path from the weighted `y` step.
4. Apply rank-one and rank-mu covariance terms, symmetrize, and floor eigenvalues for numerical safety.

## Validation
Run the included tests or `validate_skill_tree.py --run-tests`.

## Limitations
The reduced recovery uses positive recombination weights; active negative weights are not required for the selected proxy target.
