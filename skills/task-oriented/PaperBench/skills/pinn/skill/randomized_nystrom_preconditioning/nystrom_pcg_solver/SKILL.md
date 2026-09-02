---
name: nystrom_pcg_solver
description: Solve regularized PSD systems with randomized Nyström preconditioned conjugate gradients and log convergence evidence.
---

# Nyström PCG Solver

Use this skill to reproduce the paper's Algorithm 5.1 on a PSD linear system `(A + mu I)x=b`. It should call or mirror the generated Nyström factorization and preconditioner contracts rather than bypassing them.

## Inputs

- Dense PSD matrix or matrix-vector product interface.
- Right-hand side `b`.
- Regularization `mu > 0`.
- Sketch rank `ell`, tolerance, maximum iterations, and random seed.

## Outputs

- Approximate solution.
- Residual history, relative residual history, and iteration count.
- Mechanism diagnostics: factorization executed, preconditioner applications, CG step count, and convergence flag.

## Workflow

1. Build Nyström factors with `randomized_nystrom_factorization`.
2. Build an inverse preconditioner action with `nystrom_preconditioner`.
3. Run left-preconditioned CG using preconditioned residual inner products.
4. Optionally run ordinary CG as a baseline under the same tolerance.
5. Save traces for downstream recovery evaluation.

## Validation

Run:

```bash
python scripts/pcg.py --self-test
python tests/test_pcg.py
```

The tests use a deterministic ill-conditioned PSD system and require Nyström PCG to converge in fewer iterations than ordinary CG.

## Limitations

This dense script is designed for bounded recovery experiments. For large paper-scale systems, replace dense arrays with matvec closures while preserving the same logging contract.
