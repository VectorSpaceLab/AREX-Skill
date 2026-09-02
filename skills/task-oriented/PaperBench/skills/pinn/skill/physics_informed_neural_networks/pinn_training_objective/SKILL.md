---
name: pinn_training_objective
description: Combine PINN supervised and residual losses and execute bounded optimizer updates with validator-compatible traces.
---

# PINN Training Objective

Use this skill to turn a PDE problem item and residual function into a trainable PINN objective. It is appropriate for bounded recovery, smoke tests, and reduced experiments that must prove parameter updates. Do not use it to evaluate final acceptance without the recovery-evaluation skill.

## Inputs
- PDE problem item containing observations and collocation points.
- Trainable surrogate parameters.
- Residual function compatible with the PDE.
- Learning rate and loss weights.

## Outputs
- Data loss, residual loss, and total loss before and after optimization.
- `params_before` and `params_after` for recovery validators.
- Boolean evidence that an optimizer step changed parameters.

## Workflow
1. Compute mean-squared observation error.
2. Compute mean-squared PDE residual over collocation points.
3. Sum weighted components into the PINN objective.
4. Estimate gradients by deterministic finite differences for this tiny reduced surrogate.
5. Apply one or more bounded gradient-descent steps and record the trace.

## Validation
Run `python tests/test_training_objective.py` or validate via `validate_skill_tree.py --run-tests`.

## Limitations
The bundled optimizer is intentionally small and deterministic. It is mechanism-faithful for reduced recovery but not a claim of full paper-scale training.
