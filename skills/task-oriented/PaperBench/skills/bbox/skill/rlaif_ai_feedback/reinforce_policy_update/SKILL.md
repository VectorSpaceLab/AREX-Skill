---
name: reinforce_policy_update
description: Run a bounded REINFORCE-style policy update with terminal RLAIF rewards, a value baseline, and KL regularization evidence.
---

# REINFORCE Policy Update

Use this skill when a RLAIF recovery needs to prove that a reward signal actually drives a policy update. The bundled implementation uses a tiny two-action softmax policy, which is suitable for reduced recovery and deterministic tests.

Do not claim full language-model training from this skill alone. If no requested model is loaded, mark the run as reduced and keep full-model flags false.

## Inputs

- Policy logits or default two-action logits.
- `chosen_action`: the action selected by the policy trajectory.
- `reward`: terminal reward from an RM or direct-RLAIF scorer.
- `baseline`, `learning_rate`, optional `reference_logits`, and `kl_coefficient`.

## Outputs

- Updated logits and before/after probabilities.
- `loss_before`, `loss_after`, `params_before`, `params_after`, `optimizer_state_changed`.
- Advantage and KL metadata.

## Workflow

1. Compute action probabilities from current logits.
2. Compute the advantage as `reward - baseline`.
3. Apply the REINFORCE gradient for the chosen action.
4. Add a KL-gradient term that pulls toward the reference policy when configured.
5. Update logits with a real optimizer step.
6. Write a trace that can pass recovery validation.

## Validation

Run:

```bash
python scripts/policy_update.py --smoke
python tests/test_policy_update.py
```

The tests assert that a positive reward increases the chosen action probability and that validator-compatible parameter fields are present.

## Limitations

This is a faithful scalar proxy for the paper's REINFORCE mechanism, not a replacement for full sequence-model RL training.
