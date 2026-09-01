---
name: iterative_refinement_sampler
description: Run a deterministic SR3-inspired reverse denoising trajectory conditioned on low-resolution input for proxy recovery.
---

# Iterative Refinement Sampler

Use this skill after a denoising objective has produced a parameter estimate. It tests the SR3 generation pattern: start from noise and repeatedly refine while conditioning on the low-resolution input.

## Inputs
- Initial noisy scalar state.
- Conditioning scalar and scale factor.
- Learned scalar denoiser weight.
- Number of reverse refinement steps.

## Outputs
- A trajectory list with per-step states.
- Final proxy super-resolved estimate.

## Workflow
1. Initialize from a noisy state rather than the clean target.
2. At every step, combine the current state, condition-derived target prior, and learned denoiser correction.
3. Save the full trajectory for recovery analysis.
4. Compare final distance to the target against the initial distance outside this skill.

## Validation
Run `python tests/test_sampler.py` or validate the skill tree with `--run-tests`.

## Limitations
This scalar trajectory cannot measure perceptual image quality; it checks iterative conditioning mechanics only.
