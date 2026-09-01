---
name: ppo_clipped_surrogate_objective
description: Compute and validate PPO clipped probability-ratio surrogate losses and diagnostics for policy update recovery or implementation.
---

# PPO Clipped Surrogate Objective

## When To Use

Use this skill when implementing, auditing, or recovering the core objective from Proximal Policy Optimization. It is appropriate when you have action log probabilities under an old behavior policy, action log probabilities under a candidate new policy, and aligned advantage estimates.

Do not use it to collect trajectories or update model parameters; those are separate responsibilities.

## Inputs

- `old_log_probs`: aligned numeric list of sampled-action log probabilities under the old policy.
- `new_log_probs`: aligned numeric list under the candidate policy.
- `advantages`: aligned numeric list of advantages.
- `clip_epsilon`: positive clipping width, typically `0.2`.

## Outputs

The script returns JSON with `ratios`, `unclipped`, `clipped`, `objective_terms`, `mean_objective`, `loss`, `clip_fraction`, and `approx_kl`.

## Workflow

1. Freeze old-policy log probabilities before computing ratios.
2. Compute `ratio = exp(new_log_prob - old_log_prob)`.
3. Compute `unclipped = ratio * advantage`.
4. Compute `clipped = clip(ratio, 1-epsilon, 1+epsilon) * advantage`.
5. Use `minimum(unclipped, clipped)` per sample and average it.
6. Minimize `loss = -mean_objective` if using a minimization optimizer.
7. Inspect `clip_fraction` and `approx_kl` to ensure the update is auditable.

## Validation

Run:

```bash
python tests/test_clipped_surrogate.py
python scripts/compute_clipped_surrogate.py --old-log-probs '[0,0]' --new-log-probs '[0.3,-0.3]' --advantages '[1,-1]' --clip-epsilon 0.2
```

## Limitations

This skill does not estimate advantages, sample environments, or train parameters. It focuses only on the PPO objective and diagnostics.
