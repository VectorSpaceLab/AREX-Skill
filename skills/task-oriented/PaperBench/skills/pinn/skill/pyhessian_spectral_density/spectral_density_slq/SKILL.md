---
name: spectral_density_slq
description: Builds a Lanczos tridiagonal matrix from HVP calls and extracts eigenvalue-weight pairs as a compact ESD proxy.
---

# Spectral Density via Lanczos Quadrature

Use this skill when a recovery or analysis task needs the PyHessian paper component described by this module. Do not use it to read or depend on the original PyHessian repository during recovery; the scripts are self-contained reduced implementations or contract checkers.

## Inputs
- Hessian-vector product callable
- Initial probe vector
- Lanczos iteration count

## Outputs
- Lanczos alpha/beta coefficients
- Approximate spectral eigenvalues and quadrature weights

## Workflow
1. Confirm that the requested experiment matches this module contract.
2. Use the script in `scripts/slq_density.py` for deterministic checks or as reference logic.
3. Preserve the paper mechanism: The ESD can be approximated from stochastic Lanczos quadrature, matching the paper’s full spectral-density mechanism without dense Hessian construction.
4. Write numeric evidence and avoid qualitative-only conclusions.
5. In recovery, record whether this skill was called, imported, or cross-checked.

## Validation
Run `python` through the Distiller skill-tree validator with `--run-tests`, or run the test file in `tests/` with the repository-independent Python path pointing at this skill's `scripts/` directory.

## Limitations
This generated skill captures reusable mechanism semantics. It is not a drop-in replacement for the original PyTorch package and does not authorize recovery to read the original repository.
