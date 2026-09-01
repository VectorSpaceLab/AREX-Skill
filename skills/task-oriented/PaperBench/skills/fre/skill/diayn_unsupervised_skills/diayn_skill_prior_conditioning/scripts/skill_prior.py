#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from typing import Any


def one_hot(index: int, size: int) -> list[int]:
    return [1 if i == index else 0 for i in range(size)]


def build_skill_schedule(num_skills: int, episodes: int, horizon: int, seed: int = 0) -> dict[str, Any]:
    if num_skills <= 0 or episodes <= 0 or horizon <= 0:
        raise ValueError("num_skills, episodes, and horizon must be positive")
    rng = random.Random(seed)
    skills = [rng.randrange(num_skills) for _ in range(episodes)]
    log_prior = -math.log(num_skills)
    records = []
    for episode, skill in enumerate(skills):
        for timestep in range(horizon):
            records.append({
                "episode": episode,
                "timestep": timestep,
                "skill": skill,
                "conditioning": one_hot(skill, num_skills),
                "log_prior": log_prior,
            })
    return {
        "num_skills": num_skills,
        "episodes": episodes,
        "horizon": horizon,
        "seed": seed,
        "skills": skills,
        "prior": [1.0 / num_skills for _ in range(num_skills)],
        "log_prior": log_prior,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-skills", type=int, required=True)
    parser.add_argument("--episodes", type=int, required=True)
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(build_skill_schedule(args.num_skills, args.episodes, args.horizon, args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
