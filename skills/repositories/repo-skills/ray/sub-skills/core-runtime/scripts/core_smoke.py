#!/usr/bin/env python3
"""Small Ray Core smoke helper with safe defaults.

Default mode validates that Ray imports and prints version/API availability only.
Use --run-local to start a tiny local Ray runtime, run one task and one actor,
and then shut Ray down.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _load_ray():
    try:
        import ray  # type: ignore
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(f"Failed to import ray: {exc}") from exc
    return ray


def inspect_only() -> dict[str, Any]:
    ray = _load_ray()
    required = ["init", "shutdown", "remote", "get", "put", "wait", "is_initialized"]
    missing = [name for name in required if not hasattr(ray, name)]
    return {
        "ok": not missing,
        "mode": "inspect-only",
        "ray_version": getattr(ray, "__version__", "unknown"),
        "missing_api": missing,
    }


def run_local(num_cpus: int) -> dict[str, Any]:
    ray = _load_ray()

    @ray.remote
    def square(value: int) -> int:
        return value * value

    @ray.remote
    class Counter:
        def __init__(self) -> None:
            self.value = 0

        def add(self, amount: int) -> int:
            self.value += amount
            return self.value

    started_here = False
    if not ray.is_initialized():
        ray.init(num_cpus=num_cpus, include_dashboard=False, ignore_reinit_error=True)
        started_here = True

    try:
        task_refs = [square.remote(i) for i in range(4)]
        ready, unready = ray.wait(task_refs, num_returns=2, timeout=10)
        if len(ready) != 2:
            raise RuntimeError(f"Expected 2 ready refs, got {len(ready)}; unready={len(unready)}")
        task_results = ray.get(task_refs, timeout=30)

        counter = Counter.remote()
        actor_results = ray.get([counter.add.remote(1), counter.add.remote(2)], timeout=30)

        return {
            "ok": task_results == [0, 1, 4, 9] and actor_results == [1, 3],
            "mode": "run-local",
            "ray_version": getattr(ray, "__version__", "unknown"),
            "task_results": task_results,
            "actor_results": actor_results,
            "started_runtime": started_here,
        }
    finally:
        if started_here:
            ray.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Ray Core imports by default. With --run-local, start a tiny local "
            "Ray runtime, run one task and one actor, and shut it down."
        )
    )
    parser.add_argument(
        "--run-local",
        action="store_true",
        help="Start a tiny local Ray runtime and execute task/actor smoke checks.",
    )
    parser.add_argument(
        "--num-cpus",
        type=int,
        default=2,
        help="CPU count to pass to ray.init when --run-local starts a runtime (default: 2).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a short text summary.",
    )
    args = parser.parse_args(argv)

    if args.num_cpus < 1:
        parser.error("--num-cpus must be at least 1")

    result = run_local(args.num_cpus) if args.run_local else inspect_only()

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        status = "OK" if result.get("ok") else "FAILED"
        print(f"{status}: Ray Core smoke {result['mode']} with Ray {result['ray_version']}")
        if result.get("missing_api"):
            print(f"Missing APIs: {', '.join(result['missing_api'])}")
        if result.get("task_results") is not None:
            print(f"Task results: {result['task_results']}")
            print(f"Actor results: {result['actor_results']}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
