---
name: clip_power_law_scaling
description: Fit log-log power laws for CLIP downstream error metrics over compute or scale points.
---

# CLIP Power-Law Scaling

Use this skill to fit the paper's central relation: error-like downstream metrics decrease as a power of total compute or scale.

## Inputs
- Records with positive `total_compute` and a positive error metric column.
- Optional frontier selection flag.

## Outputs
- Coefficient, exponent, log-space R2, predictions, and residuals.

## Workflow
1. Filter or validate positive compute/error points.
2. Optionally keep the best-so-far decreasing error frontier.
3. Fit `log(error) = intercept + exponent * log(total_compute)`.
4. Convert intercept to coefficient and report R2.
5. Require a negative exponent for successful scaling-improvement evidence.

## Validation
Run `python tests/test_power_law_scaling.py`.

## Limitations
The fit is descriptive and depends on the supplied scale table; this skill does not establish full paper-level performance by itself.
