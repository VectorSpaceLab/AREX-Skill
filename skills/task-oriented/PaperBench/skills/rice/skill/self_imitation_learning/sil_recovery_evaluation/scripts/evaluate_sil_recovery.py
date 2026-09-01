#!/usr/bin/env python3
"""Evaluate SIL recovery evidence beyond the generic Distiller gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_sil_recovery(recovery_result: dict, command_log: dict, invocation_log: dict, source_manifest: dict, original_repo_path: str = "") -> dict:
    errors = []
    warnings = []
    sources = json.dumps(source_manifest)
    if original_repo_path and original_repo_path in sources:
        errors.append("original repository path appears in recovery source manifest")
    commands = command_log.get("commands", [])
    if not any(item.get("returncode") == 0 for item in commands):
        errors.append("no successful experiment command recorded")
    invocations = invocation_log.get("invocations", [])
    if not invocations:
        errors.append("no generated skill invocations recorded")
    checks = recovery_result.get("mechanism_checks", {})
    required = [
        "replay_records_inserted",
        "positive_advantage_gate_checked",
        "sil_loss_computed",
        "optimizer_step_executed",
        "parameters_changed",
    ]
    for key in required:
        if checks.get(key) is not True:
            errors.append(f"missing or false mechanism check: {key}")
    metrics = recovery_result.get("metrics", {})
    if "sil_loss_decrease" not in metrics:
        errors.append("missing sil_loss_decrease metric")
    elif metrics["sil_loss_decrease"] <= 0:
        errors.append("sil_loss_decrease must be positive")
    if recovery_result.get("is_proxy") is True and not checks.get("reduced_training_executed"):
        errors.append("proxy recovery must record reduced_training_executed")
    if checks.get("full_actor_critic_runtime") is True and recovery_result.get("is_proxy") is True:
        warnings.append("proxy result claims full actor-critic runtime; inspect runtime handoff")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "metrics": metrics, "mechanism_checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recovery_result")
    parser.add_argument("command_log")
    parser.add_argument("invocation_log")
    parser.add_argument("source_manifest")
    parser.add_argument("--original-repo-path", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = evaluate_sil_recovery(
        json.loads(Path(args.recovery_result).read_text(encoding="utf-8")),
        json.loads(Path(args.command_log).read_text(encoding="utf-8")),
        json.loads(Path(args.invocation_log).read_text(encoding="utf-8")),
        json.loads(Path(args.source_manifest).read_text(encoding="utf-8")),
        args.original_repo_path,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
