---
name: weaning_schedule
description: Compute QDagger teacher-distillation coefficient schedules for weaning a value student off a suboptimal teacher.
---

# Weaning Schedule

## When To Use

Use this skill when a PVRL or QDagger implementation needs the current coefficient on teacher-policy distillation. It is specifically for methods that should reduce teacher dependence over training. Do not use a fixed positive coefficient when the experiment claims QDagger-style weaning.

## Inputs

- `lambda_0`: initial nonnegative teacher-distillation coefficient.
- Linear schedule inputs: `step` and `decay_steps`.
- Performance schedule inputs: `student_score` and `teacher_score`.

## Outputs

- `lambda_t`: current nonnegative coefficient.
- `progress`: clipped progress or performance ratio.
- `schedule`: selected schedule type.

## Workflow

1. Choose `linear_decay` for step-based experiments or `performance_decay` when student and teacher scores are available.
2. Clip progress to `[0, 1]`.
3. Return `lambda_0 * (1 - progress)`.
4. Record the schedule diagnostics in recovery traces.

## Validation

Run:

```bash
python scripts/weaning_schedule.py --self-test
python tests/test_weaning_schedule.py
```

## Limitations

The skill only computes coefficients. It does not decide when a teacher query is available or evaluate the RL policy.
