#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REQUIRED_CHECKS = [
    "synthetic_data_constructed",
    "uniform_coupling_evaluated",
    "batchot_coupling_evaluated",
    "doubly_stochastic_checked",
    "joint_cfm_loss_computed",
    "optimizer_step_executed",
    "reduced_training_executed",
]
REQUIRED_MODULES = {"batch_coupling", "joint_cfm_loss", "synthetic_recovery_harness", "msfm_evaluation"}


def evaluate(recovery_result, training_trace, invocations, min_reduction=0.0):
    failures = []
    hints = []
    checks = recovery_result.get("mechanism_checks", {})
    for key in REQUIRED_CHECKS:
        if checks.get(key) is not True:
            failures.append(f"missing_or_false:{key}")
            hints.append(f"Refine the module responsible for {key} evidence.")
    if checks.get("original_repo_read") is True:
        failures.append("source_boundary:original_repo_read")
        hints.append("Remove original repository access from recovery.")
    if checks.get("full_image_training_executed") is True and recovery_result.get("is_proxy") is True:
        failures.append("inconsistent_full_training_claim")
        hints.append("Keep full-runtime booleans false for proxy recovery.")
    reduction = recovery_result.get("metrics", {}).get("batchot_transport_cost_reduction")
    if not isinstance(reduction, (int, float)) or reduction <= min_reduction:
        failures.append("metric:transport_reduction_not_positive")
        hints.append("Improve or debug BatchOT coupling construction.")
    if training_trace.get("params_before") == training_trace.get("params_after"):
        failures.append("optimizer:parameters_unchanged")
        hints.append("Ensure the Joint CFM optimizer update changes trainable parameters.")
    if training_trace.get("loss_after", 1e99) >= training_trace.get("loss_before", -1e99):
        failures.append("optimizer:loss_not_reduced")
        hints.append("Tune the tiny optimizer step or loss skill.")
    invoked = {item.get("module_id") or item.get("module") or item.get("skill") for item in invocations.get("invocations", [])}
    missing_modules = sorted(REQUIRED_MODULES - invoked)
    if missing_modules:
        failures.append("invocations:missing:" + ",".join(missing_modules))
        hints.append("Call or cross-check every generated core module in recovery.")
    return {
        "schema_version": 1,
        "ok": not failures,
        "metric": "batchot_transport_cost_reduction",
        "observed_metric": reduction,
        "min_required": min_reduction,
        "failures": failures,
        "hints": hints,
    }


def _self_test():
    recovery = {"is_proxy": True, "metrics": {"batchot_transport_cost_reduction": 0.5}, "mechanism_checks": {key: True for key in REQUIRED_CHECKS}}
    recovery["mechanism_checks"].update({"original_repo_read": False, "full_image_training_executed": False})
    trace = {"params_before": {"w": [0]}, "params_after": {"w": [1]}, "loss_before": 2.0, "loss_after": 1.0}
    invocations = {"invocations": [{"module_id": key} for key in REQUIRED_MODULES]}
    assert evaluate(recovery, trace, invocations)["ok"] is True
    recovery["mechanism_checks"]["batchot_coupling_evaluated"] = False
    assert evaluate(recovery, trace, invocations)["ok"] is False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery-result")
    parser.add_argument("--training-trace")
    parser.add_argument("--invocations")
    parser.add_argument("--output")
    parser.add_argument("--min-reduction", type=float, default=0.0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    report = evaluate(
        json.loads(Path(args.recovery_result).read_text()),
        json.loads(Path(args.training_trace).read_text()),
        json.loads(Path(args.invocations).read_text()),
        args.min_reduction,
    )
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
