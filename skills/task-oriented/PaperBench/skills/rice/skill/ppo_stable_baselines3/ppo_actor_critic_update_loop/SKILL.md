---
name: ppo_actor_critic_update_loop
description: Execute a reduced PPO actor-critic update with clipped surrogate, value loss, and optimizer-step evidence.
---

# PPO Actor-Critic Update Loop

Use this skill to build bounded PPO recovery experiments or audits that need executable evidence of a policy/value update. It is intended for mechanism-faithful reduced recovery and small deterministic tests, not for claiming full MuJoCo or Atari reproduction.

## Inputs

- Rollout steps and `last_value`, or a precomputed batch with advantages and returns.
- Old log probabilities and action features for a tiny trainable policy-ratio model.
- Scalar value predictions and learning-rate/loss coefficients.
- Paths to the rollout and clipped-objective skill scripts when composing generated skills.

## Outputs

- `loss_before` and `loss_after`.
- `params_before` and `params_after` for validator-compatible optimizer evidence.
- Mechanism diagnostics for GAE execution, clipped objective execution, and optimizer execution.

## Workflow

1. Compute advantages and returns from rollout steps.
2. Compute the clipped surrogate objective from old and current log probabilities.
3. Add a value-function squared-error term and optional entropy proxy.
4. Estimate deterministic finite-difference gradients for a tiny scalar parameterization.
5. Apply at least one optimizer step.
6. Recompute loss and write a training trace.

## Validation

Run `python tests/test_update.py` from this skill directory. The tests assert parameter changes, finite losses, and execution of GAE and clipped-surrogate paths.

## Limitations

The included optimizer is intentionally tiny and deterministic. It validates PPO's update mechanics under soft-mode recovery but is not a replacement for large-scale neural-network training.
