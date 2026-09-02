#!/usr/bin/env python3
"""Evaluate OPAL recovery evidence and proxy mechanism checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_PROXY_CHECKS = [
    "offline_segments_constructed",
    "primitive_autoencoding_loss_computed",
    "prior_matching_penalty_computed",
    "optimizer_step_executed",
    "latent_relabeling_executed",
    "high_level_latent_control_executed",
    "temporal_abstraction_verified",
]


def evaluate_recovery(module_plan, recovery_result, source_manifest=None, invocations=None):
    target = module_plan["fast_recovery_target"]
    recovered_target = recovery_result.get("paper_target", {})
    target_matches = (
        recovered_target.get("dataset") == target.get("dataset")
        and recovered_target.get("metric") == target.get("metric")
        and recovered_target.get("paper_value") == target.get("paper_value")
    )
    metric_value = recovery_result.get("metrics", {}).get(target.get("metric"))
    mechanism_checks = recovery_result.get("mechanism_checks", {})
    missing_checks = [name for name in REQUIRED_PROXY_CHECKS if not mechanism_checks.get(name)]
    original_repo_used = False
    if source_manifest:
        for item in source_manifest.get("sources", []):
            if item.get("role") == "original_repo":
                original_repo_used = True
    invoked = []
    if invocations:
        invoked = [item.get("module") or item.get("module_id") for item in invocations.get("invocations", []) if (item.get("evidence") or item.get("evidence_type")) != "not applicable"]
    paper_value = target.get("paper_value")
    metric_gap = None if metric_value is None or paper_value is None else float(metric_value) - float(paper_value)
    ok = bool(target_matches and metric_value is not None and not missing_checks and not original_repo_used and invoked)
    return {
        "ok": ok,
        "target_matches": target_matches,
        "metric_value": metric_value,
        "paper_value": paper_value,
        "metric_gap": metric_gap,
        "missing_mechanism_checks": missing_checks,
        "original_repo_used": original_repo_used,
        "invoked_modules": invoked,
        "is_proxy": bool(recovery_result.get("is_proxy")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_plan_json")
    parser.add_argument("recovery_result_json")
    parser.add_argument("--source-manifest")
    parser.add_argument("--invocations")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    module_plan = json.loads(Path(args.module_plan_json).read_text(encoding="utf-8"))
    recovery_result = json.loads(Path(args.recovery_result_json).read_text(encoding="utf-8"))
    source_manifest = json.loads(Path(args.source_manifest).read_text(encoding="utf-8")) if args.source_manifest else None
    invocations = json.loads(Path(args.invocations).read_text(encoding="utf-8")) if args.invocations else None
    result = evaluate_recovery(module_plan, recovery_result, source_manifest, invocations)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
