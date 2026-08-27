---
name: tabular-control
description: "Work with the repo's toy tabular RL workflows: Q-learning, Sarsa,
  and GridWorld."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Tabular Control

Use this sub-skill for the repo's small tabular-control workflows. The bundled demo keeps the 1D chain examples self-contained and avoids importing the original source files just to understand or run them.

## In scope
- Q-learning and Sarsa on the toy 1D chain environment
- comparing off-policy and on-policy tabular updates
- inspecting the GridWorld helper
- explaining terminal-state handling, epsilon-greedy selection, and step counts

## Not in scope
- DQN or any neural value-function approximation
- policy-gradient, actor-critic, A2C, PPO
- DDPG, SAC, TD3, or other continuous-control families
- repo-wide install, Gym-version, or plotting compatibility topics

## Bundle
- `scripts/tabular_control_demo.py` — safe runner for the toy chain example with an algorithm switch
- `scripts/gridworld.py` — fixture-friendly GridWorld helper adapted from the original class
- `references/algorithm-notes.md` — update-loop and comparison notes
- `references/troubleshooting.md` — execution and environment notes

## Typical requests
- Run the toy example: use `scripts/tabular_control_demo.py`
- Compare Q-learning vs Sarsa: pass `--algorithm both`
- Inspect the GridWorld helper: open `scripts/gridworld.py`
- Explain the tabular update loop: read `references/algorithm-notes.md`

## Routing
- For anything outside tabular control, return to the root router at `../../SKILL.md`.
- Hand off DQN, on-policy actor-critic, and off-policy continuous-control requests to the appropriate sibling sub-skill through the root router.
- If a request needs plotting or broader repo compatibility guidance, keep it out of this sub-skill and route upward.

## Notes
- The original source scripts use pandas and matplotlib, but the bundled helper keeps those optional and does not depend on them for the default run.
- The 1D chain examples and the GridWorld helper are separate toy workflows; do not assume they share the same state or action space.
