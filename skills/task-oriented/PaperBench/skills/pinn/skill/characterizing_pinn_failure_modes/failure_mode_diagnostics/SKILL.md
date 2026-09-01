---
name: failure_mode_diagnostics
description: Diagnose PINN failure-mode recovery runs with relative errors and optimizer progress checks.
---

# Failure Mode Diagnostics

Use this skill when comparing PINN predictions or reduced proxy outputs to a target field. It is especially useful for deciding whether a run shows high-error soft-constraint failure or improvement from a proposed remedy.

## Inputs
- Prediction and target arrays with matching shapes.
- Optional loss traces from vanilla or curriculum optimization.
- Relative-error thresholds for reduced recovery acceptance.

## Outputs
- Relative L2 error and absolute L2 error.
- Boolean flags for high relative error, finite loss trace, and loss improvement.
- A concise text summary for recovery and analysis reports.

## Workflow
1. Flatten prediction and target arrays while preserving numeric values.
2. Compute relative L2 error using a guarded target norm.
3. Compute root-mean-square absolute L2 error.
4. Check whether recorded losses are finite and improve.
5. Report metrics without claiming full reproduction unless the recovery target says so.

## Validation
Run the tests in `tests/`; they check exact, shifted, and constant predictions.

## Limitations
These diagnostics do not explain every loss-landscape property from the paper. They provide bounded executable evidence for recovery gating and refinement decisions.
