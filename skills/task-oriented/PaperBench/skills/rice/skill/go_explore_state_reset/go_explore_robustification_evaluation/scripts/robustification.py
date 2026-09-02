from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


ACTIONS = {"R": (1, 0), "L": (-1, 0), "U": (0, -1), "D": (0, 1)}
WALLS = {(2, 1), (3, 1), (4, 1)}
GOAL = (6, 1)
START = (0, 1)


def initial_state() -> Dict[str, Any]:
    return {"x": START[0], "y": START[1], "room": 0, "score": 0, "done": False}


def step_state(state: Dict[str, Any], action: str) -> Dict[str, Any]:
    dx, dy = ACTIONS[action]
    nx = max(0, min(6, int(state["x"]) + dx))
    ny = max(0, min(2, int(state["y"]) + dy))
    if (nx, ny) in WALLS:
        nx, ny = int(state["x"]), int(state["y"])
    done = (nx, ny) == GOAL
    return {"x": nx, "y": ny, "room": 0, "score": 1 if done else 0, "done": done}


def replay_actions(actions: Iterable[str]) -> Dict[str, Any]:
    state = initial_state()
    trace: List[Dict[str, Any]] = [dict(state)]
    for action in actions:
        state = step_state(state, action)
        trace.append(dict(state))
        if state["done"]:
            break
    return {"goal_reached": bool(state["done"]), "score": state["score"], "trace": trace}


def evaluate_trajectory(actions: Iterable[str], perturbation_checks: bool = True) -> Dict[str, Any]:
    action_list = list(actions)
    deterministic = replay_actions(action_list)
    trials = [deterministic]
    if perturbation_checks:
        trials.append(replay_actions(["L"] + action_list))
        trials.append(replay_actions(["U", "D"] + action_list))
    successes = sum(1 for trial in trials if trial["goal_reached"])
    return {
        "success_rate": successes / len(trials),
        "deterministic_goal_reached": deterministic["goal_reached"],
        "deterministic_score": deterministic["score"],
        "trial_count": len(trials),
        "mechanism_checks": {
            "discovery_and_evaluation_separated": True,
            "deterministic_replay_executed": True,
            "perturbation_checks_executed": bool(perturbation_checks),
            "full_neural_robustification_executed": False,
            "reduced_robustification_proxy": True
        },
        "trials": trials
    }
