---
name: reinforcement-learning
description: "Route and operate rlcode reinforcement-learning examples for
  GridWorld, CartPole, Atari, and hard-exploration Atari workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# reinforcement-learning Repo Skill

Use this repo skill when a task involves the `rlcode/reinforcement-learning` educational PyTorch examples: choosing an algorithm script, adapting a training loop, diagnosing setup/checkpoint/rendering issues, doing a safe smoke check, or explaining benchmark/protocol caveats for GridWorld, CartPole, Atari Breakout/Pong, or hard-exploration Atari.

This skill is self-contained. It teaches the repo's operating contracts and bundles safe smoke helpers; it does not require the original construction checkout, private Creator environment, W&B credentials, Atari ROM downloads, render windows, or full training runs.

## First checks

1. Read [`references/setup-and-troubleshooting.md`](references/setup-and-troubleshooting.md) when the task is about installation, Python version, dependency imports, display/pygame, Atari ROMs, W&B, CUDA/MPS, or why this repository is a flat script collection rather than an installable import package.
2. Run the root environment check when you need to know whether the current runtime has the main dependencies:

```bash
python scripts/check_reinforcement_learning_environment.py --help
python scripts/check_reinforcement_learning_environment.py
python scripts/check_reinforcement_learning_environment.py --include-optional-cuda --json
```

3. Then route to the smallest matching sub-skill below.

## Route by task

| User task or signal | Read |
| --- | --- |
| 5x5 GridWorld, dynamic programming, policy iteration, value iteration, tabular SARSA/Q-learning, Deep SARSA, REINFORCE, Pygame GridWorld rendering, row/column state confusion | [`sub-skills/grid-world-dp-and-control/SKILL.md`](sub-skills/grid-world-dp-and-control/SKILL.md) |
| CartPole-v1 DQN, A2C, PPO, `--render`, `--test`, `cartpole_*.pt`, reward shaping, checkpoint loading, classic-control headless smoke | [`sub-skills/cartpole-classic-control/SKILL.md`](sub-skills/cartpole-classic-control/SKILL.md) |
| Atari Breakout/Pong DQN or PPO, ALE/Gymnasium preprocessing, Nature CNN, frame stacking, life-loss vs game-over returns, replay buffer, SyncVectorEnv, W&B logging | [`sub-skills/atari-breakout-pong/SKILL.md`](sub-skills/atari-breakout-pong/SKILL.md) |
| Montezuma/Pitfall/PrivateEye, PPO+RND, envpool, deterministic Go-Explore, archive/cell/replay log, demo extraction, robustification/backward algorithm, sticky-action protocol caveats | [`sub-skills/hard-atari-exploration/SKILL.md`](sub-skills/hard-atari-exploration/SKILL.md) |

## Repo operating model

- The repository is organized as standalone workflow files, not a conventional importable Python package. Treat workflow labels such as `GridWorld policy iteration`, `CartPole DQN`, `Atari PPO`, or `Go-Explore Phase 1` as user-facing tasks, not as package modules that can be imported by name.
- README setup expects Python 3.11 and `uv sync`; operationally the runtime dependency set includes PyTorch/TorchVision, Gymnasium with Atari support, ale-py, NumPy, Matplotlib, Pygame, OpenCV headless, W&B, MoviePy, and envpool.
- Long training scripts save checkpoints next to their workflow entrypoints by default. The sub-skills document checkpoint names and loader shapes; do not assume checkpoints are interchangeable between algorithms.
- Atari workflows are benchmark-sensitive. Smoke checks in this skill validate interfaces and invariants only; they do not prove convergence, first-key discovery, paper-level scores, or Mac MPS benchmark parity.
- W&B is opt-in in Atari workflows. Omit W&B flags unless the user explicitly wants network logging and already has credentials.
- Rendering is opt-in or GUI-driven. On headless servers, prefer bundled smoke scripts and non-render training paths instead of opening Pygame/Gymnasium windows.

## Bundled smoke helpers

- Root dependency/backend check: [`scripts/check_reinforcement_learning_environment.py`](scripts/check_reinforcement_learning_environment.py).
- GridWorld algorithm invariants: [`sub-skills/grid-world-dp-and-control/scripts/grid_world_smoke.py`](sub-skills/grid-world-dp-and-control/scripts/grid_world_smoke.py).
- CartPole model/update invariants: [`sub-skills/cartpole-classic-control/scripts/cartpole_smoke.py`](sub-skills/cartpole-classic-control/scripts/cartpole_smoke.py).
- Atari DQN/PPO model/replay/GAE invariants: [`sub-skills/atari-breakout-pong/scripts/atari_basic_smoke.py`](sub-skills/atari-breakout-pong/scripts/atari_basic_smoke.py).
- Hard-Atari RND/Go-Explore/demo/robustification invariants: [`sub-skills/hard-atari-exploration/scripts/hard_atari_smoke.py`](sub-skills/hard-atari-exploration/scripts/hard_atari_smoke.py).

## Avoid this skill when

- The task is about Stable-Baselines3, CleanRL, Tianshou, PettingZoo, TRL/OpenRLHF/verl, or another RL package rather than these standalone examples.
- The user needs a production RL experiment manager, distributed RLHF stack, or generic Gymnasium API reference unrelated to the repo's scripts.
- The request is to execute a full training benchmark under Creator mode. Creator-created skills can explain and validate the operating context; a Researcher session should perform downstream experiments.

## Provenance and routing metadata

- Source baseline: [`references/repo-provenance.md`](references/repo-provenance.md).
- Router import metadata: [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).
