---
name: positive_advantage_sil_loss
description: Compute Self-Imitation Learning policy and value losses using the paper's positive-advantage gate.
---

# Positive-Advantage SIL Loss

Use this skill when a recovery or implementation needs the exact SIL objective from Equations 1-3 of "Self-Imitation Learning". It is suitable for checking full actor-critic implementations or reduced scalar proxies.

Do not use this skill for ordinary actor-critic advantages that allow negative policy pressure; SIL clamps negative advantages to zero.

## Inputs
- `returns`: Monte Carlo returns from replay records.
- `values`: current value estimates for the same states.
- `action_probabilities` or selected-action probabilities from the policy.
- `beta`: value-loss coefficient.

## Outputs
- Positive advantages.
- Valid-sample mask/count.
- Policy loss, value loss, total loss.

## Workflow
1. Compute `advantage = return - value`.
2. Clamp to `positive_advantage = max(advantage, 0)`.
3. Compute `policy_loss = mean(-log(prob_action) * positive_advantage)`.
4. Compute `value_loss = mean(0.5 * positive_advantage^2)`.
5. Return `policy_loss + beta * value_loss` and diagnostics.

## Validation
Run:

```bash
python tests/test_sil_loss.py
```

The test verifies exact loss values and zero contribution for non-positive advantages.

## Limitations
- This script computes scalar diagnostics, not automatic differentiation.
- Callers are responsible for mapping full policy distributions to selected-action probabilities.

## Zero-Pressure Ablation
If every replay return is less than or equal to the current value estimate, SIL must report zero valid samples and apply no imitation pressure. Treat this as expected behavior, not a metric failure.
