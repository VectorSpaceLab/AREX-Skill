---
name: trajectory_return_replay
description: Build Self-Imitation Learning replay records by converting completed agent episodes into discounted state-action-return tuples.
---

# Trajectory Return Replay

Use this skill when implementing or validating Self-Imitation Learning data flow from the paper "Self-Imitation Learning". It is appropriate for full RL runs and reduced proxy recoveries that need auditable replay records from the agent's own completed trajectories.

Do not use this skill for expert demonstration replay, one-step TD replay, or offline data whose episode returns cannot be reconstructed.

## Inputs
- Episode steps as JSON records with `state`, `action`, `reward`, and optional `done`.
- Discount factor `gamma` in `[0, 1]`.
- Optional replay capacity.

## Outputs
- Replay records with `state`, `action`, discounted `return`, `reward`, and `index`.
- Optional JSON item log for recovery evidence.

## Workflow
1. Validate the episode order and discount factor.
2. Compute Monte Carlo returns backward through the episode.
3. Pair each return with the original state and action.
4. Apply deterministic capacity truncation if requested.
5. Save the records as recovery evidence when running an experiment.

## Validation
Run:

```bash
python tests/test_trajectory_return_replay.py
```

The test checks sparse-reward return computation, terminal handling, and capacity truncation.

## Limitations
- This skill does not implement prioritized replay sampling; priorities can be added downstream from positive advantages.
- It does not interact with an environment; callers provide completed episode steps.

## Terminal Propagation Regression
A terminal reward must still propagate to earlier non-terminal steps in the same episode; only a terminal boundary before a previous episode resets the backward return accumulator.
