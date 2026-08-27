---
name: grid-world-dp-and-control
description: "Use and adapt GridWorld dynamic programming, tabular control, Deep
  SARSA, and REINFORCE workflows distilled from the reinforcement-learning
  examples."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# GridWorld DP and Control

Use this sub-skill when the task is about the repository's 5x5 GridWorld workflows: policy iteration, value iteration, tabular SARSA, tabular Q-learning, Deep SARSA, or REINFORCE. It is self-contained; do not depend on the original checkout at runtime.

## Route here for

- Explaining, adapting, or debugging GridWorld dynamic programming (`1-policy_iteration.py`, `2-value_iteration.py`) as provenance workflow labels.
- Explaining, adapting, or debugging tabular control (`3-sarsa.py`, `4-q_learning.py`) as provenance workflow labels.
- Making tiny CPU checks for Deep SARSA and REINFORCE neural update logic (`5-deep_sarsa.py`, `6-reinforce.py`) as provenance workflow labels.
- Diagnosing row/column versus column/row coordinate mistakes, action-order mismatches, and render/headless behavior.

## Route away from

- Gymnasium CartPole DQN/A2C/PPO: use the CartPole sub-skill.
- Atari Breakout/Pong DQN/PPO, preprocessing, ROMs, or W&B: use the standard Atari sub-skill.
- Montezuma/Pitfall/PrivateEye hard-exploration, RND, Go-Explore, or robustification: use the hard Atari sub-skill.

## Start here

1. Read [`references/algorithm-guide.md`](references/algorithm-guide.md) for the MDP layout, coordinate conventions, formulas, API-shaped examples, and safe adaptation patterns.
2. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a grid policy points in the wrong direction, rendering blocks on a server, tabular values do not update, or Torch neural checks fail.
3. Run the bundled smoke script when you need a self-contained, non-rendering API check:

```bash
python scripts/grid_world_smoke.py --help
python scripts/grid_world_smoke.py
python scripts/grid_world_smoke.py --section dp
python scripts/grid_world_smoke.py --section neural --strict-torch
```

The smoke script intentionally reimplements tiny fixtures and update steps. It does not import source repository files, open Pygame, train to convergence, or require a display.

## Critical facts to preserve

- DP workflows use state as `[row, col]`; drawing helpers usually need `(col, row)`, so swap before rendering arrows or markers.
- Tabular `Env`-style workflows use state as `[col, row]` and actions `0=up, 1=down, 2=left, 3=right`.
- Dynamic `DynamicEnv`-style workflows also use `[col, row]`, but actions are `0=up, 1=down, 2=right, 3=left`; the distilled source agents expose a fifth network output/action that behaves as a no-op in the dynamic environment.
- GUI examples are interactive and render-oriented. For validation or CI, use headless logic equivalent to `render_mode=None` rather than opening Pygame loops.
