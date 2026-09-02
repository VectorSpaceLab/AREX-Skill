---
name: minimum_sd_optimizer
description: Minimise empirical Stein discrepancy objectives with bounded searches and auditable loss traces for recovery experiments.
---

# Minimum Stein Discrepancy Optimizer

Use this skill when an empirical Stein discrepancy has been defined and a recovery needs to estimate a parameter by minimising that discrepancy. It is especially useful when full stochastic-gradient or Riemannian-gradient infrastructure is unnecessary or unavailable, but the recovery still needs executable evidence of an argmin search.

## Inputs
- A callable loss function of a scalar parameter.
- Initial parameter, search bounds, grid size, and optional local refinement radius.
- Metadata about the sample and acceptance threshold.

## Outputs
- Best parameter, best loss, initial loss, and loss improvement.
- Search trace with candidate evaluations.
- `params_before` and `params_after` fields suitable for reduced recovery validation.

## Workflow
1. Evaluate the initial parameter and record it as the baseline.
2. Evaluate a bounded grid over the supplied interval.
3. Optionally refine locally around the best grid point.
4. Select the finite candidate with minimum loss.
5. Record whether the parameter changed and whether the objective improved.

## Validation
Run `python tests/test_minimum_sd_optimizer.py` or validate the skill tree with tests. Tests include a deterministic quadratic and a monotone trace check.

## Limitations
This skill is a bounded deterministic optimiser for recovery evidence. It does not replace the paper's full stochastic Riemannian optimiser for large-scale experiments.

## Refinement cycle 1 note
Stress recovery confirmed loss improvement on the deterministic Student-t proxy; keep `params_before` and `params_after` in every optimiser trace.
