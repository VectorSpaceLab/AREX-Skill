---
name: fb_occupancy_factorization
description: Create and validate reduced forward-backward successor-occupancy factorizations from reward-free transition tables.
---

# Forward-Backward Occupancy Factorization

Use this skill when a recovery or implementation needs the FB paper mechanism that summarizes reward-free dynamics before any downstream reward is known. Do not use it for task-specific Q-learning or reward-conditioned training.

## Inputs

- A finite transition table with states, actions, next states, and discount.
- A desired embedding rank for a reduced factorization.
- Optional optimization settings for a bounded gradient step.

## Outputs

- Discounted successor occupancy rows for state-action pairs.
- Forward embeddings `F`, backward embeddings `B`, and scalar reconstruction losses.
- Diagnostics showing whether at least one parameter update reduced loss.

## Workflow

1. Build the transition matrix over state-action rows under a deterministic or supplied behavior policy.
2. Compute the discounted successor occupancy matrix `(I - gamma P)^-1`.
3. Initialize a low-rank FB factorization and run a bounded update that changes trainable parameters.
4. Report `loss_before`, `loss_after`, parameter snapshots, and shape checks.
5. Keep this module reward-free; reward projection belongs to `reward_projection`.

## Validation

Run `python scripts/fb_factorization.py --self-test` or validate through `tests/test_fb_factorization.py`. The tests use a tiny chain/grid and require nonnegative discounted occupancies plus reduced reconstruction loss.

## Limitations

This skill is a reduced deterministic implementation for recovery evidence. It does not claim to reproduce the paper's neural TD training scale.
