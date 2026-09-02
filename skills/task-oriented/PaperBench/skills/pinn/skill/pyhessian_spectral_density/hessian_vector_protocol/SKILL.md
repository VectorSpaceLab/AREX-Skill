---
name: hessian_vector_protocol
description: Defines model, loss, parameter, gradient, and Hessian-vector product contracts for PyHessian-style curvature analysis.
---

# Hessian Vector Product Protocol

Use this skill when a recovery or analysis task needs the PyHessian paper component described by this module. Do not use it to read or depend on the original PyHessian repository during recovery; the scripts are self-contained reduced implementations or contract checkers.

## Inputs
- Parameterized objective or model/criterion batch
- Parameter vector or grouped parameter tensors
- Probe vector matching the parameter structure

## Outputs
- Hessian-vector product with the same structure as the probe
- Scalar Rayleigh quotient helper for v^T H v

## Workflow
1. Confirm that the requested experiment matches this module contract.
2. Use the script in `scripts/curvature_core.py` for deterministic checks or as reference logic.
3. Preserve the paper mechanism: The paper avoids materializing the Hessian by computing Hessian-vector products, which are sufficient for downstream eigenvalue, trace, and spectral-density estimators.
4. Write numeric evidence and avoid qualitative-only conclusions.
5. In recovery, record whether this skill was called, imported, or cross-checked.

## Validation
Run `python` through the Distiller skill-tree validator with `--run-tests`, or run the test file in `tests/` with the repository-independent Python path pointing at this skill's `scripts/` directory.

## Limitations
This generated skill captures reusable mechanism semantics. It is not a drop-in replacement for the original PyTorch package and does not authorize recovery to read the original repository.
