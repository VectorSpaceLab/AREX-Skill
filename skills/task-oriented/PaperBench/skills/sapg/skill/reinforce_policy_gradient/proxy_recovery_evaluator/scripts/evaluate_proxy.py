#!/usr/bin/env python3
"""Evaluate mechanism-faithful soft-mode REINFORCE proxy recovery evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_proxy(module_plan: dict, recovery_result: dict, training_trace: dict, invocations: dict) -> dict:
    target = module_plan.get("fast_recovery_target", {})
    metric_name = target.get("metric")
    recovered_value = (recovery_result.get("metrics") or {}).get(metric_name)
    paper_target = recovery_result.get("paper_target") or {}
    checks = recovery_result.get("mechanism_checks") or {}
    trace_checks = training_trace.get("mechanism_checks") or {}
    invocation_items = invocations.get("invocations") or []
    errors = []

    if recovery_result.get("is_proxy") is not True:
        errors.append("recovery_result must declare is_proxy true for reduced bandit recovery")
    for key in ["dataset", "split", "metric", "paper_value"]:
        if paper_target.get(key) != target.get(key):
            errors.append(f"paper_target.{key} does not match module_plan.fast_recovery_target")
    if not isinstance(recovered_value, (int, float)):
        errors.append("declared metric is missing or non-numeric")
    elif recovered_value < float(target.get("paper_value", 0.0)):
        errors.append("declared metric is below proxy target threshold")

    required_checks = [
        "stochastic_actions_sampled",
        "score_function_update_computed",
        "baseline_used",
        "reduced_training_executed",
        "optimizer_step_executed",
        "expected_reward_improved",
    ]
    for name in required_checks:
        if checks.get(name) is not True and trace_checks.get(name) is not True:
            errors.append(f"missing true mechanism check: {name}")
    if training_trace.get("params_before") == training_trace.get("params_after"):
        errors.append("training_trace parameters did not change")
    called = {item.get("module") or item.get("skill") for item in invocation_items if isinstance(item, dict)}
    for required in ["score_function_estimator", "reinforce_training_loop", "proxy_recovery_evaluator"]:
        if required not in called:
            errors.append(f"generated skill invocation missing: {required}")

    metric_gap = None if not isinstance(recovered_value, (int, float)) else recovered_value - float(target.get("paper_value", 0.0))
    return {
        "schema_version": 1,
        "accepted": not errors,
        "errors": errors,
        "metric": metric_name,
        "recovered_value": recovered_value,
        "target_value": target.get("paper_value"),
        "metric_gap": metric_gap,
        "mechanism_summary": {name: checks.get(name, trace_checks.get(name)) for name in required_checks},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-plan", required=True)
    parser.add_argument("--recovery-result", required=True)
    parser.add_argument("--training-trace", required=True)
    parser.add_argument("--invocations", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = evaluate_proxy(load_json(args.module_plan), load_json(args.recovery_result), load_json(args.training_trace), load_json(args.invocations))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
