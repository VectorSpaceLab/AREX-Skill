#!/usr/bin/env python3
"""Validate a VPG transition session and report source-compatible metrics.

This is a standalone adaptation of the historical evaluate.py.  It deliberately
has no imports from the repository that produced the logs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


class EvaluationError(ValueError):
    """An actionable session-layout or metric-input error."""


def _load_array(path: Path, *, ndmin: int) -> np.ndarray:
    try:
        values = np.loadtxt(path, delimiter=" ", ndmin=ndmin)
    except (OSError, ValueError) as exc:
        raise EvaluationError(
            f"cannot read {path}: expected whitespace-separated numeric values ({exc})"
        ) from exc
    values = np.asarray(values)
    if values.size == 0:
        raise EvaluationError(f"{path} is empty; restore the missing log rows")
    if not np.all(np.isfinite(values)):
        raise EvaluationError(f"{path} contains NaN or infinite values")
    return values


def _scalar_log(path: Path) -> np.ndarray:
    values = _load_array(path, ndmin=2)
    if values.ndim != 2 or values.shape[1] != 1:
        raise EvaluationError(
            f"{path} must contain one scalar per row; got shape {values.shape}"
        )
    return values.reshape(-1)


def _read_session(session_directory: str) -> tuple[Path, np.ndarray, np.ndarray, np.ndarray]:
    session = Path(session_directory).expanduser().resolve()
    if not session.is_dir():
        raise EvaluationError(f"session directory does not exist or is not a directory: {session}")
    transitions = session / "transitions"
    if not transitions.is_dir():
        raise EvaluationError(f"missing transitions directory under session: {transitions}")
    action_path = transitions / "executed-action.log.txt"
    reward_path = transitions / "reward-value.log.txt"
    clearance_path = transitions / "clearance.log.txt"
    missing = [str(p) for p in (action_path, reward_path, clearance_path) if not p.is_file()]
    if missing:
        raise EvaluationError("missing required log file(s): " + ", ".join(missing))

    actions = _load_array(action_path, ndmin=2)
    rewards = _scalar_log(reward_path)
    clearances = _scalar_log(clearance_path)
    if actions.ndim != 2 or actions.shape[1] < 1:
        raise EvaluationError(
            f"{action_path} must have at least one column (action ID in column 0); got shape {actions.shape}"
        )
    if actions.shape[0] == 0:
        raise EvaluationError(f"{action_path} has no action rows")
    if rewards.shape[0] < actions.shape[0]:
        raise EvaluationError(
            f"{reward_path} has {rewards.shape[0]} values but {action_path} has "
            f"{actions.shape[0]} action rows; recover the truncated reward log"
        )
    action_ids = actions[:, 0]
    if not np.all(np.isin(action_ids, (0, 1))):
        bad = sorted({float(x) for x in action_ids if x not in (0, 1)})
        raise EvaluationError(
            f"{action_path} column 0 contains invalid action ID(s) {bad}; expected 0=push or 1=grasp"
        )
    if not np.all(np.equal(clearances, np.rint(clearances))):
        raise EvaluationError(f"{clearance_path} contains non-integer trial boundaries")
    endpoints = np.rint(clearances).astype(np.int64)
    n_actions = actions.shape[0]
    if np.any(endpoints < 1) or np.any(endpoints > n_actions):
        raise EvaluationError(
            f"{clearance_path} boundaries must be in [1, {n_actions}], got {endpoints.tolist()}"
        )
    if endpoints.size > 1 and np.any(np.diff(endpoints) <= 0):
        raise EvaluationError(
            f"{clearance_path} boundaries must be strictly increasing; got {endpoints.tolist()}"
        )
    return session, actions, rewards[:n_actions], endpoints


def _success_mask(rewards: np.ndarray, action_ids: np.ndarray, method: str) -> np.ndarray:
    grasp = action_ids == 1
    if method == "reactive":
        return grasp & (rewards == 0)
    if method == "reinforcement":
        return grasp & (rewards >= 0.5)
    raise EvaluationError(f"unsupported method {method!r}; choose reactive or reinforcement")


def evaluate(session_directory: str, method: str, num_obj_complete: int) -> dict[str, Any]:
    if method not in {"reactive", "reinforcement"}:
        raise EvaluationError(f"unsupported method {method!r}; choose reactive or reinforcement")
    if num_obj_complete <= 0:
        raise EvaluationError("--num_obj_complete must be a positive integer")
    session, actions, rewards, endpoints = _read_session(session_directory)
    action_ids = actions[:, 0]
    successes = _success_mask(rewards, action_ids, method)
    boundaries = np.concatenate((np.asarray([0], dtype=np.int64), endpoints))
    trials: list[dict[str, Any]] = []
    for trial_index, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:]), start=1):
        trial_actions = action_ids[start:end]
        trial_successes = successes[start:end]
        grasp_attempts = int(np.sum(trial_actions == 1))
        successful_grasps = int(np.sum(trial_successes))
        action_count = int(end - start)
        completed = successful_grasps >= num_obj_complete
        grasp_rate: float | None
        if grasp_attempts:
            grasp_rate = float(successful_grasps) / float(grasp_attempts)
        else:
            grasp_rate = None
        ratio = float(grasp_attempts) / float(action_count)
        efficiency = float(num_obj_complete) / float(action_count) if completed else None
        warning = None if grasp_attempts else "no grasp attempts in this trial; grasp rate is undefined"
        trials.append(
            {
                "trial": trial_index,
                "start_action": int(start),
                "end_action_exclusive": int(end),
                "action_count": action_count,
                "grasp_attempts": grasp_attempts,
                "successful_grasps": successful_grasps,
                "grasp_success_rate": grasp_rate,
                "completed": bool(completed),
                "action_efficiency": efficiency,
                "grasp_to_push_ratio": ratio,
                "warning": warning,
            }
        )

    completed_trials = [trial for trial in trials if trial["completed"]]
    completion_rate = 100.0 * float(len(completed_trials)) / float(len(trials))
    if completed_trials:
        grasp_metric = 100.0 * float(np.mean([t["grasp_success_rate"] for t in completed_trials]))
        efficiency_metric = 100.0 * float(np.mean([t["action_efficiency"] for t in completed_trials]))
        ratio_metric = 100.0 * float(np.mean([t["grasp_to_push_ratio"] for t in completed_trials]))
        restricted_warning = None
    else:
        grasp_metric = None
        efficiency_metric = None
        ratio_metric = None
        restricted_warning = "no trial reached --num_obj_complete; completion-conditioned metrics are undefined"

    warnings = [t["warning"] for t in trials if t["warning"]]
    if int(endpoints[-1]) < int(actions.shape[0]):
        warnings.append(
            f"{int(actions.shape[0]) - int(endpoints[-1])} trailing action row(s) lie after the final clearance boundary and are excluded from trial metrics"
        )
    if restricted_warning:
        warnings.append(restricted_warning)
    return {
        "method": method,
        "num_obj_complete": int(num_obj_complete),
        "num_trials": len(trials),
        "metrics": {
            "average_completion_rate_percent": completion_rate,
            "average_grasp_success_per_completion_percent": grasp_metric,
            "average_action_efficiency_percent": efficiency_metric,
            "average_grasp_to_push_ratio_percent": ratio_metric,
        },
        "trial_metrics": trials,
        "validation": {
            "session_directory": str(session),
            "action_rows": int(actions.shape[0]),
            "reward_rows_used": int(rewards.shape[0]),
            "clearance_boundaries": [int(x) for x in endpoints],
        },
        "warnings": warnings,
    }


def _text_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]

    def percent(value: float | None) -> str:
        return "undefined (no completed trials)" if value is None else f"{value:2.1f}"

    lines = [
        f"Average % clearance: {percent(metrics['average_completion_rate_percent'])}",
        f"Average % grasp success per clearance: {percent(metrics['average_grasp_success_per_completion_percent'])}",
        f"Average % action efficiency: {percent(metrics['average_action_efficiency_percent'])}",
        f"Average grasp to push ratio: {percent(metrics['average_grasp_to_push_ratio_percent'])}",
    ]
    if result["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a VPG session and report completion, grasp success, and action efficiency."
    )
    parser.add_argument(
        "--session_directory",
        required=True,
        help="session root containing transitions/ (source-compatible flag)",
    )
    parser.add_argument(
        "--method",
        required=True,
        choices=("reactive", "reinforcement"),
        help="reactive class labels or reinforcement rewards (source-compatible flag)",
    )
    parser.add_argument(
        "--num_obj_complete",
        required=True,
        type=int,
        help="positive number of successful grasps required to complete a trial (source-compatible flag)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format (default: text)")
    parser.add_argument("--output", help="optional file for the deterministic report; stdout is also written")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = evaluate(args.session_directory, args.method, args.num_obj_complete)
        report = _text_report(result) if args.format == "text" else json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            output = Path(args.output).expanduser()
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(report, encoding="utf-8")
            except OSError as exc:
                raise EvaluationError(f"cannot write report to {output}: {exc}") from exc
        sys.stdout.write(report)
        return 0
    except EvaluationError as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
