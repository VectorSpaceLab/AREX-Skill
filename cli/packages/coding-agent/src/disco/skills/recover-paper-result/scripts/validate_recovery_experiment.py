#!/usr/bin/env python3
"""Validate that a recovery attempt contains executable experiment evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def path_exists(value: object, attempt_dir: Path, base_dir: Path) -> bool:
    if not value:
        return False
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path.exists()
    return (attempt_dir / path).exists() or (base_dir / path).exists()


def existing_training_trace(logs_dir: Path) -> Path | None:
    for name in ["training_trace.json", "training_log.json"]:
        path = logs_dir / name
        if path.exists():
            return path
    return None


def params_changed(trace: dict) -> bool:
    before = trace.get("params_before", trace.get("parameters_before"))
    after = trace.get("params_after", trace.get("parameters_after"))
    return before is not None and after is not None and before != after


def command_succeeded(item: dict) -> bool:
    if item.get("returncode") == 0:
        return True
    if item.get("exit_code") == 0:
        return True
    return str(item.get("status", "")).lower() in {"completed", "success", "succeeded"} and item.get("returncode") in {0, None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_dir", help="Distiller attempt directory.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args(argv)

    attempt_dir = Path(args.attempt_dir).expanduser().resolve()
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    result_path = recovery_dir / "recovery_result.json"
    plan_path = recovery_dir / "experiment_plan.md"
    command_log_path = logs_dir / "experiment_command_log.json"
    evidence_path = logs_dir / "generated_skill_invocations.json"
    source_manifest_path = recovery_dir / "source_manifest.json"

    errors: list[str] = []
    warnings: list[str] = []
    present: list[str] = []

    for rel, path in [
        ("recovery/experiment_plan.md", plan_path),
        ("recovery/logs/experiment_command_log.json", command_log_path),
        ("recovery/logs/generated_skill_invocations.json", evidence_path),
        ("recovery/recovery_result.json", result_path),
        ("recovery/source_manifest.json", source_manifest_path),
    ]:
        if path.exists():
            present.append(rel)
        else:
            errors.append(f"{rel} is missing")

    recovery: dict = {}
    mechanism_checks: dict = {}
    if result_path.exists():
        try:
            recovery = load_json(result_path)
            mechanism_checks = recovery.get("mechanism_checks", {}) or {}
        except Exception as exc:
            errors.append(f"recovery/recovery_result.json is not valid JSON: {exc}")

    if command_log_path.exists():
        try:
            command_log = load_json(command_log_path)
        except Exception as exc:
            command_log = {}
            errors.append(f"recovery/logs/experiment_command_log.json is not valid JSON: {exc}")
        commands = command_log.get("commands")
        if not isinstance(commands, list) or not commands:
            errors.append("experiment command log must contain a non-empty commands list")
        elif not any(command_succeeded(item) for item in commands if isinstance(item, dict)):
            errors.append("experiment command log contains no successful command")
        for item in commands if isinstance(commands, list) else []:
            if not isinstance(item, dict):
                continue
            if "command" not in item:
                errors.append("experiment command entry lacks command")
                break
    if recovery:
        recovery_commands = recovery.get("commands")
        if not isinstance(recovery_commands, list) or not recovery_commands:
            errors.append("recovery_result.json must list the experiment command(s) that produced it")
        metrics = recovery.get("metrics")
        if not isinstance(metrics, dict) or not any(isinstance(value, (int, float)) for value in metrics.values()):
            errors.append("recovery_result.json must contain at least one numeric metric")

    if evidence_path.exists():
        try:
            evidence = load_json(evidence_path)
        except Exception as exc:
            evidence = {}
            errors.append(f"generated skill invocation log is not valid JSON: {exc}")
        invocations = evidence.get("invocations")
        if not isinstance(invocations, list) or not invocations:
            errors.append("generated skill invocation log must contain a non-empty invocations list")
        else:
            for item in invocations:
                if not isinstance(item, dict):
                    errors.append("generated skill invocation entries must be objects")
                    continue
                module = item.get("module") or item.get("skill")
                kind = item.get("evidence") or item.get("kind")
                log_path = item.get("log") or item.get("artifact")
                if not module:
                    errors.append("generated skill invocation entry lacks module/skill")
                if not kind:
                    errors.append(f"generated skill invocation for {module or '<unknown>'} lacks evidence/kind")
                if log_path and not path_exists(log_path, attempt_dir, evidence_path.parent):
                    errors.append(f"generated skill invocation log path does not exist: {log_path}")

    reduced = mechanism_checks.get("reduced_training_executed") is True
    optimizer_step = mechanism_checks.get("optimizer_step_executed") is True
    full_training = mechanism_checks.get("training_step_executed") is True
    required_model_loaded = mechanism_checks.get("qwen3_model_loaded")

    if reduced:
        data_item = logs_dir / "generated_data_item.json"
        if not data_item.exists():
            errors.append("reduced recovery is missing recovery/logs/generated_data_item.json")
        else:
            try:
                data = load_json(data_item)
            except Exception as exc:
                errors.append(f"generated data item is not valid JSON: {exc}")
                data = {}
            resource_files = data.get("resource_files") or data.get("source_files")
            if data.get("is_resource_derived") is True and not resource_files:
                errors.append("resource-derived data item does not list resource_files/source_files")
        trace_path = existing_training_trace(logs_dir)
        if trace_path is None:
            errors.append("reduced recovery is missing recovery/logs/training_trace.json")
        else:
            try:
                trace = load_json(trace_path)
            except Exception as exc:
                trace = {}
                errors.append(f"training trace is not valid JSON: {exc}")
            if "loss_before" not in trace or "loss_after" not in trace:
                errors.append("training trace lacks loss_before/loss_after")
            if optimizer_step and not (params_changed(trace) or trace.get("optimizer_state_changed") is True):
                errors.append("optimizer_step_executed is true but trace shows no parameter or optimizer-state change")
            if "params_before" not in trace or "params_after" not in trace:
                errors.append("training trace must include params_before and params_after for reduced recovery")

    if full_training and required_model_loaded is False:
        errors.append("training_step_executed is true even though qwen3_model_loaded is false")
    if recovery.get("is_proxy") and not mechanism_checks:
        errors.append("proxy recovery is missing mechanism_checks")

    report = {
        "schema_version": 1,
        "ok": not errors,
        "attempt_dir": str(attempt_dir),
        "present": present,
        "errors": errors,
        "warnings": warnings,
    }
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
