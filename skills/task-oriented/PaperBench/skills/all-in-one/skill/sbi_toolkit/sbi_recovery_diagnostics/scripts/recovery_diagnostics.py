#!/usr/bin/env python3
"""Validate SBI recovery diagnostics and source-boundary evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def params_changed(trace: dict) -> bool:
    before = trace.get("params_before", trace.get("parameters_before"))
    after = trace.get("params_after", trace.get("parameters_after"))
    return before is not None and after is not None and before != after


def validate_recovery_artifacts(attempt_dir: Path, forbidden_substring: str = "/sources/repo") -> dict:
    attempt_dir = attempt_dir.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    recovery_path = attempt_dir / "recovery" / "recovery_result.json"
    source_path = attempt_dir / "recovery" / "source_manifest.json"
    trace_path = attempt_dir / "recovery" / "logs" / "training_trace.json"
    data_path = attempt_dir / "recovery" / "logs" / "generated_data_item.json"
    invocation_path = attempt_dir / "recovery" / "logs" / "generated_skill_invocations.json"
    handoff_path = attempt_dir / "environment" / "runtime_handoff.json"

    for path in [recovery_path, source_path, invocation_path, handoff_path]:
        if not path.exists():
            errors.append(f"missing required artifact: {path.relative_to(attempt_dir)}")

    recovery = load_json(recovery_path) if recovery_path.exists() else {}
    mechanism = recovery.get("mechanism_checks", {}) or {}
    metrics = recovery.get("metrics", {})
    if not isinstance(metrics, dict) or not any(isinstance(value, (int, float)) for value in metrics.values()):
        errors.append("recovery result lacks a numeric metric")

    if mechanism.get("reduced_training_executed") is True:
        if not data_path.exists():
            errors.append("reduced recovery is missing generated_data_item.json")
        if not trace_path.exists():
            errors.append("reduced recovery is missing training_trace.json")
        else:
            trace = load_json(trace_path)
            if "loss_before" not in trace or "loss_after" not in trace:
                errors.append("training trace lacks before/after loss")
            if mechanism.get("optimizer_step_executed") is True and not (
                params_changed(trace) or trace.get("optimizer_state_changed") is True
            ):
                errors.append("optimizer step was claimed but no parameter or optimizer-state change was recorded")

    if source_path.exists():
        source_text = source_path.read_text(encoding="utf-8", errors="replace")
        if forbidden_substring and forbidden_substring in source_text:
            errors.append("source manifest includes the forbidden original repository path")
        source = load_json(source_path)
        if source.get("forbidden_sources_detected"):
            errors.append("source manifest reports forbidden sources")

    if invocation_path.exists():
        invocations = load_json(invocation_path).get("invocations", [])
        if not invocations:
            errors.append("generated skill invocation log is empty")

    if mechanism.get("posterior_api_checked") is not True:
        warnings.append("posterior API check was not explicitly marked true")

    return {
        "schema_version": 1,
        "ok": not errors,
        "attempt_dir": str(attempt_dir),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    result = validate_recovery_artifacts(Path(args.attempt_dir))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
