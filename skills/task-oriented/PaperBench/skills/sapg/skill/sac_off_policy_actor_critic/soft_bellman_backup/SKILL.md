---
name: soft_bellman_backup
description: Construct SAC soft state values, Q targets, and Bellman residuals from replay rewards, log probabilities, and critic estimates.
---

# Soft Bellman Backup

Use this skill to validate the critic side of Soft Actor-Critic. It applies the paper's soft value estimate `V = Q - alpha * log_pi` and Q target `r + gamma * (1-done) * V_next` on bounded batches.

## Inputs
- Current Q estimates and policy log probabilities.
- Rewards, done flags, and next soft values.
- Discount factor and temperature coefficient.

## Outputs
- Soft values.
- Q targets.
- Mean squared Bellman error.

## Workflow
1. Compute `soft_value = q_value - alpha * log_prob`.
2. For each transition, compute `reward` for terminal transitions.
3. For nonterminal transitions, add discounted next soft value.
4. Compare Q estimates against targets with squared residuals.
5. Save the residuals for recovery traces.

## Validation
Run `python tests/test_soft_bellman.py` or the Distiller skill validator.

## Limitations
This skill does not define neural network architectures. It is a deterministic batch-level contract for SAC backups.
