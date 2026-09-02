#!/usr/bin/env python3
"""Evaluate Tent recovery traces and mechanism checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_PROXY_CHECKS = [
    "target_only_adaptation",
    "entropy_loss_computed",
    "normalization_affine_updated",
    "optimizer_step_executed",
    "reduced_training_executed",
]


def evaluate_recovery(recovery: dict, trace: dict, source_manifest: dict | None = None) -> dict:
    failures = []
    metrics = recovery.get("metrics", {})
    if not any(isinstance(value, (int, float)) for value in metrics.values()):
        failures.append("missing_numeric_metric")
    if source_manifest and source_manifest.get("forbidden_sources_detected"):
        failures.append("forbidden_source_detected")
    checks = recovery.get("mechanism_checks", {}) or {}
    if recovery.get("is_proxy"):
        for key in REQUIRED_PROXY_CHECKS:
            if checks.get(key) is not True:
                failures.append(f"missing_or_false_{key}")
    if trace.get("loss_after") is None or trace.get("loss_before") is None:
        failures.append("missing_loss_trace")
    elif trace["loss_after"] >= trace["loss_before"]:
        failures.append("entropy_not_reduced")
    if trace.get("params_before") == trace.get("params_after"):
        failures.append("parameters_unchanged")
    return {"ok": not failures, "failures": failures, "decision": "accept" if not failures else "refine"}


def self_test() -> None:
    recovery = {"is_proxy": True, "metrics": {"entropy_reduction": 0.1}, "mechanism_checks": {key: True for key in REQUIRED_PROXY_CHECKS}}
    trace = {"loss_before": 0.6, "loss_after": 0.4, "params_before": {"scale": 1.0}, "params_after": {"scale": 1.1}}
    assert evaluate_recovery(recovery, trace, {"forbidden_sources_detected": []})["ok"] is True
    bad_trace = {"loss_before": 0.6, "loss_after": 0.7, "params_before": {"scale": 1.0}, "params_after": {"scale": 1.0}}
    assert evaluate_recovery(recovery, bad_trace)["decision"] == "refine"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("recovery", nargs="?")
    parser.add_argument("trace", nargs="?")
    parser.add_argument("--source-manifest", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"ok": True, "self_test": True}))
        return 0
    if not args.recovery or not args.trace:
        raise SystemExit("recovery and trace paths are required unless --self-test is used")
    source_manifest = json.loads(Path(args.source_manifest).read_text(encoding="utf-8")) if args.source_manifest else None
    report = evaluate_recovery(json.loads(Path(args.recovery).read_text(encoding="utf-8")), json.loads(Path(args.trace).read_text(encoding="utf-8")), source_manifest)
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
