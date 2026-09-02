---
name: maximum_entropy_objective
description: Compute SAC maximum entropy objective diagnostics for rewards, log probabilities, discounts, and temperature-scaled entropy bonuses.
---

# Maximum Entropy Objective

Use this skill when a recovery or implementation must verify the SAC maximum-entropy objective from Haarnoja et al. The skill is appropriate for bounded checks, synthetic replay batches, and cross-checks of entropy bonus signs. Do not use it to claim full MuJoCo performance.

## Inputs
- A reward sequence.
- Matching policy log probabilities.
- Discount factor `gamma`.
- Temperature or reward-scale coefficient `alpha`.

## Outputs
- Discounted reward-only return.
- Discounted soft return using `reward - alpha * log_prob`.
- Per-step entropy bonuses.

## Workflow
1. Validate reward and log-probability lengths.
2. Convert entropy to the sign convention `-log_prob`.
3. Add `alpha * entropy` to reward at each step.
4. Compute discounted totals for reward-only and soft objectives.
5. Use the difference as a mechanism diagnostic, not as a task score.

## Validation
Run `python tests/test_entropy_objective.py` or validate the whole tree with the Distiller skill validator.

## Limitations
This module computes objective diagnostics only. It does not implement replay sampling, neural critics, or environment interaction.
