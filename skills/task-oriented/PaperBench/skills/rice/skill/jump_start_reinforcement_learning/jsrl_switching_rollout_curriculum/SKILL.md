---
name: jsrl_switching_rollout_curriculum
description: Build Jump-Start Reinforcement Learning rollouts that switch from guide-policy control to exploration-policy control under curriculum or random guide-step schedules.
---

# JSRL Switching Rollout Curriculum

## When To Use

Use this skill to collect trajectories for JSRL or to test whether a recovery harness correctly implements the paper's two-policy handoff. It is useful for full RL environments and for reduced sparse-reward proxy environments.

## Inputs

- Environment with `reset()` and `step(action)`.
- Guide-policy and exploration-policy callables.
- Horizon `H`, selected guide-step `h`, and optional guide-step schedule.
- Threshold `β` used to advance curriculum stages.

## Outputs

- Trajectory records with state, action, reward, next state, done flag, and `controller` equal to `guide` or `exploration`.
- Handoff summary with selected `h`, guide action count, exploration action count, total reward, and success flag.
- Curriculum cursor updates for threshold-based advancement.

## Workflow

1. Clamp the selected guide-step to the valid horizon.
2. Roll out the guide-policy while `t < h`.
3. Roll out the exploration-policy after the handoff until termination or horizon.
4. Append controller labels to every transition.
5. Advance the curriculum only after evaluation meets or exceeds `β`.
6. For ablations, sample guide steps from the same schedule without changing the data schema.

## Validation

Run:

```bash
python scripts/switching_rollout.py --demo
python -m pytest tests
```

The demo prints a small trajectory and handoff summary.

## Limitations

This skill does not implement a complete RL algorithm. It only owns the rollout and curriculum contract; policy/value updates belong in the value exploration update skill.
