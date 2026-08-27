#!/usr/bin/env python3
"""Safe tabular-control demo for Q-learning and Sarsa.

The helper keeps the 1D chain examples self-contained, avoids auto-running on
import, and leaves plotting out of the default path.
"""

from __future__ import annotations

import argparse
import time
from typing import Iterable

import numpy as np

ACTIONS = ("left", "right")
LEFT = 0
RIGHT = 1

ALGORITHM_ALIASES = {
    "q_learning": "q_learning",
    "q-learning": "q_learning",
    "sarsa": "sarsa",
    "both": "both",
}


def build_q_table(n_state: int, n_actions: int = len(ACTIONS)) -> np.ndarray:
    if n_state < 2:
        raise ValueError("n_state must be at least 2 so a terminal state exists")
    if n_actions != len(ACTIONS):
        raise ValueError("The bundled demo expects exactly two actions: left and right")
    return np.zeros((n_state, n_actions), dtype=float)


def choose_action(
    q_table: np.ndarray,
    state: int,
    epsilon: float,
    rng: np.random.Generator,
) -> int:
    row = q_table[state]
    if np.allclose(row, 0.0) or rng.random() < epsilon:
        return int(rng.integers(row.shape[0]))
    greedy = np.flatnonzero(row == row.max())
    return int(rng.choice(greedy))


def transition_line_world(state: int, action: int, n_state: int) -> tuple[int, float, bool]:
    terminal_state = n_state - 1
    if action not in (LEFT, RIGHT):
        raise ValueError(f"Unknown action index {action!r}; expected 0 for left or 1 for right")

    if action == RIGHT:
        if state >= n_state - 2:
            return terminal_state, 1.0, True
        return state + 1, -0.5, False

    if state == 0:
        return 0, -0.5, False
    return state - 1, -0.5, False


def render_chain(state: int, n_state: int, done: bool = False) -> str:
    cells = ["-"] * (n_state - 1) + ["T"]
    if done:
        cells[-1] = "T"
    else:
        cells[state] = "*"
    return "".join(cells)


def format_q_table(q_table: np.ndarray) -> str:
    header = "state " + " ".join(f"{name:>12}" for name in ACTIONS)
    rows = [header]
    for idx, row in enumerate(q_table):
        rows.append(f"{idx:>5} " + " ".join(f"{value:12.4f}" for value in row))
    return "\n".join(rows)


def run_episode(
    algorithm: str,
    q_table: np.ndarray,
    n_state: int,
    alpha: float,
    gamma: float,
    epsilon: float,
    rng: np.random.Generator,
    render: bool = False,
    delay: float = 0.0,
    max_steps: int | None = None,
) -> int:
    if algorithm not in {"q_learning", "sarsa"}:
        raise ValueError(f"Unsupported algorithm {algorithm!r}")

    if max_steps is None:
        max_steps = max(1, 10 * n_state)

    state = 0
    action = choose_action(q_table, state, epsilon, rng)
    steps = 0

    if render:
        print(render_chain(state, n_state))

    while True:
        next_state, reward, done = transition_line_world(state, action, n_state)

        if algorithm == "q_learning":
            target = reward if done else reward + gamma * float(np.max(q_table[next_state]))
            next_action = None
        else:
            if done:
                target = reward
                next_action = None
            else:
                next_action = choose_action(q_table, next_state, epsilon, rng)
                target = reward + gamma * q_table[next_state, next_action]

        q_table[state, action] += alpha * (target - q_table[state, action])
        steps += 1
        state = next_state

        if render:
            print(render_chain(state, n_state, done=done))
            if delay > 0.0:
                time.sleep(delay)

        if done:
            break
        if steps >= max_steps:
            raise RuntimeError(
                "Episode exceeded max_steps; check terminal handling or policy parameters"
            )

        if algorithm == "q_learning":
            action = choose_action(q_table, state, epsilon, rng)
        else:
            action = int(next_action)

    return steps


def run_training(
    algorithm: str,
    episodes: int,
    n_state: int,
    alpha: float,
    gamma: float,
    epsilon: float,
    seed: int,
    render: bool = False,
    delay: float = 0.0,
    max_steps: int | None = None,
) -> tuple[np.ndarray, list[int]]:
    if episodes < 1:
        raise ValueError("episodes must be at least 1")

    q_table = build_q_table(n_state)
    step_counts: list[int] = []
    rng = np.random.default_rng(seed)

    for _ in range(episodes):
        steps = run_episode(
            algorithm=algorithm,
            q_table=q_table,
            n_state=n_state,
            alpha=alpha,
            gamma=gamma,
            epsilon=epsilon,
            rng=rng,
            render=render,
            delay=delay,
            max_steps=max_steps,
        )
        step_counts.append(steps)

    return q_table, step_counts


def print_summary(name: str, q_table: np.ndarray, step_counts: list[int]) -> None:
    average_steps = float(np.mean(step_counts)) if step_counts else float("nan")
    print(f"\n{name}")
    print(f"step counts: {step_counts}")
    print(f"average steps: {average_steps:.2f}")
    print(format_q_table(q_table))


def normalize_algorithm(value: str) -> str:
    key = value.strip().lower()
    if key not in ALGORITHM_ALIASES:
        allowed = ", ".join(sorted(ALGORITHM_ALIASES))
        raise ValueError(f"Unknown algorithm {value!r}. Expected one of: {allowed}")
    return ALGORITHM_ALIASES[key]


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--algorithm",
        default="q_learning",
        help="q_learning, q-learning, sarsa, or both",
    )
    parser.add_argument("--episodes", type=int, default=20, help="Number of episodes to run")
    parser.add_argument("--n-state", type=int, default=6, help="Number of states in the chain")
    parser.add_argument("--alpha", type=float, default=0.1, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.1,
        help="Exploration probability for epsilon-greedy action selection",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--render", action="store_true", help="Print the chain after each step")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Optional sleep time after each rendered step",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Episode guardrail; defaults to 10 * n_state",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    algorithm = normalize_algorithm(args.algorithm)

    if algorithm == "both":
        q_table, q_steps = run_training(
            algorithm="q_learning",
            episodes=args.episodes,
            n_state=args.n_state,
            alpha=args.alpha,
            gamma=args.gamma,
            epsilon=args.epsilon,
            seed=args.seed,
            render=args.render,
            delay=args.delay,
            max_steps=args.max_steps,
        )
        sarsa_table, sarsa_steps = run_training(
            algorithm="sarsa",
            episodes=args.episodes,
            n_state=args.n_state,
            alpha=args.alpha,
            gamma=args.gamma,
            epsilon=args.epsilon,
            seed=args.seed,
            render=args.render,
            delay=args.delay,
            max_steps=args.max_steps,
        )
        print_summary("Q-learning", q_table, q_steps)
        print_summary("Sarsa", sarsa_table, sarsa_steps)
        return 0

    q_table, step_counts = run_training(
        algorithm=algorithm,
        episodes=args.episodes,
        n_state=args.n_state,
        alpha=args.alpha,
        gamma=args.gamma,
        epsilon=args.epsilon,
        seed=args.seed,
        render=args.render,
        delay=args.delay,
        max_steps=args.max_steps,
    )
    display_name = "Q-learning" if algorithm == "q_learning" else "Sarsa"
    print_summary(display_name, q_table, step_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
