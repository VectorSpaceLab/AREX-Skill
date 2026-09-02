---
name: default_strategy_parameters
description: Compute CMA-ES default strategy parameters from the tutorial formulas for bounded recovery experiments.
---

# Default CMA-ES Strategy Parameters

Use this skill when a recovery or implementation needs dimension-aware CMA-ES defaults rather than hand-picked optimizer constants. Do not use it for gradient optimizers or algorithms that do not adapt a Gaussian covariance matrix.

## Inputs
- Search dimension `n`, a positive integer.
- Optional population size `lambda_`; if absent use `4 + floor(3 ln n)`.

## Outputs
- `lambda`, `mu`, positive recombination `weights`, `mueff`, `cm`, `cs`, `ds`, `cc`, `c1`, `cmu`, and `expected_norm`.

## Workflow
1. Validate the dimension and population size.
2. Compute log-shaped positive parent weights and normalize them to sum to one.
3. Compute effective parent mass and learning rates using the tutorial's Appendix A defaults.
4. Return JSON-serializable values so downstream skills can reproduce the run.

## Validation
Run `python scripts/cmaes_parameters.py --dimension 2` and `python -m pytest tests` or the Distiller skill-tree validator with `--run-tests`.

## Limitations
This skill implements the positive-weight default sufficient for the reduced recovery; active negative covariance weights are documented but not required by the proxy experiment.
