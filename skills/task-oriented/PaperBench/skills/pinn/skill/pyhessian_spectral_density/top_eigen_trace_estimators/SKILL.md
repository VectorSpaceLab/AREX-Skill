---
name: top_eigen_trace_estimators
description: Implements power iteration and Hutchinson trace estimation over an HVP oracle for fast curvature summaries.
---

# Top Eigenvalue and Trace Estimators

Use this skill when a recovery or analysis task needs the PyHessian paper component described by this module. Do not use it to read or depend on the original PyHessian repository during recovery; the scripts are self-contained reduced implementations or contract checkers.

## Inputs
- Hessian-vector product callable
- Parameter dimension
- Iteration limits, tolerance, and deterministic probe policy

## Outputs
- Estimated top eigenvalue and vector
- Trace probe values and trace estimate

## Workflow
1. Confirm that the requested experiment matches this module contract.
2. Use the script in `scripts/estimators.py` for deterministic checks or as reference logic.
3. Preserve the paper mechanism: Power iteration and randomized trace probing preserve the paper mechanism for scalable second-order summaries.
4. Write numeric evidence and avoid qualitative-only conclusions.
5. In recovery, record whether this skill was called, imported, or cross-checked.

## Validation
Run `python` through the Distiller skill-tree validator with `--run-tests`, or run the test file in `tests/` with the repository-independent Python path pointing at this skill's `scripts/` directory.

## Limitations
This generated skill captures reusable mechanism semantics. It is not a drop-in replacement for the original PyTorch package and does not authorize recovery to read the original repository.
