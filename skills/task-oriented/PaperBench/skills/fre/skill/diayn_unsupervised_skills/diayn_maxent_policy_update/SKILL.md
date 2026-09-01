---
name: diayn_maxent_policy_update
description: Execute a bounded maximum-entropy DIAYN policy surrogate update with before-after loss and parameter-change evidence.
---

# DIAYN Maximum-Entropy Policy Update

Use this skill when a recovery needs executable evidence that a skill-conditioned policy was updated using the DIAYN intrinsic objective. The full paper uses SAC; this skill provides a bounded surrogate contract for reduced recovery when full MuJoCo/SAC training is infeasible.

## Inputs

- Trainable scalar policy parameters indexed by skill.
- Target state regions or action directions for each sampled skill.
- Learning rate and entropy coefficient.
- A rollout batch or deterministic synthetic batch.

## Outputs

- `params_before` and `params_after`.
- `loss_before` and `loss_after`.
- Objective delta, entropy diagnostic, and optimizer-step status.

## Workflow

1. Construct skill-conditioned predictions from current parameters.
2. Compute a differentiable surrogate loss against discriminable skill-specific targets.
3. Add an entropy-aware diagnostic so recovery records stochasticity pressure.
4. Apply a real gradient step to the parameters.
5. Report whether parameters changed and whether loss improved.

## Validation

Run `python scripts/policy_update.py --demo`. Tests verify that one update changes parameters and does not increase the deterministic surrogate loss.

## Limitations

This helper is not a full SAC implementation and must be labeled as reduced/proxy recovery when used alone. It preserves the DIAYN optimizer contract but not the full benchmark runtime.
