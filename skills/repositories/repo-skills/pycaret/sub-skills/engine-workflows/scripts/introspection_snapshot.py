#!/usr/bin/env python3
"""Print JSON snapshots from PyCaret's typed introspection API.

Examples
--------
python scripts/introspection_snapshot.py --help
python scripts/introspection_snapshot.py --task classification --task regression
python scripts/introspection_snapshot.py --task all --include-setup-params --indent 2

This script is side-effect-free apart from printing JSON. It does not fit
experiments and does not touch the network.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import asdict
from typing import Any


TASK_ALIASES = {
    "classification": "classification",
    "regression": "regression",
    "clustering": "clustering",
    "anomaly": "anomaly",
    "time-series": "time_series",
    "time_series": "time_series",
    "timeseries": "time_series",
}
ORDERED_TASKS = ["classification", "regression", "clustering", "anomaly", "time_series"]


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    try:
        return asdict(obj)
    except Exception:  # noqa: BLE001
        return repr(obj)


def _version() -> str | None:
    try:
        import pycaret

        return getattr(pycaret, "__version__", None)
    except Exception:  # noqa: BLE001
        return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print JSON from pycaret.api list_models/list_metrics/describe_setup_params."
    )
    parser.add_argument(
        "--task",
        action="append",
        choices=["classification", "regression", "clustering", "anomaly", "time-series", "time_series", "timeseries", "all"],
        default=None,
        help="Task to include. Repeat for multiple tasks, or use all. Default: classification.",
    )
    parser.add_argument(
        "--include-setup-params",
        action="store_true",
        help="Include describe_setup_params(task) output. Enabled by default unless --no-setup-params is passed.",
    )
    parser.add_argument(
        "--no-setup-params",
        action="store_true",
        help="Omit setup parameter schemas from output.",
    )
    parser.add_argument(
        "--model-id",
        action="append",
        default=[],
        help="Model ID to describe for every selected task where it exists. Repeatable.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation. Use 0 for compact output.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include tracebacks for failed per-task API calls.",
    )
    return parser.parse_args(argv)


def normalize_tasks(task_args: list[str] | None) -> list[str]:
    if not task_args:
        return ["classification"]
    out: list[str] = []
    for item in task_args:
        if item == "all":
            for task in ORDERED_TASKS:
                if task not in out:
                    out.append(task)
        else:
            normalized = TASK_ALIASES[item]
            if normalized not in out:
                out.append(normalized)
    return out


def snapshot_task(task: str, model_ids: list[str], include_setup: bool, include_tb: bool) -> dict[str, Any]:
    from pycaret.api import describe_model, describe_setup_params, list_metrics, list_models

    record: dict[str, Any] = {"task": task, "status": "ok"}

    try:
        models = list_models(task)
        record["models"] = [m.to_dict() for m in models]
        record["model_count"] = len(models)
    except Exception as exc:  # noqa: BLE001
        record["status"] = "error"
        record["models_error"] = {"type": type(exc).__name__, "message": str(exc)}
        if include_tb:
            record["models_error"]["traceback"] = traceback.format_exc()

    try:
        metrics = list_metrics(task)
        record["metrics"] = [m.to_dict() for m in metrics]
        record["metric_count"] = len(metrics)
    except Exception as exc:  # noqa: BLE001
        record["status"] = "error"
        record["metrics_error"] = {"type": type(exc).__name__, "message": str(exc)}
        if include_tb:
            record["metrics_error"]["traceback"] = traceback.format_exc()

    if include_setup:
        try:
            setup = describe_setup_params(task)
            record["setup_params"] = setup.to_dict()
            record["setup_param_count"] = len(setup.parameters)
            record["setup_groups"] = list(setup.groups)
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["setup_error"] = {"type": type(exc).__name__, "message": str(exc)}
            if include_tb:
                record["setup_error"]["traceback"] = traceback.format_exc()

    described: dict[str, Any] = {}
    for model_id in model_ids:
        try:
            described[model_id] = describe_model(task, model_id).to_dict()
        except Exception as exc:  # noqa: BLE001
            described[model_id] = {"error_type": type(exc).__name__, "error": str(exc)}
    if described:
        record["described_models"] = described

    return record


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    tasks = normalize_tasks(args.task)
    include_setup = args.include_setup_params or not args.no_setup_params

    results = [snapshot_task(task, args.model_id, include_setup, args.traceback) for task in tasks]
    ok = all(r.get("status") == "ok" for r in results)
    payload = {
        "schema": "pycaret.introspection-snapshot.v1",
        "pycaret_version": _version(),
        "tasks": tasks,
        "results": results,
        "notes": [
            "Static list_models/list_metrics are populated primarily for classification and regression in this engine version.",
            "For clustering, anomaly, and time_series runtime registries, fit an Experiment and call exp.models() / exp.get_metrics().",
        ],
        "ok": ok,
    }
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(payload, indent=indent, default=_json_default, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
