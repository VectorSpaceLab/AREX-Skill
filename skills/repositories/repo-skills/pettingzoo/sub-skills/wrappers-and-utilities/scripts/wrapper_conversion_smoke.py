#!/usr/bin/env python3
"""Bounded PettingZoo wrapper/conversion smoke check.

This script defines a tiny Parallel rock-paper-scissors-like environment using
only PettingZoo base dependencies, converts it to AEC with ``parallel_to_aec``,
converts it back with ``aec_to_parallel`` where valid, and runs short deterministic
rollouts through both APIs.
"""

from __future__ import annotations

import argparse
import functools
from typing import Any

ROCK = 0
PAPER = 1
SCISSORS = 2
NO_MOVE = 3
MOVES = ("rock", "paper", "scissors", "none")
REWARD_MAP = {
    (ROCK, ROCK): (0, 0),
    (ROCK, PAPER): (-1, 1),
    (ROCK, SCISSORS): (1, -1),
    (PAPER, ROCK): (1, -1),
    (PAPER, PAPER): (0, 0),
    (PAPER, SCISSORS): (-1, 1),
    (SCISSORS, ROCK): (-1, 1),
    (SCISSORS, PAPER): (1, -1),
    (SCISSORS, SCISSORS): (0, 0),
}


def build_tiny_parallel_rps_class(parallel_env_base: type, numpy_module: Any, discrete_space: type) -> type:
    class TinyParallelRPS(parallel_env_base):
        """Small deterministic Parallel env for conversion smoke checks."""

        metadata = {"name": "tiny_parallel_rps_v0", "render_modes": ["ansi"]}

        def __init__(self, max_cycles: int = 3, render_mode: str | None = None):
            self.possible_agents = ["player_0", "player_1"]
            self.agents: list[str] = []
            self.max_cycles = max(1, int(max_cycles))
            self.render_mode = render_mode
            self.state = {
                agent: numpy_module.array(NO_MOVE, dtype=numpy_module.int64)
                for agent in self.possible_agents
            }
            self.num_cycles = 0

        @functools.lru_cache(maxsize=None)
        def observation_space(self, agent: str) -> Any:
            self._require_known_agent(agent)
            return discrete_space(4)

        @functools.lru_cache(maxsize=None)
        def action_space(self, agent: str) -> Any:
            self._require_known_agent(agent)
            return discrete_space(3)

        def reset(
            self, seed: int | None = None, options: dict[str, Any] | None = None
        ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
            del options
            if seed is not None:
                for index, agent in enumerate(self.possible_agents):
                    self.action_space(agent).seed(seed + index)
            self.agents = self.possible_agents[:]
            self.num_cycles = 0
            self.state = {
                agent: numpy_module.array(NO_MOVE, dtype=numpy_module.int64)
                for agent in self.agents
            }
            observations = {agent: value.copy() for agent, value in self.state.items()}
            infos = {agent: {} for agent in self.agents}
            return observations, infos

        def step(
            self, actions: dict[str, int]
        ) -> tuple[
            dict[str, Any],
            dict[str, float],
            dict[str, bool],
            dict[str, bool],
            dict[str, dict[str, Any]],
        ]:
            if not self.agents:
                return {}, {}, {}, {}, {}

            expected = set(self.agents)
            received = set(actions)
            if received != expected:
                raise AssertionError(f"expected actions for {sorted(expected)}, got {sorted(received)}")

            for agent, action in actions.items():
                if not self.action_space(agent).contains(action):
                    raise AssertionError(f"action {action!r} for {agent} is outside Discrete(3)")

            player_0, player_1 = self.agents
            reward_0, reward_1 = REWARD_MAP[(int(actions[player_0]), int(actions[player_1]))]
            rewards = {player_0: float(reward_0), player_1: float(reward_1)}

            self.num_cycles += 1
            truncated = self.num_cycles >= self.max_cycles
            terminations = {agent: False for agent in self.agents}
            truncations = {agent: truncated for agent in self.agents}
            observations = {
                player_0: numpy_module.array(actions[player_1], dtype=numpy_module.int64),
                player_1: numpy_module.array(actions[player_0], dtype=numpy_module.int64),
            }
            self.state = {agent: value.copy() for agent, value in observations.items()}
            infos = {agent: {"cycle": self.num_cycles} for agent in self.agents}

            if truncated:
                self.agents = []

            return observations, rewards, terminations, truncations, infos

        def render(self) -> str | None:
            if self.render_mode != "ansi":
                return None
            return ", ".join(f"{agent} saw {MOVES[int(obs)]}" for agent, obs in self.state.items())

        def close(self) -> None:
            return None

        @property
        def unwrapped(self) -> Any:
            return self

        def _require_known_agent(self, agent: str) -> None:
            if agent not in self.possible_agents:
                raise KeyError(f"unknown agent {agent!r}")

    return TinyParallelRPS


def run_parallel(env: Any, cycles: int, seed: int) -> dict[str, Any]:
    observations, infos = env.reset(seed=seed)
    total_rewards = {agent: 0.0 for agent in env.agents}
    steps = 0
    while env.agents and steps < cycles:
        actions = {agent: (steps + index) % 3 for index, agent in enumerate(env.agents)}
        observations, rewards, terminations, truncations, infos = env.step(actions)
        for agent, reward in rewards.items():
            total_rewards[agent] = total_rewards.get(agent, 0.0) + float(reward)
        steps += 1
        if all(terminations.values()) or all(truncations.values()):
            break
    return {
        "steps": steps,
        "remaining_agents": list(env.agents),
        "total_rewards": total_rewards,
        "last_observation_keys": sorted(observations),
        "last_info_keys": sorted(infos),
    }


def run_aec(aec_env: Any, max_agent_steps: int, seed: int) -> dict[str, Any]:
    aec_env.reset(seed=seed)
    total_rewards = {agent: 0.0 for agent in aec_env.agents}
    agent_steps = 0
    for agent in aec_env.agent_iter(max_iter=max_agent_steps):
        observation, reward, termination, truncation, info = aec_env.last()
        del observation, info
        total_rewards[agent] = total_rewards.get(agent, 0.0) + float(reward)
        if termination or truncation:
            action = None
        else:
            action = agent_steps % 3
        aec_env.step(action)
        agent_steps += 1
    return {
        "agent_steps": agent_steps,
        "remaining_agents": list(aec_env.agents),
        "total_rewards": total_rewards,
        "metadata_is_parallelizable": bool(aec_env.metadata.get("is_parallelizable", False)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded PettingZoo wrapper conversion smoke check using a tiny Parallel RPS env."
    )
    parser.add_argument("--cycles", type=int, default=3, help="Maximum Parallel cycles to run; default: 3.")
    parser.add_argument(
        "--aec-agent-steps",
        type=int,
        default=12,
        help="Maximum AEC agent_iter steps to run after parallel_to_aec; default: 12.",
    )
    parser.add_argument("--seed", type=int, default=123, help="Deterministic seed for action spaces; default: 123.")
    return parser.parse_args()


def import_runtime_dependencies() -> tuple[Any, type, type, Any, Any]:
    try:
        import numpy as np
        from gymnasium.spaces import Discrete
        from pettingzoo import ParallelEnv
        from pettingzoo.utils import aec_to_parallel, parallel_to_aec
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for smoke execution. Install PettingZoo with its base "
            f"dependencies, then rerun this script. Original error: {exc}"
        ) from exc
    return np, Discrete, ParallelEnv, aec_to_parallel, parallel_to_aec


def main() -> int:
    args = parse_args()
    np, Discrete, ParallelEnv, aec_to_parallel, parallel_to_aec = import_runtime_dependencies()
    TinyParallelRPS = build_tiny_parallel_rps_class(ParallelEnv, np, Discrete)
    cycles = max(1, args.cycles)
    aec_agent_steps = max(1, args.aec_agent_steps)

    parallel_env = TinyParallelRPS(max_cycles=cycles, render_mode="ansi")
    parallel_summary = run_parallel(parallel_env, cycles=cycles, seed=args.seed)

    aec_env = parallel_to_aec(TinyParallelRPS(max_cycles=cycles, render_mode="ansi"))
    aec_summary = run_aec(aec_env, max_agent_steps=aec_agent_steps, seed=args.seed)

    roundtrip_parallel_env = aec_to_parallel(aec_env)
    roundtrip_summary = run_parallel(roundtrip_parallel_env, cycles=cycles, seed=args.seed)

    print("PettingZoo wrapper conversion smoke passed")
    print(f"parallel: steps={parallel_summary['steps']} rewards={parallel_summary['total_rewards']}")
    print(
        "parallel_to_aec: "
        f"agent_steps={aec_summary['agent_steps']} "
        f"is_parallelizable={aec_summary['metadata_is_parallelizable']} "
        f"rewards={aec_summary['total_rewards']}"
    )
    print(
        "aec_to_parallel roundtrip: "
        f"steps={roundtrip_summary['steps']} rewards={roundtrip_summary['total_rewards']}"
    )
    print(f"ansi render sample: {roundtrip_parallel_env.render()}")

    parallel_env.close()
    aec_env.close()
    roundtrip_parallel_env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
