---
name: annealed_langevin_sampler
description: Run annealed Langevin dynamics with composed scores for F-NPSE or PF-NPSE posterior sampling.
---

# Annealed Langevin Sampler

Use this skill when a recovery needs to sample from a posterior approximation using a score function already composed from F-NPSE or PF-NPSE terms. It implements the paper's Algorithm 1 in a bounded, deterministic-seeded form suitable for tests and recovery harnesses.

Do not use this skill to train score networks or to define the F-NPSE algebra. It consumes a callable score and a reference sampler.

## Inputs

- Initial samples from the high-noise reference distribution, or a reference sampler.
- Composed score callable `score(theta, t)`.
- Time levels ordered from high noise to low noise.
- Step size, Langevin steps per level, and random seed.

## Outputs

- Final posterior samples.
- Trace metadata with score norms, sample means, level count, step size, and seed.

## Workflow

1. Initialize samples from the reference distribution.
2. Traverse time levels from high noise to low noise.
3. Apply `theta <- theta + 0.5 * step_size * score(theta, t) + sqrt(step_size) * noise`.
4. Log per-level summary statistics.
5. Return samples and trace.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

The tests use an exact Gaussian score and verify that samples move toward the target mean while preserving trace metadata.

## Limitations

The sampler is sensitive to step size and score scaling. Recovery scripts should expose these settings and avoid interpreting a short bounded run as a full-scale reproduction of the paper's 400-level experiments.
