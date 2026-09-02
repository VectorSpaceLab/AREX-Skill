---
name: randomized_nystrom_factorization
description: Compute a stable randomized Nyström PSD low-rank eigendecomposition from a dense PSD matrix or matrix-vector product interface.
---

# Randomized Nyström Factorization

Use this skill when you need the paper's Algorithm 2.1 component: a reproducible low-rank PSD approximation `A_nys = U diag(lambda_hat) U.T` for a symmetric positive-semidefinite matrix. Do not use it as a full linear solver; downstream solver skills own preconditioning and PCG.

## Inputs

- PSD matrix `A` as a dense JSON/NumPy array, or a Python callable that applies `A` to a matrix.
- Dimension `n` and sketch rank `ell`, with `1 <= ell <= n`.
- Random seed for reproducibility.

## Outputs

- `U`: orthonormal basis for the Nyström range.
- `lambda_hat`: nonnegative approximate eigenvalues.
- Diagnostics: sketch rank, returned rank, stability shift, matvec count, and Cholesky retry count.

## Workflow

1. Validate matrix dimensions and rank.
2. Draw a standard Gaussian sketch and orthonormalize it with thin QR.
3. Form `Y = A @ Omega`; this is the only matrix interaction required by the algorithm.
4. Add a tiny stability shift `nu * Omega` before Cholesky.
5. Factor `Omega.T @ Y_shift`, solve by the Cholesky factor, and take a thin SVD.
6. Return `U` and squared singular values minus the stability shift, clipped at zero for roundoff.

## Validation

Run:

```bash
python scripts/nystrom.py --self-test
python tests/test_nystrom.py
```

The tests verify shapes, orthonormality, nonnegative eigenvalues, deterministic seeding, and improved approximation with larger rank.

## Limitations

The routine assumes PSD-compatible input. It is intentionally small and dense-friendly for recovery experiments; large production runs should provide an efficient matvec closure and avoid forming dense matrices.
