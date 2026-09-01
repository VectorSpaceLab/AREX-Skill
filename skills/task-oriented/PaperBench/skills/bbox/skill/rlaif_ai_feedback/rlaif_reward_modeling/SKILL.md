---
name: rlaif_reward_modeling
description: Train and validate tiny soft-label pairwise reward models that distill RLAIF AI preference distributions with cross-entropy.
---

# RLAIF Reward Modeling

Use this skill when a RLAIF workflow needs canonical reward-model distillation from pairwise AI soft labels. It is designed for small deterministic recovery checks as well as adapter code that mirrors the paper's reward-model objective.

Do not use this skill for direct-RLAIF single-response scoring or policy-gradient updates. It produces a reward model or score trace, not a trained language model policy.

## Inputs

- Pairwise examples with `context`, `response1`, `response2`, and `preference = [p1, p2]`.
- Initial model parameters or defaults for a tiny linear response scorer.
- Training settings such as learning rate and number of steps.

## Outputs

- Updated reward-model parameters.
- Scores and predicted pairwise probability distribution.
- Training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and `optimizer_state_changed`.

## Workflow

1. Convert each response to deterministic features.
2. Score each response with a shared scalar reward model.
3. Softmax the pair of scores.
4. Compute soft-label cross-entropy against the AI preference distribution.
5. Update parameters with gradient descent.
6. Log before/after losses and parameter changes.

## Validation

Run:

```bash
python scripts/reward_modeling.py --smoke
python tests/test_reward_modeling.py
```

The tests assert that training decreases soft-label cross-entropy, changes parameters, and preserves soft labels without one-hot rounding.

## Limitations

This skill's bundled trainer is intentionally tiny. It proves the canonical RLAIF loss and data contract, but it does not reproduce PaLM 2 reward-model fine-tuning.
