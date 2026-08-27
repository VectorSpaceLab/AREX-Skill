#!/usr/bin/env python
"""Build a dry metadata-generation command plan.

This helper is intentionally safe: it does not import auto-sklearn, does not
contact OpenML, and does not run AutoML. It only validates explicit task IDs and
metrics and prints either shell commands or a JSON plan for a maintainer to
review.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Dict, Iterable, List, Optional

CLASSIFICATION_METRICS = {
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced_accuracy",
    "roc_auc": "roc_auc",
    "logloss": "logloss",
    "log_loss": "logloss",
}
REGRESSION_METRICS = {
    "r2": "r2",
    "root_mean_squared_error": "root_mean_squared_error",
    "mean_absolute_error": "mean_absolute_error",
    "mean_squared_error": "mean_squared_error",
}


def quote_parts(parts: Iterable[object]) -> str:
    """Return a shell-escaped command string."""

    return " ".join(shlex.quote(str(part)) for part in parts)


def metric_map(task_type: str) -> Dict[str, str]:
    if task_type == "classification":
        return CLASSIFICATION_METRICS
    if task_type == "regression":
        return REGRESSION_METRICS
    raise ValueError(f"unsupported task type: {task_type}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a dry, explicit metadata-generation plan without contacting "
            "OpenML or running AutoML."
        )
    )
    parser.add_argument(
        "--task-type",
        choices=("classification", "regression"),
        required=True,
        help="Task family for all provided task IDs.",
    )
    parser.add_argument(
        "--task-id",
        type=int,
        action="append",
        required=True,
        help="OpenML task ID to include. Repeat for multiple tasks.",
    )
    parser.add_argument(
        "--metric",
        action="append",
        required=True,
        help=(
            "Metric to include. Repeat for multiple metrics. Classification: "
            "accuracy, balanced_accuracy, roc_auc, logloss/log_loss. Regression: "
            "r2, root_mean_squared_error, mean_absolute_error, mean_squared_error."
        ),
    )
    parser.add_argument(
        "--working-directory",
        default="./metadata-work",
        help="Working directory that generated commands should use.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=86400,
        help="Total time limit in seconds to print for each AutoML command.",
    )
    parser.add_argument(
        "--per-run-time-limit",
        type=int,
        default=1800,
        help="Per-model time limit in seconds to print for each AutoML command.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Seed to print for each AutoML command.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Interpreter command name to print; no interpreter is executed.",
    )
    parser.add_argument(
        "--script-root",
        default="scripts",
        help="Relative directory containing the metadata maintenance scripts.",
    )
    parser.add_argument(
        "--unittest",
        action="store_true",
        help="Append the runner's unit-test flag and test-mode metafeature step.",
    )
    parser.add_argument(
        "--format",
        choices=("commands", "json"),
        default="commands",
        help="Output shell commands or a structured JSON plan.",
    )
    parser.add_argument(
        "--no-post-steps",
        action="store_true",
        help="Only print per-task AutoML commands, not retrieval/metafeature/ASLib steps.",
    )
    return parser


def validate_metrics(task_type: str, metrics: List[str]) -> List[str]:
    allowed = metric_map(task_type)
    normalized: List[str] = []
    invalid: List[str] = []
    for metric in metrics:
        key = metric.strip()
        if key not in allowed:
            invalid.append(metric)
        else:
            normalized.append(allowed[key])
    if invalid:
        valid = ", ".join(sorted(allowed))
        raise ValueError(f"invalid metric(s) for {task_type}: {invalid}; valid: {valid}")
    return normalized


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    metrics = validate_metrics(args.task_type, args.metric)
    warnings: List[str] = [
        "Dry plan only: no OpenML calls, no auto-sklearn imports, no AutoML execution.",
        "Review task IDs, metrics, runtime, disk, and network approval before running commands.",
    ]
    if args.task_type == "classification" and "roc_auc" in metrics:
        warnings.append(
            "roc_auc is valid only for binary classification tasks in the broad generator; "
            "verify labels before execution."
        )

    runner = f"{args.script_root.rstrip('/')}/run_auto-sklearn_for_metadata_generation.py"
    retrieve = f"{args.script_root.rstrip('/')}/02_retrieve_metadata.py"
    metafeatures = f"{args.script_root.rstrip('/')}/03_calculate_metafeatures.py"
    aslib = f"{args.script_root.rstrip('/')}/04_create_aslib_files.py"

    commands: List[Dict[str, object]] = []
    commands.append(
        {
            "stage": "prepare-working-directory",
            "command": quote_parts(["mkdir", "-p", args.working_directory]),
        }
    )

    for task_id in args.task_id:
        for metric in metrics:
            parts: List[object] = [
                args.python,
                runner,
                "--working-directory",
                args.working_directory,
                "--time-limit",
                args.time_limit,
                "--per-run-time-limit",
                args.per_run_time_limit,
                "--task-id",
                task_id,
                "-s",
                args.seed,
                "--metric",
                metric,
            ]
            if args.unittest:
                parts.append("--unittest")
            commands.append(
                {
                    "stage": "run-autosklearn-for-metadata",
                    "task_type": args.task_type,
                    "task_id": task_id,
                    "metric": metric,
                    "command": quote_parts(parts),
                }
            )

    if not args.no_post_steps:
        commands.append(
            {
                "stage": "retrieve-metadata",
                "command": quote_parts(
                    [args.python, retrieve, "--working-directory", args.working_directory]
                ),
            }
        )
        meta_parts: List[object] = [
            args.python,
            metafeatures,
            "--working-directory",
            args.working_directory,
        ]
        if args.unittest:
            meta_parts.append("--test-mode")
        commands.append(
            {"stage": "calculate-metafeatures", "command": quote_parts(meta_parts)}
        )
        commands.append(
            {
                "stage": "create-aslib-files",
                "command": quote_parts(
                    [args.python, aslib, "--working-directory", args.working_directory]
                ),
            }
        )

    return {
        "task_type": args.task_type,
        "task_ids": args.task_id,
        "metrics": metrics,
        "working_directory": args.working_directory,
        "time_limit": args.time_limit,
        "per_run_time_limit": args.per_run_time_limit,
        "seed": args.seed,
        "unittest": args.unittest,
        "warnings": warnings,
        "commands": commands,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        for warning in plan["warnings"]:
            print(f"# {warning}")
        for item in plan["commands"]:
            print(item["command"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
