#!/usr/bin/env python3
"""Fixture-friendly GridWorld helper adapted from the original repo.

The class keeps the source method names for compatibility while fixing the
scalar-action handling, the undefined-name position bug, and the render side
effects that make the original helper awkward to reuse in tests.
"""

from __future__ import annotations

import argparse
import time
from typing import Iterable

import numpy as np


class GridWorld:
    def __init__(self, tot_row: int, tot_col: int, seed: int | None = None):
        if tot_row < 1 or tot_col < 1:
            raise ValueError("GridWorld dimensions must be positive")

        self.action_space_size = 4
        self.world_row = int(tot_row)
        self.world_col = int(tot_col)
        self.rng = np.random.default_rng(seed)
        self.transition_matrix = np.ones((self.action_space_size, self.action_space_size), dtype=float)
        self.transition_matrix /= self.action_space_size
        self.reward_matrix = np.zeros((self.world_row, self.world_col), dtype=float)
        self.state_matrix = np.zeros((self.world_row, self.world_col), dtype=int)
        self.position = [int(self.rng.integers(self.world_row)), int(self.rng.integers(self.world_col))]

    def set_transition_matrix(self, transition_matrix: np.ndarray) -> None:
        transition_matrix = np.asarray(transition_matrix, dtype=float)
        expected = self.transition_matrix.shape
        if transition_matrix.shape != expected:
            raise ValueError(f"The transition matrix must have shape {expected}, got {transition_matrix.shape}")
        row_sums = transition_matrix.sum(axis=1)
        if not np.allclose(row_sums, 1.0):
            raise ValueError("Each transition-matrix row must sum to 1.0")
        self.transition_matrix = transition_matrix

    def set_reward_matrix(self, reward_matrix: np.ndarray) -> None:
        reward_matrix = np.asarray(reward_matrix, dtype=float)
        expected = self.reward_matrix.shape
        if reward_matrix.shape != expected:
            raise ValueError(f"The reward matrix must have shape {expected}, got {reward_matrix.shape}")
        self.reward_matrix = reward_matrix

    def set_state_matrix(self, state_matrix: np.ndarray) -> None:
        state_matrix = np.asarray(state_matrix, dtype=int)
        expected = self.state_matrix.shape
        if state_matrix.shape != expected:
            raise ValueError(f"The state matrix must have shape {expected}, got {state_matrix.shape}")
        self.state_matrix = state_matrix

    def set_position(self, index_row: int | None = None, index_col: int | None = None) -> None:
        if index_row is None or index_col is None:
            self.position = [int(self.rng.integers(self.world_row)), int(self.rng.integers(self.world_col))]
            return

        row = int(index_row)
        col = int(index_col)
        if not (0 <= row < self.world_row and 0 <= col < self.world_col):
            raise ValueError("Position is outside the world bounds")
        self.position = [row, col]

    def reset(self, exploring_starts: bool = False):
        if exploring_starts:
            free_cells = np.argwhere(self.state_matrix == 0)
            if free_cells.size == 0:
                raise ValueError("No walkable cells are available for exploring starts")
            row, col = free_cells[self.rng.integers(len(free_cells))]
            self.position = [int(row), int(col)]
        else:
            self.position = [self.world_row - 1, 0]
        return self.position.copy()

    def step(self, action):
        action = int(np.asarray(action).item())
        if action < 0 or action >= self.action_space_size:
            raise ValueError("The action is not included in the action space")

        actual_action = int(self.rng.choice(self.action_space_size, p=self.transition_matrix[action]))

        if actual_action == 0:
            new_position = [self.position[0] - 1, self.position[1]]
        elif actual_action == 1:
            new_position = [self.position[0], self.position[1] + 1]
        elif actual_action == 2:
            new_position = [self.position[0] + 1, self.position[1]]
        elif actual_action == 3:
            new_position = [self.position[0], self.position[1] - 1]
        else:
            raise ValueError("The action is not included in the action space")

        if 0 <= new_position[0] < self.world_row and 0 <= new_position[1] < self.world_col:
            if self.state_matrix[new_position[0], new_position[1]] != -1:
                self.position = new_position

        reward = float(self.reward_matrix[self.position[0], self.position[1]])
        done = bool(self.state_matrix[self.position[0], self.position[1]] == 1)
        return self.position.copy(), reward, done

    def as_ascii(self) -> str:
        lines = []
        for row in range(self.world_row):
            cells = []
            for col in range(self.world_col):
                if self.position == [row, col]:
                    cells.append(" O ")
                elif self.state_matrix[row, col] == -1:
                    cells.append(" # ")
                elif self.state_matrix[row, col] == 1:
                    cells.append(" * ")
                else:
                    cells.append(" - ")
            lines.append("".join(cells))
        return "\n".join(lines)

    def render(self, delay: float = 0.0, stream=None) -> str:
        text = self.as_ascii()
        print(text, file=stream)
        if delay > 0.0:
            time.sleep(delay)
        return text

    # Compatibility aliases that preserve the source method names.
    setTransitionMatrix = set_transition_matrix
    setRewardMatrix = set_reward_matrix
    setStateMatrix = set_state_matrix
    setPosition = set_position


def build_demo_world(rows: int, cols: int, seed: int | None = None) -> GridWorld:
    world = GridWorld(rows, cols, seed=seed)
    state = np.zeros((rows, cols), dtype=int)
    reward = np.zeros((rows, cols), dtype=float)
    state[0, cols - 1] = 1
    reward[0, cols - 1] = 1.0
    if rows > 1 and cols > 1:
        state[1, 1] = -1
    world.set_state_matrix(state)
    world.set_reward_matrix(reward)
    return world


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Load a tiny terminal-and-obstacle demo world")
    parser.add_argument("--rows", type=int, default=4, help="World height")
    parser.add_argument("--cols", type=int, default=3, help="World width")
    parser.add_argument("--steps", type=int, default=5, help="Number of random steps to take in demo mode")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--delay", type=float, default=0.0, help="Optional render delay")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    world = build_demo_world(args.rows, args.cols, seed=args.seed) if args.demo else GridWorld(args.rows, args.cols, seed=args.seed)

    start = world.reset(exploring_starts=args.demo)
    print(f"start={start}")
    world.render(delay=args.delay)

    if args.demo:
        for _ in range(args.steps):
            action = int(world.rng.integers(world.action_space_size))
            position, reward, done = world.step(action)
            print(f"action={action} -> position={position} reward={reward} done={done}")
            world.render(delay=args.delay)
            if done:
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
