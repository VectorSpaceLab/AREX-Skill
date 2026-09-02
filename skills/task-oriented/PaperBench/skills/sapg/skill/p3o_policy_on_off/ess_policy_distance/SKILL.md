---
name: ess_policy_distance
description: Compute P3O effective sample size and derive adaptive clipping and KL coefficients from replay policy probabilities.
---

# ESS Policy Distance

Use this skill when implementing or auditing P3O replay updates that need the paper's automatic hyperparameter schedule. Do not use it for unrelated off-policy methods that tune clipping or regularization manually.

## Inputs
- `target_probs`: probabilities assigned by the current target policy to sampled actions.
- `behavior_probs`: probabilities stored with replay data by the behavior policy.

## Outputs
- `importance_ratios`: target divided by behavior probabilities.
- `ess`: normalized effective sample size in `[0, 1]`.
- `clip_threshold`: equal to `ess`.
- `kl_coefficient`: equal to `1 - ess`.

## Workflow
1. Validate non-empty equal-length probability vectors.
2. Clamp denominators by a small epsilon to avoid division by zero.
3. Compute ratios `rho = pi_theta(a|s) / beta(a|s)`.
4. Compute normalized ESS as `(sum(rho)^2) / (N * sum(rho^2))`.
5. Return `c = ESS` and `lambda = 1 - ESS` for the P3O update.

## Source Boundary
Use this skill with the paper, module documents, generated artifacts, and ordinary package documentation. Do not read or depend on the original P3O repository.

## Validation
Run `python scripts/<script>.py --self-test` or `python -m pytest tests` from the skill directory. The bundled tests use only the Python standard library.

