---
name: stochastic_interpolant_sampler
description: Integrate bounded stochastic-interpolant probability-flow ODE and simple diffusion sampler updates from learned velocity and score fields.
---

# Stochastic Interpolant Sampler

Use this skill after velocity and score or denoiser fields have been defined. It provides bounded deterministic ODE and seeded Euler-Maruyama style SDE updates for recovery experiments.

## Inputs

- Initial scalar samples or sample summaries.
- A velocity function `b(t, x)`.
- Optional score function `s(t, x)`.
- A scalar diffusion coefficient `epsilon` and step count.
- A deterministic seed for stochastic updates.

## Outputs

- Final generated samples.
- Trajectory summaries for initial and final states.
- Solver metadata tying the result to ODE or SDE dynamics.

## Workflow

1. Use ODE mode for the main reduced recovery unless stochastic diffusion behavior is being ablated.
2. Apply Euler updates on a bounded uniform grid.
3. For SDE mode, use drift `b + epsilon*s` and seeded Gaussian increments.
4. Treat `epsilon=0` as deterministic and verify it matches ODE drift-only behavior.
5. Log step count and sample summaries for validation.

## Validation

Run:

```bash
python scripts/sampler.py --demo
python tests/test_sampler.py
```

## Limitations

The script is intentionally small and deterministic. It is not a substitute for the paper's adaptive Dormand-Prince or Heun samplers, but it preserves the probability-flow and tunable-diffusion contracts for bounded recovery.
