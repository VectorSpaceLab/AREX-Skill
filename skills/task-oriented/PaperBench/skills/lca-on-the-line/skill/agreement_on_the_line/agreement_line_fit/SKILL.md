---
name: agreement_line_fit
description: Fit the probit-space ID-to-OOD agreement line and report agreement-on-the-line diagnostics without OOD labels.
---

# Agreement Line Fit

Use this skill when pairwise agreement statistics are available and you need to check whether agreement-on-the-line plausibly holds.

## Inputs

- JSON statistics from `agreement_statistics`.
- Optional R² threshold.

## Outputs

- Slope, intercept, R², residual summaries, and `on_line` decision.

## Workflow

1. Align pairwise ID/OOD agreement probit values.
2. Fit ordinary least squares in probit space.
3. Compute R² and residual summaries.
4. Treat low R² as a reliability warning for downstream OOD accuracy estimates.

## Validation

Run `python tests/test_agreement_line_fit.py` from this skill directory.

## Limitations

The line diagnostic is unlabeled; it cannot prove true OOD accuracy without a separate evaluation harness.
