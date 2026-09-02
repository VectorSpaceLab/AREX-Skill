---
name: predictor_corrector_sampling
description: Execute bounded reverse predictor-corrector sampling checks for score-SDE mechanism-faithful recovery.
---

# Predictor-Corrector Sampling

Use this skill when a score-SDE recovery must exercise reverse-dynamics sampling rather than only a training loss. It implements a deterministic scalar predictor-corrector loop that logs every reverse predictor and score-based corrector update.

## Inputs
- Initial scalar latent state.
- Strictly decreasing time grid.
- Score function parameters for `score(x)=a*x+c` or an injected callable.
- Predictor step scale and corrector step size.

## Outputs
- Ordered trajectory entries for predictor and corrector phases.
- Final sample value.
- Mechanism checks showing both phases executed.

## Workflow
1. Validate the time grid is decreasing.
2. At each interval, evaluate the score and make a reverse predictor step.
3. Apply a corrector step in the score direction.
4. Append diagnostics for phase, time, state, score, and update.
5. Return the trajectory for recovery logs or tests.

## Validation
Run `python scripts/predictor_corrector_sampling.py --self-test` or the generated skill validator with tests enabled.

## Limitations
This scalar implementation is a mechanism check. It does not produce image samples or estimate FID.
