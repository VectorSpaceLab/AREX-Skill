#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REQUIRED_MECHANISMS = [
    "old_policy_log_probs_frozen",
    "clipped_surrogate_computed",
    "positive_and_negative_advantages_used",
    "advantage_normalization_executed",
    "minibatch_epochs_executed",
    "optimizer_step_executed",
    "policy_parameters_changed",
    "expected_reward_improved",
]


def _load(path):
    return json.loads(Path(path).read_text())


def _numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_recovery(module_plan, recovery_result, source_manifest=None, invocation_log=None, original_repo_path=""):
    errors = []
    warnings = []
    target = module_plan.get("fast_recovery_target", {})
    recovered_target = recovery_result.get("paper_target", {})
    for key in ["dataset", "split", "metric", "paper_value", "proxy"]:
        if recovered_target.get(key) != target.get(key):
            errors.append(f"paper_target.{key} does not match module_plan.fast_recovery_target")

    metrics = recovery_result.get("metrics", {})
    if not metrics:
        errors.append("metrics is empty")
    for name, value in metrics.items():
        if not _numeric(value):
            errors.append(f"metric {name} is not numeric")

    if recovery_result.get("is_proxy"):
        mechanisms = recovery_result.get("mechanism_checks", {})
        for name in REQUIRED_MECHANISMS:
            if mechanisms.get(name) is not True:
                errors.append(f"missing or false mechanism check: {name}")
    elif target.get("proxy"):
        warnings.append("module plan target is proxy but recovery_result.is_proxy is false")

    source_boundary_ok = True
    if source_manifest:
        manifest_text = json.dumps(source_manifest)
        forbidden = original_repo_path or source_manifest.get("original_repo_path", "")
        if forbidden and forbidden in manifest_text:
            source_boundary_ok = False
            errors.append("source manifest includes original repository path")

    if invocation_log is not None:
        invocations = invocation_log.get("invocations", [])
        exercised = [entry for entry in invocations if entry.get("evidence_type") != "not applicable"]
        if not exercised:
            errors.append("no generated skills were invoked or cross-checked")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "target_metric": target.get("metric"),
        "metrics": metrics,
        "source_boundary_ok": source_boundary_ok,
        "required_mechanisms": REQUIRED_MECHANISMS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-plan", required=True)
    parser.add_argument("--recovery-result", required=True)
    parser.add_argument("--source-manifest", default="")
    parser.add_argument("--invocation-log", default="")
    parser.add_argument("--original-repo-path", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = evaluate_recovery(
        _load(args.module_plan),
        _load(args.recovery_result),
        _load(args.source_manifest) if args.source_manifest else None,
        _load(args.invocation_log) if args.invocation_log else None,
        args.original_repo_path,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
