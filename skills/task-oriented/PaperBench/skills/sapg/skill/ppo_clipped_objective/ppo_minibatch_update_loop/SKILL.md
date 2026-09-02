---
name: ppo_minibatch_update_loop
description: Run a deterministic reduced PPO minibatch update loop with frozen old log probabilities and auditable optimizer traces.
---

# PPO Minibatch Update Loop

## When To Use

Use this skill when you need an executable, bounded PPO-style optimizer step that demonstrates repeated minibatch updates against frozen old-policy probabilities. It is designed for recovery tests and small implementations where full MuJoCo/Atari training is unavailable.

Do not present this reduced runner as full benchmark training.

## Inputs

- Batch fields: `actions`, `old_log_probs`, `advantages`, and optional `rewards` or `returns`.
- Scalar Bernoulli-policy initial `theta` for reduced recovery, or equivalent trainable policy parameters.
- Optimizer settings: `learning_rate`, `epochs`, `clip_epsilon`, and minibatch size.

## Outputs

- `params_before` and `params_after`.
- `loss_before`, `loss_after`, `expected_reward_before`, `expected_reward_after`.
- Per-step diagnostics including ratios, clip fraction, approximate KL, and policy-gradient estimate.
- `optimizer_step_executed` and `old_log_probs_frozen` booleans.

## Workflow

1. Copy old action log probabilities before training.
2. Normalize advantages if requested by the caller.
3. For each epoch, compute the PPO clipped objective.
4. Estimate a bounded first-order update for the scalar Bernoulli policy.
5. Apply a deterministic gradient-ascent step.
6. Log losses, parameters, expected-reward proxy, clipping diagnostics, and source skill names.

## Validation

Run:

```bash
python tests/test_minibatch_update.py
python scripts/run_minibatch_ppo.py --output /tmp/ppo_trace.json
```

## Limitations

This skill intentionally uses a tiny Bernoulli-policy proxy. It validates mechanism faithfulness but not full continuous-control or Atari performance.
