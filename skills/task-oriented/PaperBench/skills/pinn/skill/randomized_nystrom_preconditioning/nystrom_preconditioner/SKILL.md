---
name: nystrom_preconditioner
description: Build and apply the inverse action of the Nyström preconditioner for regularized PSD linear systems.
---

# Nyström Preconditioner

Use this skill after obtaining `U, lambda_hat` from a randomized Nyström factorization. It provides the inverse preconditioner action used by Nyström PCG and dense diagnostics for small recovery experiments.

## Inputs

- `U`: orthonormal Nyström basis.
- `lambda_hat`: nonnegative approximate eigenvalues.
- `mu > 0`: regularization parameter.
- Residual vector or right-hand-side matrix.

## Outputs

- `apply_inverse_preconditioner(U, lambda_hat, mu, r)` result.
- Preconditioner metadata, including rank and baseline scale.
- Optional condition-number comparison for `A + mu I` versus the symmetrically preconditioned matrix.

## Workflow

1. Validate dimensions, `mu`, and approximate orthonormality.
2. Sort eigenpairs by decreasing `lambda_hat` if necessary.
3. Set `sigma = lambda_hat[-1] + mu`.
4. Apply `P^{-1}` by scaling captured components with `sigma / (lambda_hat_i + mu)` and leaving orthogonal components unchanged.
5. For dense recovery checks, construct the SPD square-root action and estimate condition numbers.

## Validation

Run:

```bash
python scripts/preconditioner.py --self-test
python tests/test_preconditioner.py
```

The tests verify inverse-action shape, dimension checks, and condition-number reduction on a diagonal PSD example.

## Limitations

Dense condition-number diagnostics are intended for small experiments. Large systems should only use the vector action.
