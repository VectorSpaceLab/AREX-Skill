#!/usr/bin/env python3
"""Print the distilled DRL-Pytorch algorithm and dependency matrix.

This helper is self-contained skill runtime content. It does not import a
DRL-Pytorch checkout or run training. Use it when an agent needs a quick routing
summary before choosing a sub-skill or command recipe.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

ALGORITHMS: list[dict[str, Any]] = [
    {
        "key": "q-learning",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "1.Q-learning",
        "implementation": "QLearningAgent",
        "action_space": "discrete/tabular",
        "envs": [{"EnvIdex": None, "name": "CliffWalking-v0", "extra": "base gymnasium"}],
        "safe_smoke": "python sub-skills/value-based-discrete-control/scripts/smoke_value_based.py --repo-root <repo-root> --algorithm q-learning",
        "notes": "main.py has no parser and trains by default; use the bundled module smoke for diagnostics.",
    },
    {
        "key": "dqn-family",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "2.1_Duel-Double-DQN",
        "implementation": "DQN_agent with Q_Net or Duel_Q_Net",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "--Duel and --Double choose Dueling/Double/vanilla variants.",
    },
    {
        "key": "per-light",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "2.3 .../LightPriorDQN_gym0.2x",
        "implementation": "DQN_Agent + LightPriorReplayBuffer",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "CUDA_VISIBLE_DEVICES='' python main.py --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "recommended modern PER path; no --dvc flag in this launcher.",
    },
    {
        "key": "per-sumtree",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "2.3 .../PriorDQN_gym0.2x",
        "implementation": "DQN_Agent + PrioritizedReplayBuffer",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "CUDA_VISIBLE_DEVICES='' python main.py --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "use when a sum-tree PER comparison is requested; legacy gym0.1x variant needs a separate Python/gym stack.",
    },
    {
        "key": "c51",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "2.4_Categorical-DQN_C51",
        "implementation": "CDQN_agent + Categorical_Q_Net",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "--DQL toggles Double Q-learning; distribution atoms default to 51.",
    },
    {
        "key": "noisynet",
        "sub_skill": "value-based-discrete-control",
        "directory_label": "2.5_NoisyNet-DQN",
        "implementation": "NoisyNetDQN_agent + Noisy_Q_Net",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "exploration comes from NoisyLinear layers rather than epsilon flags.",
    },
    {
        "key": "ppo-discrete",
        "sub_skill": "policy-and-actor-critic-control",
        "directory_label": "3.1 PPO-Discrete",
        "implementation": "PPO_discrete",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "on-policy trajectory buffer with T_horizon and PPO clipping.",
    },
    {
        "key": "ppo-continuous",
        "sub_skill": "policy-and-actor-critic-control",
        "directory_label": "3.2 PPO-Continuous",
        "implementation": "PPO_agent",
        "action_space": "continuous",
        "envs": [
            {"EnvIdex": 0, "name": "Pendulum-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLanderContinuous-v2", "extra": "gymnasium[box2d]"},
            {"EnvIdex": 2, "name": "Humanoid-v4", "extra": "gymnasium[mujoco] or mujoco"},
            {"EnvIdex": 3, "name": "HalfCheetah-v4", "extra": "gymnasium[mujoco] or mujoco"},
            {"EnvIdex": 4, "name": "BipedalWalker-v3", "extra": "gymnasium[box2d]"},
            {"EnvIdex": 5, "name": "BipedalWalkerHardcore-v3", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "--Distribution Beta, GS_ms, or GS_m selects actor distribution.",
    },
    {
        "key": "ddpg-td3-sac-continuous",
        "sub_skill": "policy-and-actor-critic-control",
        "directory_label": "4.1 DDPG / 4.2 TD3 / 5.2 SAC-Continuous",
        "implementation": "DDPG_agent, TD3_agent, SAC_countinuous",
        "action_space": "continuous",
        "envs": [
            {"EnvIdex": 0, "name": "Pendulum-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLanderContinuous-v2", "extra": "gymnasium[box2d]"},
            {"EnvIdex": 2, "name": "Humanoid-v4", "extra": "gymnasium[mujoco] or mujoco"},
            {"EnvIdex": 3, "name": "HalfCheetah-v4", "extra": "gymnasium[mujoco] or mujoco"},
            {"EnvIdex": 4, "name": "BipedalWalker-v3", "extra": "gymnasium[box2d]"},
            {"EnvIdex": 5, "name": "BipedalWalkerHardcore-v3", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "off-policy actor-critic methods with replay buffers and model/ checkpoint files per algorithm directory.",
    },
    {
        "key": "sac-discrete",
        "sub_skill": "policy-and-actor-critic-control",
        "directory_label": "5.1 SAC-Discrete",
        "implementation": "SACD_agent",
        "action_space": "discrete",
        "envs": [
            {"EnvIdex": 0, "name": "CartPole-v1", "extra": "base gymnasium"},
            {"EnvIdex": 1, "name": "LunarLander-v2", "extra": "gymnasium[box2d]"},
        ],
        "safe_smoke": "python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0",
        "notes": "discrete entropy-regularized actor-critic with optional adaptive alpha.",
    },
    {
        "key": "atari-dqn",
        "sub_skill": "atari-and-asl-workflows",
        "directory_label": "2.2_Noisy-Duel-DDQN-Atari",
        "implementation": "DeepQ_Agent with Q_Net or Duel_Q_Net",
        "action_space": "Atari discrete image observations",
        "envs": [
            {"EnvIdex": 20, "name": "EnduroNoFrameskip-v4", "extra": "gymnasium[atari], accept-rom-license, opencv-python"},
            {"EnvIdex": 37, "name": "PongNoFrameskip-v4", "extra": "gymnasium[atari], accept-rom-license, opencv-python"},
        ],
        "safe_smoke": "python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root>",
        "notes": "real env creation is ROM/license gated; flags --Double/--Duel/--Noisy choose variants.",
    },
    {
        "key": "asl-envpool",
        "sub_skill": "atari-and-asl-workflows",
        "directory_label": "6. Actor-Sharer-Learner",
        "implementation": "Actor, Sharer, Learner, Evaluator, Recorder processes",
        "action_space": "Atari discrete image observations via EnvPool",
        "envs": [{"EnvIdex": 1, "name": "Alien-v5 by default", "extra": "envpool + Atari support"}],
        "safe_smoke": "python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root> --probe-asl-sharer",
        "notes": "full ASL launch is long-running multiprocessing training, not a smoke test.",
    },
]


def print_table(rows: list[dict[str, Any]]) -> None:
    headers = ["key", "sub_skill", "directory_label", "action_space"]
    widths = {h: max(len(h), *(len(str(row[h])) for row in rows)) for h in headers}
    print(" | ".join(h.ljust(widths[h]) for h in headers))
    print("-+-".join("-" * widths[h] for h in headers))
    for row in rows:
        print(" | ".join(str(row[h]).ljust(widths[h]) for h in headers))


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the DRL-Pytorch algorithm routing matrix.")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format. Default: table.")
    parser.add_argument("--sub-skill", choices=sorted({row["sub_skill"] for row in ALGORITHMS}), help="Filter to one sub-skill owner.")
    args = parser.parse_args()
    rows = [row for row in ALGORITHMS if args.sub_skill is None or row["sub_skill"] == args.sub_skill]
    if args.format == "json":
        print(json.dumps(rows, indent=2))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
