---
name: annealed_langevin_sampling
description: Run bounded annealed Langevin posterior sampling from composed score functions for score-based SBI recovery.
---

# Annealed Langevin Sampling

Use this skill when a recovery needs to turn a composed F-NPSE or PF-NPSE score into posterior samples. It implements the paper's score-driven sampler in a bounded, deterministic form suitable for reduced experiments.

## Inputs

- A score callable or Gaussian target parameters for the script interface.
- Number of samples, noise levels, Langevin steps per level, step size, reference variance, and random seed.
- Optional trace output path.

## Outputs

- Posterior samples.
- Sampler trace with seed, score evaluations, reference variance, step size, and finite-sample diagnostics.

## Workflow

1. Initialize particles from the F-NPSE reference distribution, typically `N(0, I/n)`.
2. Iterate over noise/progress levels from reference to target.
3. Apply Langevin updates with the composed score and Gaussian noise.
4. Return final samples and trace details for recovery logs.
5. Use bounded sample counts and fixed seeds for fast validation.

## Validation

Run `python tests/test_annealed_langevin_sampling.py` or validate the whole skill tree.

## Limitations

This skill is a sampler. It assumes score composition has already been defined and does not validate whether the learned score is accurate.
