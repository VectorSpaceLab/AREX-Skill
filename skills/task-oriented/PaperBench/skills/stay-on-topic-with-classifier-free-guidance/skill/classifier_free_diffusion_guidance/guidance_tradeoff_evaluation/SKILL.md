---
name: guidance_tradeoff_evaluation
description: Evaluate classifier-free guidance sweeps with proxy confidence and diversity trade-off metrics.
---

# Guidance Trade-off Evaluation

Use this skill after generating samples at multiple guidance weights. It checks the paper's empirical pattern: stronger classifier-free guidance improves condition fidelity/confidence while decreasing diversity.

## Inputs
- Samples grouped by guidance weight.
- Class prototype/target mean.
- Target metadata copied from `module_plan.json`.

## Outputs
- Per-weight confidence and diversity.
- Numeric `guidance_tradeoff_score` and diagnostic booleans.

## Workflow
1. Compute confidence as inverse mean absolute distance to the class prototype.
2. Compute diversity as sample variance.
3. Check confidence is higher and diversity lower at stronger guidance than at no guidance.
4. Preserve proxy target metadata; do not overwrite it with full ImageNet metrics.

## Validation
Run tests or the Distiller skill validator.

## Limitations
Proxy confidence/diversity is only accepted in soft mode when full FID/IS recovery is blocked.
