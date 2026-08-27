#!/usr/bin/env python3
"""Deterministic smoke checks for tree-of-thoughts DFS/BFS orchestration.

This helper performs no network calls. It imports the installed
``tree_of_thoughts`` package and supplies a fake agent whose ``run`` method
returns dictionaries with the fields expected by the search classes.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from typing import Any, Dict, Optional


class DeterministicFakeAgent:
    """Thread-safe fake agent matching the tree-of-thoughts search contract."""

    def __init__(self) -> None:
        self.max_loops: Optional[int] = None
        self._lock = threading.Lock()
        self._per_task_counts: Dict[str, int] = {}
        self.total_calls = 0

    def run(self, task: Any) -> Dict[str, Any]:
        state = " ".join(str(task).split()) or "<empty-task>"
        short_state = state[:72]

        with self._lock:
            self.total_calls += 1
            branch_index = self._per_task_counts.get(short_state, 0) + 1
            self._per_task_counts[short_state] = branch_index
            call_index = self.total_calls

        # Cycle intentionally includes one pruned score and several accepted
        # scores so DFS smoke runs exercise both final_thoughts and pruning.
        evaluation_cycle = (0.32, 0.58, 0.82, 0.67, 0.91)
        evaluation = evaluation_cycle[(branch_index - 1) % len(evaluation_cycle)]
        thought = (
            f"fake branch {branch_index} after call {call_index}: "
            f"refine [{short_state}]"
        )
        return {"thought": thought, "evaluation": evaluation}


def _load_dfs_class():
    try:
        from tree_of_thoughts import ToTDFSAgent
    except Exception as exc:  # pragma: no cover - error path for operators
        raise SystemExit(
            "Failed to import ToTDFSAgent from the installed tree_of_thoughts "
            f"package: {exc}"
        ) from exc
    return ToTDFSAgent


def _load_bfs_class():
    try:
        from tree_of_thoughts.bfs import BFSWithTotAgent
    except Exception as exc:  # pragma: no cover - error path for operators
        raise SystemExit(
            "Failed to import BFSWithTotAgent from tree_of_thoughts.bfs. "
            "BFS is not exported by the package root. Original error: "
            f"{exc}"
        ) from exc
    return BFSWithTotAgent


def _require_thought_dict(value: Any, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a dict or None, got {type(value).__name__}")
    if "thought" not in value or "evaluation" not in value:
        raise SystemExit(f"{label} lacks required thought/evaluation keys: {value!r}")
    try:
        float(value["evaluation"])
    except Exception as exc:
        raise SystemExit(f"{label} has non-numeric evaluation: {value!r}") from exc


def run_dfs(args: argparse.Namespace) -> Dict[str, Any]:
    ToTDFSAgent = _load_dfs_class()
    fake_agent = DeterministicFakeAgent()
    search = ToTDFSAgent(
        agent=fake_agent,
        threshold=0.8,
        max_loops=args.max_loops,
        prune_threshold=0.5,
        number_of_agents=args.number_of_agents,
        autosave_on=not args.no_autosave,
        id="fake-agent-search-smoke-dfs",
    )
    raw = search.run("Tiny fixture: choose a concise arithmetic path to 24.")
    data = json.loads(raw)

    final_thoughts = data.get("final_thoughts")
    pruned_branches = data.get("pruned_branches")
    if not isinstance(final_thoughts, list):
        raise SystemExit("DFS output final_thoughts must be a list")
    if not isinstance(pruned_branches, list):
        raise SystemExit("DFS output pruned_branches must be a list")
    for index, thought in enumerate(final_thoughts):
        _require_thought_dict(thought, f"DFS final_thoughts[{index}]")
    for index, thought in enumerate(pruned_branches):
        _require_thought_dict(thought, f"DFS pruned_branches[{index}]")
    highest = data.get("highest_rated_thought")
    _require_thought_dict(highest, "DFS highest_rated_thought")

    return {
        "mode": "dfs",
        "max_loops": args.max_loops,
        "number_of_agents": args.number_of_agents,
        "autosave_enabled": not args.no_autosave,
        "parsed_keys": sorted(data.keys()),
        "final_thoughts_count": len(final_thoughts),
        "pruned_branches_count": len(pruned_branches),
        "highest_rated_thought": highest,
        "fake_agent_calls": fake_agent.total_calls,
    }


def run_bfs(args: argparse.Namespace) -> Dict[str, Any]:
    BFSWithTotAgent = _load_bfs_class()
    fake_agent = DeterministicFakeAgent()
    search = BFSWithTotAgent(
        agent=fake_agent,
        max_loops=args.max_loops,
        breadth_limit=args.breadth_limit,
        number_of_agents=args.number_of_agents,
        autosave_on=not args.no_autosave,
        id="fake-agent-search-smoke-bfs",
    )
    raw = search.run("Tiny fixture: choose a concise arithmetic path to 24.")
    data = json.loads(raw)

    all_thoughts = data.get("all_thoughts")
    if not isinstance(all_thoughts, list):
        raise SystemExit("BFS output all_thoughts must be a list")
    for index, thought in enumerate(all_thoughts):
        _require_thought_dict(thought, f"BFS all_thoughts[{index}]")
    final_thought = data.get("final_thought")
    _require_thought_dict(final_thought, "BFS final_thought")

    return {
        "mode": "bfs",
        "max_loops": args.max_loops,
        "number_of_agents": args.number_of_agents,
        "breadth_limit": args.breadth_limit,
        "autosave_enabled": not args.no_autosave,
        "parsed_keys": sorted(data.keys()),
        "all_thoughts_count": len(all_thoughts),
        "final_thought": final_thought,
        "fake_agent_calls": fake_agent.total_calls,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic fake-agent smoke checks for tree-of-thoughts DFS/BFS."
    )
    parser.add_argument(
        "--mode",
        choices=("dfs", "bfs"),
        required=True,
        help="Search workflow to exercise.",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=2,
        help="Maximum DFS depth or BFS expansion levels. Default: 2.",
    )
    parser.add_argument(
        "--number-of-agents",
        type=int,
        default=3,
        help="Candidate thoughts generated per state. Default: 3.",
    )
    parser.add_argument(
        "--breadth-limit",
        type=int,
        default=2,
        help="BFS states retained per level. Ignored for DFS. Default: 2.",
    )
    parser.add_argument(
        "--no-autosave",
        action="store_true",
        help="Disable DFS autosave side effects; accepted for BFS parity.",
    )
    args = parser.parse_args(argv)

    if args.max_loops < 0:
        parser.error("--max-loops must be >= 0")
    if args.number_of_agents < 1:
        parser.error("--number-of-agents must be >= 1")
    if args.breadth_limit < 0:
        parser.error("--breadth-limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    summary = run_dfs(args) if args.mode == "dfs" else run_bfs(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
