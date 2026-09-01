---
name: ppo_rollout_advantage_protocol
description: Compute PPO fixed-segment rollout returns and generalized advantage estimates with auditable terminal handling.
---

# PPO Rollout Advantage Protocol

Use this skill when implementing or checking PPO-style actor-critic recovery runs that need fixed-length rollout records and truncated generalized advantage estimation. Do not use it for off-policy replay buffers or value targets that are not derived from on-policy trajectory segments.

## Inputs

- Ordered rollout steps with numeric `reward`, `value`, and boolean `done` fields.
- `last_value` for bootstrapping after the final segment step.
- PPO discount `gamma` and GAE parameter `gae_lambda`.

## Outputs

- `advantages`: one scalar per rollout step.
- `returns`: `advantages[i] + value[i]` for each step.
- `deltas`: temporal-difference residuals.
- `diagnostics`: terminal reset and input-shape checks.

## Workflow

1. Preserve rollout order exactly as collected.
2. Iterate backward through the segment.
3. Use the next step value, or `last_value` at the boundary.
4. Set `next_nonterminal` to zero when the current transition ends an episode.
5. Compute delta and recursive GAE.
6. Return advantages and value targets for PPO minibatch updates.

## Validation

Run `python tests/test_advantage.py` from this skill directory, or validate the entire skill with Distiller's `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not collect environment interactions and does not normalize advantages. Callers that normalize advantages must record that preprocessing separately.
