---
name: jsrl_value_exploration_update
description: Apply a minimal value-based exploration-policy update to Jump-Start Reinforcement Learning trajectories and record optimizer evidence.
---

# JSRL Value Exploration Update

## When To Use

Use this skill after JSRL switching rollouts have produced trajectories and the recovery needs to show a real value-based policy update. It is suitable for reduced proxy runs and for sanity-checking full implementations.

## Inputs

- Transitions containing `state`, `action`, `reward`, `next_state`, and `done`.
- Q-value table or parameter dictionary for the exploration-policy.
- Learning rate and discount factor.

## Outputs

- Updated Q-value parameters.
- Training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and `optimizer_state_changed`.
- Greedy action helper for the exploration-policy.

## Workflow

1. Build a deterministic key for each state-action value.
2. Compute TD targets with terminal-state handling.
3. Record squared TD loss before the update.
4. Apply Q-learning style updates to trainable parameters.
5. Recompute loss and save parameter-change evidence.
6. Use the updated greedy policy in later exploration rollouts.

## Validation

Run:

```bash
python scripts/value_update.py --demo
python -m pytest tests
```

The demo prints before/after Q parameters and a validator-compatible training trace.

## Limitations

This reduced update is not a replacement for IQL, DQN, or QT-Opt. It preserves the paper-relevant requirement that JSRL data feeds a value-based train-policy step with auditable parameter changes.
