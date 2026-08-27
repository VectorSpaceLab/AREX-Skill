#!/usr/bin/env python3
"""Check Habitat-Lab imports and core config composition safely."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


def import_module(name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"
        return item
    item["ok"] = True
    item["version"] = getattr(module, "__version__", None)
    return item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-baselines", action="store_true")
    parser.add_argument("--include-hitl", action="store_true")
    parser.add_argument(
        "--config",
        default="benchmark/nav/pointnav/pointnav_habitat_test.yaml",
        help="Core Habitat config name to compose after import succeeds.",
    )
    args = parser.parse_args(argv)

    modules = ["habitat", "habitat_sim", "magnum"]
    if args.include_baselines:
        modules.append("habitat_baselines")
    if args.include_hitl:
        modules.append("habitat_hitl")

    results = [import_module(name) for name in modules]
    print(json.dumps({"imports": results}, indent=2, sort_keys=True))
    if any(not item["ok"] for item in results):
        print(
            "One or more imports failed. Check Python/Habitat-Sim compatibility, "
            "optional Baselines/HITL dependencies, and graphics/backend packages.",
            file=sys.stderr,
        )
        return 1

    try:
        from habitat.config.default import get_config

        cfg = get_config(args.config)
        summary = {
            "config": args.config,
            "env_task": cfg.habitat.env_task,
            "dataset_type": cfg.habitat.dataset.type,
            "simulator_type": cfg.habitat.simulator.type,
            "max_episode_steps": cfg.habitat.environment.max_episode_steps,
        }
        print(json.dumps({"config_summary": summary}, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"Config composition failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
