---
name: sac_update_step
description: Execute one deterministic reduced Soft Actor-Critic critic actor and target update for recovery evidence.
---

# SAC Update Step

Use this skill for bounded recovery experiments that must show the SAC update mechanism without full MuJoCo or neural-network training. It consumes a validated replay batch and scalar parameters, then emits losses, changed parameters, and mechanism flags.

## Inputs
- Replay batch with transition dictionaries.
- Scalar parameters `value`, `q1`, `q2`, `policy`, and `target_value`.
- Hyperparameters `gamma`, `alpha`, `lr`, and `tau`.

## Outputs
- `loss_before` and `loss_after`.
- `params_before` and `params_after`.
- Mechanism checks for entropy, replay use, twin Q, actor/critic update, target update, and optimizer change.

## Workflow
1. Compute soft value targets using `min(q1, q2) - alpha * log_prob`.
2. Compute Q targets from reward plus discounted target value.
3. Compute actor pressure from `alpha * log_prob - min(q1, q2)`.
4. Apply a small scalar gradient-like update to value, Q, and policy parameters.
5. Apply Polyak averaging to the target value parameter.

## Validation
Run `python tests/test_update.py` or validate the full skill tree with the Distiller validator.

## Limitations
This is a declared reduced/proxy update and must not be reported as full paper-scale SAC training.
