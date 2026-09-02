---
name: budget_scheduler
description: Schedule AdaLoRA global rank budgets with warmup, cubic decay, mask intervals, and final fixed allocation.
---

# Global Budget Scheduler

Use this skill when implementing AdaLoRA's gradual budget reduction and deciding when rank masks should be applied.

## Inputs

- Current step and total training steps.
- Initial warmup and final warmup lengths.
- Initial total rank and target total rank.
- Mask interval.

## Outputs

- Current rank budget.
- `mask` boolean indicating whether to apply rank masking at this step.

## Workflow

1. Validate that total steps exceed initial plus final warmup and that the target rank is no larger than the initial rank.
2. Return the full initial rank during initial warmup with no masking.
3. In the decay phase, compute `target + (initial-target) * (1-progress)^3` and mask only on interval steps.
4. In final warmup, return the target rank and keep masking enabled so the final rank pattern remains fixed.

## Validation

Run `python scripts/budget_schedule.py --self-test` or the generated tests.

## Limitations

The schedule handles integer rank budgets. It does not choose target budgets; those are experiment hyperparameters from the recovery plan.
