---
name: score_sde_reverse_sampling
description: Run reduced reverse-time SDE, probability-flow, and predictor-corrector sampling updates for Score SDE.
---

# Score SDE Reverse Sampling

Use this skill when you need an executable reduced sampler that follows the Score SDE reverse-time mechanism. It consumes SDE drift/diffusion callbacks and a score function; it does not depend on the original paper repository.

Do not use this skill to claim full image generation quality. It is a compact sampler for validating reverse SDE and predictor-corrector mechanics.

## Inputs

- Initial state from a prior or supplied latent value.
- Descending times from `T` to `eps`.
- Drift and diffusion callbacks from a forward SDE.
- Score callback.
- Predictor mode: Euler-Maruyama or probability flow.
- Corrector settings: number of Langevin steps, step size, optional noise seed.

## Outputs

- Final state and trajectory.
- Score evaluation count.
- Predictor/corrector update diagnostics.
- Flags indicating stochastic or deterministic operation.

## Workflow

1. Build a `SamplerConfig`.
2. Call `run_sampler` with callbacks for drift, diffusion, and score.
3. Use `probability_flow=True` for deterministic ODE-style updates.
4. Use `corrector_steps > 0` to add Langevin correction before each predictor step.
5. Save the trajectory and score-call count as recovery evidence.

## Validation

Run:

```bash
python scripts/reverse_sampling.py --self-test
python tests/test_reverse_sampling.py
```

The tests check deterministic probability-flow behavior, finite stochastic updates, and corrector movement under a controlled score.

## Limitations

The sampler is intentionally low-dimensional and standard-library only. Full PC sampling for images requires neural model replicas, device mapping, denoising options, and dataset scalers outside this skill.
