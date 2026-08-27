#!/usr/bin/env python3
"""Bounded Ray Train/Tune smoke helper.

By default this script performs import and signature checks only. Pass
``--run-tune`` to start a tiny deterministic local Tune run adapted from Ray's
AsyncHyperBand example without external ML frameworks.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict


REQUIRED_SIGNATURES = {
    "train.ScalingConfig": ["num_workers", "use_gpu", "resources_per_worker"],
    "train.RunConfig": ["name", "storage_path", "checkpoint_config"],
    "train.report": ["metrics"],
    "tune.Tuner": ["trainable", "param_space", "tune_config", "run_config"],
    "tune.TuneConfig": ["metric", "mode", "num_samples", "max_concurrent_trials"],
    "tune.report": ["metrics"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Ray Train/Tune imports or run a tiny deterministic Tune sweep."
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="perform import/signature checks and exit; this is also the default",
    )
    parser.add_argument(
        "--run-tune",
        action="store_true",
        help="start a tiny local Ray Tune run with deterministic metrics",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=1,
        help="number of random/grid repetitions for the optional Tune run",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=2,
        help="number of reporting iterations per optional Tune trial",
    )
    parser.add_argument(
        "--cpus-per-trial",
        type=float,
        default=1.0,
        help="logical CPUs requested for each optional Tune trial",
    )
    parser.add_argument(
        "--max-concurrent-trials",
        type=int,
        default=1,
        help="maximum concurrent trials for the optional Tune run",
    )
    parser.add_argument(
        "--storage-path",
        default=None,
        help="optional Tune storage path; defaults to a temporary directory for --run-tune",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a compact JSON summary",
    )
    return parser


def import_ray_modules():
    try:
        import ray  # noqa: F401
        from ray import train, tune
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Failed to import Ray Train/Tune. Install the narrow extras needed for "
            "this workflow, usually 'ray[train]' and/or 'ray[tune]'."
        ) from exc
    return train, tune


def signature_status() -> Dict[str, Any]:
    train, tune = import_ray_modules()
    objects = {
        "train.ScalingConfig": train.ScalingConfig,
        "train.RunConfig": train.RunConfig,
        "train.report": train.report,
        "tune.Tuner": tune.Tuner,
        "tune.TuneConfig": tune.TuneConfig,
        "tune.report": tune.report,
    }
    status: Dict[str, Any] = {}
    for name, obj in objects.items():
        signature = inspect.signature(obj)
        params = list(signature.parameters)
        missing = [param for param in REQUIRED_SIGNATURES[name] if param not in params]
        status[name] = {
            "signature": str(signature),
            "required_present": not missing,
            "missing": missing,
        }
    return status


def tiny_objective(config: Dict[str, Any]) -> None:
    from ray import tune

    width = int(config["width"])
    height = int(config["height"])
    steps = int(config["steps"])
    for step in range(steps):
        loss = float((width - 3) ** 2 + height * 0.01 + (steps - step - 1) * 0.001)
        tune.report({"loss": loss, "step": step, "width": width, "height": height})


def run_tune(args: argparse.Namespace) -> Dict[str, Any]:
    _, tune = import_ray_modules()
    if args.num_samples < 1:
        raise ValueError("--num-samples must be >= 1")
    if args.steps < 1:
        raise ValueError("--steps must be >= 1")
    if args.cpus_per_trial <= 0:
        raise ValueError("--cpus-per-trial must be > 0")
    if args.max_concurrent_trials < 1:
        raise ValueError("--max-concurrent-trials must be >= 1")

    storage_context = None
    storage_path = args.storage_path
    if storage_path is None:
        storage_context = tempfile.TemporaryDirectory(prefix="ray-tune-smoke-")
        storage_path = storage_context.name

    try:
        scheduler = None
        try:
            from ray.tune.schedulers import AsyncHyperBandScheduler

            scheduler = AsyncHyperBandScheduler(
                metric="loss",
                mode="min",
                max_t=max(args.steps, 1),
                grace_period=1,
            )
        except Exception:
            scheduler = None

        tuner = tune.Tuner(
            tune.with_resources(
                tiny_objective,
                {"cpu": args.cpus_per_trial, "gpu": 0},
            ),
            param_space={
                "steps": args.steps,
                "width": tune.grid_search([2, 3]),
                "height": tune.grid_search([0, 1]),
            },
            tune_config=tune.TuneConfig(
                metric="loss",
                mode="min",
                scheduler=scheduler,
                num_samples=args.num_samples,
                max_concurrent_trials=args.max_concurrent_trials,
            ),
            run_config=tune.RunConfig(
                name="tune_train_smoke",
                storage_path=storage_path,
                stop={"training_iteration": args.steps},
                verbose=0,
            ),
        )
        results = tuner.fit()
        best = results.get_best_result(metric="loss", mode="min")
        summary = {
            "experiment_path": results.experiment_path,
            "num_errors": results.num_errors,
            "num_terminated": results.num_terminated,
            "best_config": best.config,
            "best_loss": best.metrics.get("loss"),
        }
        if results.num_errors:
            raise RuntimeError(f"Tune run had {results.num_errors} trial errors: {results.errors}")
        return summary
    finally:
        if storage_context is not None:
            storage_context.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        checks = signature_status()
        failures = {
            name: details["missing"]
            for name, details in checks.items()
            if not details["required_present"]
        }
        if failures:
            raise RuntimeError(f"Required signature parameters missing: {failures}")

        result: Dict[str, Any] = {"signature_checks": checks}
        if args.run_tune:
            result["tune_run"] = run_tune(args)

        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("Ray Train/Tune import and signature checks passed.")
            if args.run_tune:
                tune_run = result["tune_run"]
                print("Tiny Tune run passed.")
                print(f"Best config: {tune_run['best_config']}")
                print(f"Best loss: {tune_run['best_loss']}")
        return 0
    except Exception as exc:  # pragma: no cover - command-line diagnostic path
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
