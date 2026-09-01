---
name: pinn_recovery_evaluation
description: Convert PINN traces into numeric proxy metrics and mechanism checks for validator-ready recovery evidence.
---

# PINN Recovery Evaluation

Use this skill after a PINN experiment command has produced a data item, training trace, and generated-skill invocation evidence. It decides whether the trace proves the declared full or reduced target. Do not use it to train the model or compute PDE derivatives.

## Inputs
- Module-plan target metadata.
- Training trace with loss components and before/after parameters.
- Data item and source-manifest metadata.
- Generated-skill invocation evidence.

## Outputs
- Numeric metrics such as `loss_reduction` and `relative_loss_reduction`.
- Mechanism checks covering data construction, residual computation, composite loss, optimizer update, source boundary, and reduced/full runtime status.
- Recovery-result fields aligned with `module_plan.json.fast_recovery_target`.

## Workflow
1. Load the training trace and compute loss-reduction metrics.
2. Confirm parameter or optimizer-state change evidence.
3. Build mechanism checks for all claimed modules.
4. Preserve target metadata exactly from the module plan.
5. Emit validator-compatible recovery fields.

## Validation
Run `python tests/test_recovery_evaluation.py` or validate with the Distiller skill validator.

## Limitations
This skill accepts reduced recovery only when mechanism checks are explicit. Full paper-scale claims require separate runtime evidence.
