---
name: reduced_recovery_evaluation
description: Packages reduced recovery evidence, source-boundary checks, mechanism checks, metrics, and validation-ready logs.
---

# Reduced Recovery Evaluation

Use this skill when a recovery or analysis task needs the PyHessian paper component described by this module. Do not use it to read or depend on the original PyHessian repository during recovery; the scripts are self-contained reduced implementations or contract checkers.

## Inputs
- Experiment command log
- Generated skill invocation records
- Curvature metrics and training trace
- Runtime handoff and source manifest

## Outputs
- Validator-compatible recovery_result.json fields
- Analysis-ready gap and acceptance summary

## Workflow
1. Confirm that the requested experiment matches this module contract.
2. Use the script in `scripts/recovery_contract.py` for deterministic checks or as reference logic.
3. Preserve the paper mechanism: Soft-mode recovery can be valid only when it declares the proxy, records executable evidence, and demonstrates the paper mechanism numerically.
4. Write numeric evidence and avoid qualitative-only conclusions.
5. In recovery, record whether this skill was called, imported, or cross-checked.

## Validation
Run `python` through the Distiller skill-tree validator with `--run-tests`, or run the test file in `tests/` with the repository-independent Python path pointing at this skill's `scripts/` directory.

## Limitations
This generated skill captures reusable mechanism semantics. It is not a drop-in replacement for the original PyTorch package and does not authorize recovery to read the original repository.
