#!/usr/bin/env python3
"""Read-only NAVSIM evaluation preflight and override consistency checker.

This tool does not import datasets, open metric-cache files, start Hydra, start
workers, download data, or run a benchmark. It checks user-supplied paths only
for existence, reports the public runner/module contract, and applies safe
split/stage/sampling invariants. Use ``--self-test`` for a data-free fixture
check.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


TWO_STAGE_SPLITS = {
    "navhard_two_stage",
    "navsafe_two_stage",
    "navtest_two_stage",
    "private_test_hard_two_stage",
    "warmup_two_stage",
    "warmup_navsafe_two_stage_extended",
}
RUNNERS = {
    "cache": "navsim.planning.script.run_metric_caching",
    "one_stage": "navsim.planning.script.run_pdm_score_one_stage",
    "two_stage": "navsim.planning.script.run_pdm_score",
    "submission": "navsim.planning.script.run_pdm_score_from_submission",
}


def _issue(issues: List[Dict[str, str]], level: str, message: str) -> None:
    issues.append({"level": level, "message": message})


def _path_status(value: Optional[str], label: str, issues: List[Dict[str, str]]) -> Dict[str, Any]:
    if value is None:
        return {"value": None, "exists": None}
    path = Path(value).expanduser()
    exists = path.exists()
    if not exists:
        _issue(issues, "error", f"{label} does not exist: {path}")
    return {"value": str(path), "exists": exists, "is_dir": path.is_dir() if exists else None}


def _check_modules(issues: List[Dict[str, str]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for name in ["navsim", *RUNNERS.values()]:
        try:
            result[name] = "available" if importlib.util.find_spec(name) else "missing"
        except (ImportError, ModuleNotFoundError, ValueError) as exc:
            result[name] = f"unavailable: {exc.__class__.__name__}"
    if result.get("navsim") != "available":
        _issue(issues, "error", "navsim is not discoverable by the active interpreter")
    return result


def inspect(args: argparse.Namespace) -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []
    split = args.split
    stage = args.stage
    two_stage = split in TWO_STAGE_SPLITS

    if stage == "auto":
        stage = "two_stage" if two_stage else "one_stage"
    if stage == "two_stage" and not two_stage:
        _issue(issues, "warning", f"stage=two_stage with non-two-stage split {split!r}; verify the split mapping")
    if stage != "two_stage" and two_stage:
        _issue(issues, "warning", f"two-stage split {split!r} selected for {stage}; synthetic roots may be required")

    if args.proposal_num_poses <= 0 or args.proposal_interval <= 0:
        _issue(issues, "error", "proposal sampling values must be positive")
    horizon = args.proposal_num_poses * args.proposal_interval
    if not math.isclose(horizon, 4.0, rel_tol=0.0, abs_tol=1e-6):
        _issue(issues, "warning", f"proposal horizon is {horizon:g}s, not the default 4s; record the protocol and rebuild caches")

    paths = {
        "metric_cache_path": _path_status(args.cache_path, "metric cache path", issues),
        "navsim_log_path": _path_status(args.log_path, "NAVSIM log path", issues),
        "synthetic_sensor_path": _path_status(args.synthetic_sensor_path, "synthetic sensor path", issues),
        "synthetic_scenes_path": _path_status(args.synthetic_scenes_path, "synthetic scenes path", issues),
    }
    if args.cache_path is None:
        _issue(issues, "error", "metric cache path is required before a data-backed run")

    if stage == "two_stage":
        for key in ("synthetic_sensor_path", "synthetic_scenes_path"):
            if paths[key]["value"] is None:
                _issue(issues, "error", f"{key} is required for a two-stage run")
    if args.cache_path and two_stage and split not in Path(args.cache_path).name:
        _issue(issues, "warning", "cache path name does not contain the selected two-stage split; verify token coverage explicitly")

    modules = _check_modules(issues)
    errors = sum(issue["level"] == "error" for issue in issues)
    warnings = sum(issue["level"] == "warning" for issue in issues)
    return {
        "status": "blocked" if errors else ("review" if warnings else "ready_for_explicit_run"),
        "split": split,
        "stage": stage,
        "two_stage_split": two_stage,
        "proposal_sampling": {
            "num_poses": args.proposal_num_poses,
            "interval_length": args.proposal_interval,
            "horizon_seconds": horizon,
            "default_four_second_horizon": math.isclose(horizon, 4.0, abs_tol=1e-6),
        },
        "paths": paths,
        "runner_modules": RUNNERS,
        "module_discovery": modules,
        "checks": {
            "errors": errors,
            "warnings": warnings,
            "cache_token_set_checked": False,
            "dataset_or_cache_opened": False,
            "benchmark_started": False,
        },
        "issues": issues,
    }


def _self_test() -> None:
    args = argparse.Namespace(
        split="navtest",
        stage="auto",
        cache_path="/tmp/navtest-cache",
        log_path=None,
        synthetic_sensor_path=None,
        synthetic_scenes_path=None,
        proposal_num_poses=8,
        proposal_interval=0.5,
    )
    report = inspect(args)
    assert report["status"] == "blocked"
    assert report["checks"]["errors"] > 0
    assert report["checks"]["dataset_or_cache_opened"] is False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="navtest", help="resolved train_test_split name")
    parser.add_argument("--stage", choices=("auto", "one_stage", "two_stage", "submission", "cache"), default="auto")
    parser.add_argument("--cache-path", help="metric cache directory; checked for existence only")
    parser.add_argument("--log-path", help="log annotation directory; checked for existence only")
    parser.add_argument("--synthetic-sensor-path", help="two-stage sensor directory; checked for existence only")
    parser.add_argument("--synthetic-scenes-path", help="two-stage scene-pickle directory; checked for existence only")
    parser.add_argument("--proposal-num-poses", type=int, default=40)
    parser.add_argument("--proposal-interval", type=float, default=0.1)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--self-test", action="store_true", help="run a data-free fixture assertion and exit")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.self_test:
        _self_test()
        print("self-test: ok")
        return 0

    report = inspect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"split: {report['split']} | stage: {report['stage']}")
        sampling = report["proposal_sampling"]
        print(f"sampling: {sampling['num_poses']} poses x {sampling['interval_length']}s = {sampling['horizon_seconds']:g}s")
        print("runner modules:")
        for key, value in report["runner_modules"].items():
            print(f"  {key}: {value}")
        for issue in report["issues"]:
            print(f"{issue['level']}: {issue['message']}")
        print("no dataset/cache contents opened; no benchmark started")
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
