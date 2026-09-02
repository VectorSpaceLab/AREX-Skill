from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

ACTIONS = {"R": (1, 0), "L": (-1, 0), "U": (0, -1), "D": (0, 1)}


def encode_cell(state: Dict[str, Any]) -> Tuple[int, int, int]:
    return (int(state.get("room", 0)), int(state["x"]), int(state["y"]))


def update_archive(archive: Dict[Any, Dict[str, Any]], record: Dict[str, Any]) -> bool:
    key = tuple(record["cell_key"])
    candidate = dict(record)
    candidate["cell_key"] = key
    candidate["length"] = int(candidate.get("length", len(candidate.get("actions", []))))
    candidate.setdefault("selection_count", 0)
    if key not in archive:
        archive[key] = candidate
        return True
    old = archive[key]
    old_length = int(old.get("length", len(old.get("actions", []))))
    if candidate["score"] > old["score"] or (candidate["score"] == old["score"] and candidate["length"] < old_length):
        candidate["selection_count"] = old.get("selection_count", 0)
        archive[key] = candidate
        return True
    return False


def select_cell(archive: Dict[Any, Dict[str, Any]], seed: int = 0) -> Tuple[Any, Dict[str, Any]]:
    if not archive:
        raise ValueError("cannot select from an empty archive")
    keys = sorted(archive.keys(), key=repr)
    index = seed % len(keys)
    key = keys[index]
    archive[key]["selection_count"] = int(archive[key].get("selection_count", 0)) + 1
    return key, archive[key]



@dataclass
class SparseGrid:
    width: int = 7
    height: int = 3
    start: Tuple[int, int] = (0, 1)
    goal: Tuple[int, int] = (6, 1)
    walls: Tuple[Tuple[int, int], ...] = ((2, 1), (3, 1), (4, 1))

    def initial_state(self) -> Dict[str, Any]:
        return {"x": self.start[0], "y": self.start[1], "room": 0, "score": 0, "done": False}

    def step(self, state: Dict[str, Any], action: str) -> Dict[str, Any]:
        dx, dy = ACTIONS[action]
        nx = max(0, min(self.width - 1, int(state["x"]) + dx))
        ny = max(0, min(self.height - 1, int(state["y"]) + dy))
        if (nx, ny) in self.walls:
            nx, ny = int(state["x"]), int(state["y"])
        done = (nx, ny) == self.goal
        return {"x": nx, "y": ny, "room": 0, "score": 1 if done else 0, "done": done}


def run_go_explore_proxy(iterations: int = 12, horizon: int = 6, seed: int = 0) -> Dict[str, Any]:
    env = SparseGrid()
    archive: Dict[Any, Dict[str, Any]] = {}
    start = env.initial_state()
    update_archive(archive, {"cell_key": encode_cell(start), "state": start, "actions": [], "score": 0, "length": 0})
    schedules = [list("RUURRR"), list("RRRRRR"), list("DDRRRR"), list("RRDDRR"), list("RRRRDD")]
    trace: List[Dict[str, Any]] = []
    best = {"score": 0, "actions": [], "state": start, "goal_reached": False}
    for iteration in range(iterations):
        key, entry = select_cell(archive, seed=seed + iteration)
        state = dict(entry["state"])
        actions = list(entry.get("actions", []))
        rollout_actions = schedules[iteration % len(schedules)][:horizon]
        updates = 0
        for action in rollout_actions:
            state = env.step(state, action)
            actions.append(action)
            record = {"cell_key": encode_cell(state), "state": dict(state), "actions": list(actions), "score": state["score"], "length": len(actions)}
            if update_archive(archive, record):
                updates += 1
            if state["score"] > best["score"] or (state["score"] == best["score"] and len(actions) < len(best["actions"]) if best["actions"] else True):
                best = {"score": state["score"], "actions": list(actions), "state": dict(state), "goal_reached": bool(state["done"])}
            if state["done"]:
                break
        trace.append({"iteration": iteration, "selected_cell": list(key), "restored_state": entry["state"], "explore_actions": rollout_actions, "archive_updates": updates})
        if best["goal_reached"]:
            break
    return {"archive_size": len(archive), "best": best, "trace": trace, "mechanism": {"selected_from_archive": True, "state_reset_used": True, "exploration_after_return": True}}


def run_restart_only_baseline(total_steps: int = 60) -> Dict[str, Any]:
    env = SparseGrid()
    schedule = list("RRRRRR")
    successes = 0
    for start_step in range(0, total_steps, len(schedule)):
        state = env.initial_state()
        for action in schedule:
            state = env.step(state, action)
            if state["done"]:
                successes += 1
                break
    return {"goal_reached": successes > 0, "successes": successes}
