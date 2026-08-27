#!/usr/bin/env python3
"""Path-explicit nuPlan preprocessing adapter for Diffusion Planner.

This bundled adapter replaces the repository shell/entrypoint assumptions with
explicit paths and a manifest destination. It still requires an installed
nuPlan-devkit, real DB/map data, and the Diffusion Planner package; it does not
download data or run unless the user explicitly invokes it.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, List, Optional

from diffusion_planner.data_process.data_processor import DataProcessor
from nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder import NuPlanScenarioBuilder
from nuplan.planning.scenario_builder.scenario_filter import ScenarioFilter
from nuplan.planning.utils.multithreading.worker_parallel import SingleMachineParallelExecutor


def _bool(value: str) -> bool:
    lowered = str(value).lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def _scenario_filter(args: argparse.Namespace, log_names: Optional[List[str]]) -> ScenarioFilter:
    # Keep the same positional contract used by the selected nuPlan-devkit.
    return ScenarioFilter(
        None, None, log_names, None,
        args.scenarios_per_type, args.total_scenarios, None, None,
        True, False, args.shuffle_scenarios, None, None, None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preprocess nuPlan scenarios into Diffusion Planner records with explicit paths."
    )
    parser.add_argument("--data-path", required=True, help="nuPlan trainval/DB root")
    parser.add_argument("--map-path", required=True, help="nuPlan map root")
    parser.add_argument("--save-path", required=True, help="directory for processed .npz records")
    parser.add_argument("--log-names", required=True, help="JSON file containing the training log-name list")
    parser.add_argument("--manifest-output", help="JSON filename list destination (default: save-path/diffusion_planner_training.json)")
    parser.add_argument("--map-version", default="nuplan-maps-v1.0")
    parser.add_argument("--scenarios-per-type", type=int, default=None)
    parser.add_argument("--total-scenarios", type=int, default=10)
    parser.add_argument("--shuffle-scenarios", type=_bool, default=True)
    parser.add_argument("--agent-num", type=int, default=32)
    parser.add_argument("--static-objects-num", type=int, default=5)
    parser.add_argument("--lane-len", type=int, default=20)
    parser.add_argument("--lane-num", type=int, default=70)
    parser.add_argument("--route-len", type=int, default=20)
    parser.add_argument("--route-num", type=int, default=25)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    for label, value in (("data", args.data_path), ("maps", args.map_path), ("log names", args.log_names)):
        path = Path(value)
        if not path.exists():
            raise SystemExit(f"ERROR: {label} path does not exist: {path}")
        if label == "log names" and not path.is_file():
            raise SystemExit(f"ERROR: log names must be a JSON file: {path}")
        if label != "log names" and not path.is_dir():
            raise SystemExit(f"ERROR: {label} path must be a directory: {path}")
    save_path = Path(args.save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest_output) if args.manifest_output else save_path / "diffusion_planner_training.json"
    with Path(args.log_names).open("r", encoding="utf-8") as handle:
        log_names = json.load(handle)
    if not isinstance(log_names, list) or not all(isinstance(item, str) for item in log_names):
        raise SystemExit("ERROR: --log-names must contain a JSON array of strings")

    builder = NuPlanScenarioBuilder(args.data_path, args.map_path, None, None, args.map_version)
    scenario_filter = _scenario_filter(args, log_names)
    worker = SingleMachineParallelExecutor(use_process_pool=True)
    scenarios = builder.get_scenarios(scenario_filter, worker)
    print(f"Total number of scenarios: {len(scenarios)}")
    del worker, builder, scenario_filter

    processor = DataProcessor(args)
    processor.work(scenarios)
    filenames = sorted(name for name in os.listdir(save_path) if name.endswith(".npz"))
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(filenames, handle, indent=2)
    print(f"Saved {len(filenames)} .npz file names to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
