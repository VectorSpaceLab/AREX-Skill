---
name: particle_mirror_descent_density_metrics
description: Use this skill to score Particle Mirror Descent density approximations against reduced posterior targets with total variation, cross entropy, and symmetric mode coverage diagnostics.
---

# Posterior Density and Mode Metrics

## When To Use

Use this skill after a PMD or proxy density run has produced particles, weights, grid densities, or explicit mode locations. Do not use it to generate observations or update particles.

## Inputs

- Particle locations and normalized weights.
- Expected posterior mode coordinates and a radius for reduced mode checks.
- Optional grid target and estimated density arrays with a cell area.

## Outputs

- `total_variation` and `cross_entropy` for grid densities when available.
- Per-mode mass, mass ratio, effective sample size, and `mode_coverage_score`.
- Mechanism-check booleans suitable for recovery validation.

## Workflow

1. Confirm weights are nonnegative and normalized within numerical tolerance.
2. Accumulate particle mass inside each expected mode ball.
3. Convert balanced multimodal support into `mode_coverage_score`.
4. For grid inputs, compute total variation and cross entropy with a shared cell area.
5. Emit mechanism checks that distinguish metric success from actual PMD execution.

## Validation

Run:

```bash
python tests/test_density_metrics.py
```

## Limitations

The mode score is a reduced synthetic proxy for the paper's full figure-level total variation and cross-entropy comparisons. It should be interpreted only with the recorded PMD trace.
