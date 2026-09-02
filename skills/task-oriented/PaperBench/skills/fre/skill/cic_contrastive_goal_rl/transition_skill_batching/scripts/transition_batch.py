#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from typing import Iterable, List, Sequence

Matrix = List[List[float]]


def _as_matrix(name: str, value: Sequence[Sequence[float]]) -> Matrix:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{name} must be a non-empty 2D numeric sequence")
    rows: Matrix = []
    width = None
    for row in value:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or not row:
            raise ValueError(f"{name} rows must be non-empty numeric sequences")
        converted = []
        for item in row:
            number = float(item)
            if not math.isfinite(number):
                raise ValueError(f"{name} contains a non-finite value")
            converted.append(number)
        if width is None:
            width = len(converted)
        elif len(converted) != width:
            raise ValueError(f"{name} must be rectangular")
        rows.append(converted)
    return rows


def build_transition_skill_batch(states: Sequence[Sequence[float]], next_states: Sequence[Sequence[float]], skills: Sequence[Sequence[float]], source: str = "provided") -> dict:
    state_rows = _as_matrix("states", states)
    next_rows = _as_matrix("next_states", next_states)
    skill_rows = _as_matrix("skills", skills)
    if len(state_rows) != len(next_rows) or len(state_rows[0]) != len(next_rows[0]):
        raise ValueError("states and next_states must have identical shapes")
    if len(skill_rows) != len(state_rows):
        raise ValueError("skills must have the same batch size as states")
    tau = [s + ns for s, ns in zip(state_rows, next_rows)]
    return {
        "tau": tau,
        "states": state_rows,
        "next_states": next_rows,
        "skills": skill_rows,
        "metadata": {
            "batch_size": len(state_rows),
            "state_dim": len(state_rows[0]),
            "skill_dim": len(skill_rows[0]),
            "transition_dim": len(tau[0]),
            "source": source,
        },
    }


def deterministic_synthetic_batch(batch_size: int = 8, state_dim: int = 3, skill_dim: int = 3, seed: int = 7) -> dict:
    if batch_size < 2:
        raise ValueError("batch_size must be at least 2")
    if state_dim < 1 or skill_dim < 1:
        raise ValueError("state_dim and skill_dim must be positive")
    rng = random.Random(seed)
    states: Matrix = []
    next_states: Matrix = []
    skills: Matrix = []
    for index in range(batch_size):
        skill = [0.0 for _ in range(skill_dim)]
        skill[index % skill_dim] = 1.0
        skill = [value + 0.05 * rng.uniform(-1.0, 1.0) for value in skill]
        state = [0.25 * (index + 1) + 0.1 * dim for dim in range(state_dim)]
        delta = [0.15 * skill[dim % skill_dim] + 0.03 * (index + 1) for dim in range(state_dim)]
        next_state = [state[dim] + delta[dim] for dim in range(state_dim)]
        states.append(state)
        next_states.append(next_state)
        skills.append(skill)
    return build_transition_skill_batch(states, next_states, skills, source="deterministic_synthetic")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CIC transition-skill batch.")
    parser.add_argument("--demo", action="store_true", help="Emit a deterministic synthetic batch as JSON.")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--state-dim", type=int, default=3)
    parser.add_argument("--skill-dim", type=int, default=3)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if not args.demo:
        parser.error("Only --demo mode is provided for CLI use; import functions for custom arrays.")
    print(json.dumps(deterministic_synthetic_batch(args.batch_size, args.state_dim, args.skill_dim, args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
