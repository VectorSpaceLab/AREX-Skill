---
name: curriculum_regularization
description: Generate coefficient schedules for curriculum-regularized PINN recovery experiments.
---

# Curriculum Regularization

Use this skill when a PINN failure-mode experiment should begin with an easier PDE residual and progress to the target coefficient. Do not use it to silently change the final target coefficient.

## Inputs
- Starting coefficient, target coefficient, number of stages, and residual weight.
- Optional policy constraints for monotonicity and endpoint matching.

## Outputs
- A list of stages with `beta` and `residual_weight` fields.
- Validation metadata covering stage count, monotonicity, and target endpoint.

## Workflow
1. Choose an easy starting coefficient based on the reduced experiment.
2. Generate a deterministic monotone schedule up to the target coefficient.
3. Preserve residual weight as a separate field from the PDE coefficient.
4. Pass the schedule to the recovery harness one stage at a time.
5. Save the schedule in traces so analysis can verify curriculum execution.

## Validation
Run `python scripts/schedule.py --start 1 --target 30 --stages 5` and the tests in `tests/`.

## Limitations
The included scheduler is linear and coefficient-focused. More complex curricula may add adaptive stages, but they must keep explicit endpoint and monotonicity checks.
