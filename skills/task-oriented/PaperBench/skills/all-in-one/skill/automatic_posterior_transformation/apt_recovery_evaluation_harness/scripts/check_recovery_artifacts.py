#!/usr/bin/env python3
"""Lightweight checks for APT recovery artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = [
    "recovery/experiment_plan.md",
    "recovery/source_manifest.json",
    "recovery/logs/experiment_command_log.json",
    "recovery/logs/generated_skill_invocations.json",
    "recovery/logs/generated_data_item.json",
    "recovery/logs/training_trace.json",
    "recovery/recovery_result.json",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    root = Path(args.attempt_dir).expanduser().resolve()
    errors = []
    for rel in REQUIRED:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    result_path = root / "recovery" / "recovery_result.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        checks = result.get("mechanism_checks") or {}
        for key in [
            "proposal_rounds_executed",
            "posterior_transformation_executed",
            "atomic_loss_executed",
            "optimizer_step_executed",
        ]:
            if checks.get(key) is not True:
                errors.append(f"mechanism check is not true: {key}")
        if not isinstance(result.get("metrics"), dict) or not result["metrics"]:
            errors.append("metrics are missing")
    manifest_path = root / "recovery" / "source_manifest.json"
    if manifest_path.exists():
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")
        manifest = json.loads(manifest_text)
        if manifest.get("forbidden_sources_detected"):
            errors.append("source manifest reports forbidden sources")
        if "runtime_handoff.json" not in manifest_text:
            errors.append("source manifest does not mention runtime_handoff.json")
    report = {"ok": not errors, "attempt_dir": str(root), "errors": errors}
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
