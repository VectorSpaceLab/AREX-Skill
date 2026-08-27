#!/usr/bin/env python3
"""Safe PettingZoo custom environment template with bounded smoke runs.

The module exposes the usual PettingZoo factories:
- parallel_env(...): bare ParallelEnv implementation.
- raw_env(...): AEC conversion of the parallel environment.
- env(...): user-facing AEC environment with common wrappers.

Run examples:
    python custom_env_template.py --mode parallel --cycles 3 --seed 7
    python custom_env_template.py --mode aec --cycles 6 --seed 7 --action-masks
"""

from __future__ import annotations

import argparse
import functools
import sys
from typing import Any

try:
    import numpy as np
    from gymnasium import spaces
    from gymnasium.utils import seeding
    from pettingzoo import ParallelEnv
    from pettingzoo.utils import parallel_to_aec, wrappers
except ModuleNotFoundError as exc:
    if "--help" in sys.argv or "-h" in sys.argv:
        np = spaces = seeding = parallel_to_aec = wrappers = None  # type: ignore[assignment]

        class ParallelEnv:  # type: ignore[no-redef]
            pass
    else:
        raise SystemExit(
            f"Missing required package {exc.name!r}. Install PettingZoo with its base "
            "dependencies before running this template smoke test."
        ) from exc

GRID_SIZE = 5
GRID_CELLS = GRID_SIZE * GRID_SIZE
DEFAULT_CYCLES = 8
MAX_SMOKE_CYCLES = 1000
RUNNER = "runner"
CATCHER = "catcher"
ACTIONS = {
    0: (-1, 0, "up"),
    1: (1, 0, "down"),
    2: (0, -1, "left"),
    3: (0, 1, "right"),
    4: (0, 0, "stay"),
}


def env(render_mode: str | None = None, max_cycles: int = DEFAULT_CYCLES, action_masks: bool = False):
    """Return a wrapped AEC environment for normal users."""
    internal_render_mode = "human" if render_mode == "ansi" else render_mode
    aec_env = raw_env(
        render_mode=internal_render_mode,
        max_cycles=max_cycles,
        action_masks=action_masks,
    )
    if render_mode == "ansi":
        aec_env = wrappers.CaptureStdoutWrapper(aec_env)
    aec_env = wrappers.AssertOutOfBoundsWrapper(aec_env)
    aec_env = wrappers.OrderEnforcingWrapper(aec_env)
    return aec_env


def raw_env(render_mode: str | None = None, max_cycles: int = DEFAULT_CYCLES, action_masks: bool = False):
    """Return the AEC conversion of the bare parallel environment."""
    return parallel_to_aec(
        parallel_env(
            render_mode=render_mode,
            max_cycles=max_cycles,
            action_masks=action_masks,
        )
    )


class parallel_env(ParallelEnv):
    """Tiny simultaneous-move grid game for custom-env authoring."""

    metadata = {
        "name": "custom_grid_v0",
        "render_modes": ["human", "ansi"],
        "is_parallelizable": True,
    }

    def __init__(
        self,
        render_mode: str | None = None,
        max_cycles: int = DEFAULT_CYCLES,
        action_masks: bool = False,
    ):
        self.possible_agents = [RUNNER, CATCHER]
        self.agent_name_mapping = {agent: index for index, agent in enumerate(self.possible_agents)}
        self.render_mode = render_mode
        self.max_cycles = int(max_cycles)
        self.include_action_masks = bool(action_masks)
        self.agents: list[str] = []
        self.timestep = 0
        self.runner_pos = (0, 0)
        self.catcher_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.goal_pos = (0, GRID_SIZE - 1)
        self.np_random, self.np_random_seed = seeding.np_random(None)

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent: str):
        base_space = spaces.MultiDiscrete([GRID_CELLS, GRID_CELLS, GRID_CELLS, self.max_cycles + 1])
        if not self.include_action_masks:
            return base_space
        return spaces.Dict(
            {
                "observation": base_space,
                "action_mask": spaces.MultiBinary(len(ACTIONS)),
            }
        )

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent: str):
        return spaces.Discrete(len(ACTIONS))

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None):
        if seed is not None:
            self.np_random, self.np_random_seed = seeding.np_random(seed)
        self.agents = self.possible_agents[:]
        self.timestep = 0
        self.runner_pos = (0, 0)
        self.catcher_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.goal_pos = (0, GRID_SIZE - 1)
        observations = self._observations()
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    def step(self, actions: dict[str, int]):
        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}

        active_agents = self.agents[:]
        runner_action = int(actions.get(RUNNER, 4))
        catcher_action = int(actions.get(CATCHER, 4))

        self.runner_pos = self._move(self.runner_pos, runner_action)
        self.catcher_pos = self._move(self.catcher_pos, catcher_action)
        self.timestep += 1

        runner_escaped = self.runner_pos == self.goal_pos
        runner_caught = self.runner_pos == self.catcher_pos
        time_limit = self.timestep >= self.max_cycles

        rewards = {agent: 0.0 for agent in active_agents}
        if runner_escaped:
            rewards = {RUNNER: 1.0, CATCHER: -1.0}
        elif runner_caught:
            rewards = {RUNNER: -1.0, CATCHER: 1.0}

        terminations = {agent: bool(runner_escaped or runner_caught) for agent in active_agents}
        truncations = {agent: bool(time_limit and not terminations[agent]) for agent in active_agents}
        observations = self._observations(active_agents)
        infos = {agent: {} for agent in active_agents}

        if any(terminations.values()) or all(truncations.values()):
            self.agents = []

        if self.render_mode == "human":
            self.render()
        return observations, rewards, terminations, truncations, infos

    def render(self):
        rows = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        goal_row, goal_col = self.goal_pos
        runner_row, runner_col = self.runner_pos
        catcher_row, catcher_col = self.catcher_pos
        rows[goal_row][goal_col] = "G"
        rows[runner_row][runner_col] = "R"
        rows[catcher_row][catcher_col] = "C" if self.catcher_pos != self.runner_pos else "X"
        board = "\n".join(" ".join(row) for row in rows)
        text = f"t={self.timestep}\n{board}"
        if self.render_mode == "ansi":
            return text
        print(text)
        return None

    def close(self):
        return None

    def state(self):
        return np.array(
            [
                self._encode(self.runner_pos),
                self._encode(self.catcher_pos),
                self._encode(self.goal_pos),
                self.timestep,
            ],
            dtype=np.int64,
        )

    def _observations(self, agents: list[str] | None = None):
        selected_agents = self.agents if agents is None else agents
        base = np.array(
            [
                self._encode(self.runner_pos),
                self._encode(self.catcher_pos),
                self._encode(self.goal_pos),
                min(self.timestep, self.max_cycles),
            ],
            dtype=np.int64,
        )
        if not self.include_action_masks:
            return {agent: base.copy() for agent in selected_agents}
        return {
            agent: {
                "observation": base.copy(),
                "action_mask": self._action_mask(agent),
            }
            for agent in selected_agents
        }

    def _action_mask(self, agent: str):
        position = self.runner_pos if agent == RUNNER else self.catcher_pos
        mask = np.ones(len(ACTIONS), dtype=np.int8)
        row, col = position
        if row == 0:
            mask[0] = 0
        if row == GRID_SIZE - 1:
            mask[1] = 0
        if col == 0:
            mask[2] = 0
        if col == GRID_SIZE - 1:
            mask[3] = 0
        mask[4] = 1
        return mask

    @staticmethod
    def _encode(position: tuple[int, int]):
        return position[0] * GRID_SIZE + position[1]

    @staticmethod
    def _move(position: tuple[int, int], action: int):
        row_delta, col_delta, _ = ACTIONS.get(action, ACTIONS[4])
        row = min(max(position[0] + row_delta, 0), GRID_SIZE - 1)
        col = min(max(position[1] + col_delta, 0), GRID_SIZE - 1)
        return row, col


def _extract_mask(observation, info):
    if isinstance(observation, dict) and "action_mask" in observation:
        return np.asarray(observation["action_mask"], dtype=np.int8)
    if isinstance(info, dict) and "action_mask" in info:
        return np.asarray(info["action_mask"], dtype=np.int8)
    return None


def _sample_action(action_space, observation, info, rng: np.random.Generator):
    mask = _extract_mask(observation, info)
    if mask is not None:
        valid_actions = np.flatnonzero(mask)
        if len(valid_actions) == 0:
            raise RuntimeError("live agent received an all-zero action mask")
        return int(rng.choice(valid_actions))
    return int(rng.integers(action_space.n))


def run_parallel(cycles: int, seed: int, use_masks: bool):
    rng = np.random.default_rng(seed)
    env_obj = parallel_env(max_cycles=cycles, action_masks=use_masks)
    observations, infos = env_obj.reset(seed=seed)
    print(f"parallel reset agents={env_obj.agents} masks={use_masks}")
    for step_index in range(cycles):
        if not env_obj.agents:
            break
        actions = {
            agent: _sample_action(env_obj.action_space(agent), observations[agent], infos.get(agent, {}), rng)
            for agent in env_obj.agents
        }
        observations, rewards, terminations, truncations, infos = env_obj.step(actions)
        print(
            f"parallel step={step_index + 1} actions={actions} rewards={rewards} "
            f"terminations={terminations} truncations={truncations}"
        )
    env_obj.close()


def run_aec(cycles: int, seed: int, use_masks: bool):
    rng = np.random.default_rng(seed)
    env_obj = env(max_cycles=cycles, action_masks=use_masks)
    env_obj.reset(seed=seed)
    print(f"aec reset agents={env_obj.agents} masks={use_masks}")
    max_iter = cycles * max(1, len(env_obj.possible_agents)) + len(env_obj.possible_agents)
    for step_index, agent in enumerate(env_obj.agent_iter(max_iter=max_iter), start=1):
        observation, reward, termination, truncation, info = env_obj.last()
        if termination or truncation:
            action = None
        else:
            action = _sample_action(env_obj.action_space(agent), observation, info, rng)
        env_obj.step(action)
        print(
            f"aec step={step_index} agent={agent} action={action} reward={reward} "
            f"termination={termination} truncation={truncation}"
        )
    env_obj.close()


def positive_bounded_int(value: str):
    parsed = int(value)
    if parsed < 1 or parsed > MAX_SMOKE_CYCLES:
        raise argparse.ArgumentTypeError(f"value must be between 1 and {MAX_SMOKE_CYCLES}")
    return parsed


def build_parser():
    parser = argparse.ArgumentParser(description="Run a bounded smoke rollout for a minimal custom PettingZoo environment.")
    parser.add_argument("--mode", choices=["parallel", "aec"], default="parallel", help="API mode to smoke test.")
    parser.add_argument("--cycles", type=positive_bounded_int, default=DEFAULT_CYCLES, help="Bounded number of environment cycles.")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed for reset and random policy.")
    parser.add_argument("--action-masks", action="store_true", help="Emit observation-dictionary action masks and sample from them.")
    return parser


def main(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)
    if args.mode == "parallel":
        run_parallel(args.cycles, args.seed, args.action_masks)
    else:
        run_aec(args.cycles, args.seed, args.action_masks)


if __name__ == "__main__":
    main()
