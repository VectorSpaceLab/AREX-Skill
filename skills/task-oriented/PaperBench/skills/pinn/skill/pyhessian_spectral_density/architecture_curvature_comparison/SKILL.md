---
name: architecture_curvature_comparison
description: Compares curvature metrics across architecture-style variants and records qualitative sharper/flatter conclusions.
---

# Architecture Curvature Comparison

Use this skill when a recovery or analysis task needs the PyHessian paper component described by this module. Do not use it to read or depend on the original PyHessian repository during recovery; the scripts are self-contained reduced implementations or contract checkers.

## Inputs
- Curvature summaries for baseline and ablated variants
- Variant metadata describing residual or normalization changes

## Outputs
- Ranked curvature comparison
- Mechanism checks for top eigenvalue, trace, ESD range, and qualitative direction

## Workflow
1. Confirm that the requested experiment matches this module contract.
2. Use the script in `scripts/compare_curvature.py` for deterministic checks or as reference logic.
3. Preserve the paper mechanism: The paper’s scientific use case is not merely computing Hessians, but comparing BN and residual ablations by curvature diagnostics.
4. Write numeric evidence and avoid qualitative-only conclusions.
5. In recovery, record whether this skill was called, imported, or cross-checked.

## Validation
Run `python` through the Distiller skill-tree validator with `--run-tests`, or run the test file in `tests/` with the repository-independent Python path pointing at this skill's `scripts/` directory.

## Limitations
This generated skill captures reusable mechanism semantics. It is not a drop-in replacement for the original PyTorch package and does not authorize recovery to read the original repository.
