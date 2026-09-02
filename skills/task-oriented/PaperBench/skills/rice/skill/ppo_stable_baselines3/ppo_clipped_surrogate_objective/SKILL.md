---
name: ppo_clipped_surrogate_objective
description: Compute and validate PPO clipped probability-ratio surrogate objectives and trust-region-style diagnostics.
---

# PPO Clipped Surrogate Objective

Use this skill when a PPO implementation, recovery harness, or audit needs the paper's clipped surrogate objective from Equation 7. Do not use it as a generic ratio clamp: the selected term must be the minimum of the unclipped and clipped advantage-weighted objectives.

## Inputs

- `new_log_probs`: log probabilities under the updated/current policy.
- `old_log_probs`: log probabilities under the behavior policy.
- `advantages`: advantage estimates aligned with the sampled actions.
- `clip_epsilon`: clipping half-width, often `0.2`.

## Outputs

- Per-sample ratios, unclipped terms, clipped terms, and selected terms.
- Mean objective and minimization loss.
- Clip fraction and approximate KL diagnostics.

## Workflow

1. Compute `ratio = exp(new_log_prob - old_log_prob)`.
2. Compute `ratio * advantage` for the conservative-policy-iteration surrogate term.
3. Clamp the ratio to `[1 - epsilon, 1 + epsilon]` and multiply by the same advantage.
4. Select the smaller objective contribution per sample.
5. Average selected terms and negate for minimization.
6. Record diagnostics for recovery analysis.

## Validation

Run `python tests/test_surrogate.py` from this skill directory. The tests cover positive-advantage upper clipping, negative-advantage lower clipping, and in-range no-op behavior.

## Limitations

This skill computes the policy objective only. Value loss, entropy bonus, rollout generation, and optimizer execution belong to separate modules.
