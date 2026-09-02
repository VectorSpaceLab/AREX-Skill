---
name: score_sde_pc_sampler
description: Run bounded predictor-corrector reverse sampling diagnostics for score-based SDE mechanisms.
---

# Score SDE Predictor-Corrector Sampler

Use this skill to validate reverse-time SDE sampling behavior in a small recovery experiment. It should be invoked after an SDE and score function are defined.

## Inputs

- Initial scalar or vector state.
- Score function callable or oracle Gaussian score parameter.
- Number of reverse-time steps.
- Predictor step size and corrector settings.

## Outputs

- Final state and trajectory.
- Predictor and corrector invocation counts.
- Finite-value and movement diagnostics.

## Workflow

1. Initialize from a prior or deterministic proxy state.
2. Step from high time to epsilon.
3. Apply an Euler-style reverse predictor.
4. Apply Langevin-style corrector updates using the score.
5. Record every update count and final-state diagnostics.

## Validation

Run:

```bash
python tests/test_pc_sampler.py
python scripts/pc_sampler.py --initial 2.0 --steps 5 --corrector-steps 1
```

## Limitations

This skill validates sampler mechanics on tiny numeric states. It does not compute image FID or replace full pretrained sampling.
