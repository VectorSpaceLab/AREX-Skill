---
name: particle_mirror_descent_mixture_protocol
description: Use this skill to construct the synthetic tied Gaussian mixture posterior target from the Particle Mirror Descent paper, including data generation, log prior/likelihood functions, and grid posterior evaluation.
---

# Synthetic Mixture Model Protocol

## When To Use

Use this skill when a recovery or experiment needs the paper's synthetic multimodal Bayesian target. Do not use it to run PMD updates or score a completed density estimate.

## Inputs

- Random seed and observation count.
- Optional model constants: `theta_true=(1,-2)`, `sigma1=1`, `sigma2=1`, `sigma_x=2.5`, `mix_prob=0.5`.
- Optional grid bounds for posterior evaluation.

## Outputs

- Generated observations and provenance metadata.
- Stable `log_prior`, `log_likelihood`, and dataset log posterior functions.
- Normalized target posterior density on a two-dimensional grid.
- Expected symmetric mode locations.

## Workflow

1. Generate observations from the tied two-component Gaussian mixture described in Section 6.
2. Evaluate likelihoods with log-sum-exp to avoid underflow.
3. Combine independent Gaussian priors and the full-data likelihood into an unnormalized posterior.
4. Normalize grid posterior arrays before downstream metric computation.
5. Save generated data provenance when used in recovery.

## Validation

Run:

```bash
python tests/test_mixture_protocol.py
```

## Limitations

This skill provides a reduced synthetic protocol, not the paper's full repeated 1000-sample comparison against all baselines.
