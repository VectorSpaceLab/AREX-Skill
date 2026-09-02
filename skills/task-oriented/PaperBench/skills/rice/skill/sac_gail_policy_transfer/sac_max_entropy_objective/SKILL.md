---
name: sac_max_entropy_objective
description: Compute Soft Actor-Critic maximum-entropy value and actor objective terms for bounded recovery experiments.
---

# SAC Maximum Entropy Objective

Use this skill when a recovery or implementation task needs the SAC formulas that combine reward-seeking Q-values with policy entropy. Do not use it to manage replay buffers or perform optimizer updates.

## Inputs
- Equal-length numeric lists of Q-values and log policy probabilities.
- Optional entropy coefficient `alpha`, defaulting to `1.0`.

## Outputs
- Elementwise soft values `q - alpha * log_prob`.
- Elementwise actor losses `alpha * log_prob - q`.
- Mean summaries for recovery metrics.

## Workflow
1. Validate the input lists are non-empty, equal length, and finite.
2. Compute soft values with the entropy term included.
3. Compute policy losses with the same alpha convention.
4. Save or return the summary for downstream SAC update checks.

## Validation
Run `python tests/test_objective.py` or validate the full skill tree with the Distiller validator.

## Limitations
This skill encodes deterministic scalar/list formulas only; full neural policies and temperature tuning belong to a larger training harness.
