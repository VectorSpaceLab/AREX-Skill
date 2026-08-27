#!/usr/bin/env python3
"""Write the final organized Paper2Skills distillation report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except Exception as exc:
        return {"_parse_error": str(exc)}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def load_module_validations(root: Path, module_plan: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for module in module_plan.get("modules", []) if isinstance(module_plan.get("modules"), list) else []:
        if not isinstance(module, dict):
            continue
        module_id = str(module.get("id") or "")
        path = root / "generated_skills_validation" / f"{module_id}.json"
        data = optional_json(path)
        tests = data.get("tests") if isinstance(data.get("tests"), dict) else {}
        results.append(
            {
                "module_id": module_id,
                "skill_name": module.get("skill_name") or module_id,
                "validation_path": rel(path, root),
                "ok": data.get("ok"),
                "tests_attempted": tests.get("attempted"),
                "tests_ok": tests.get("ok"),
                "errors": data.get("errors", []),
                "warnings": data.get("warnings", []),
            }
        )
    return results


def issue_bucket(report: dict[str, Any]) -> dict[str, list[str]]:
    critical: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    final_validation = report.get("final_validation", {})
    if final_validation.get("ok") is False:
        critical.extend([f"final validation: {item}" for item in final_validation.get("errors", [])])
        critical.extend([f"missing artifact: {item}" for item in final_validation.get("missing", [])])
    warnings.extend([f"final validation: {item}" for item in final_validation.get("warnings", [])])

    recovery_gate = report.get("recovery_gate", {})
    if recovery_gate.get("ok") is False:
        critical.extend([f"recovery gate: {item}" for item in recovery_gate.get("errors", [])])

    analysis = report.get("analysis", {})
    if analysis.get("decision") not in {"accept", None}:
        critical.extend([f"analysis feedback: {item}" for item in analysis.get("feedback", [])])
    if analysis.get("source_issues"):
        critical.extend([f"source issue: {item}" for item in analysis.get("source_issues", [])])
    if analysis.get("mechanism_issues"):
        critical.extend([f"mechanism issue: {item}" for item in analysis.get("mechanism_issues", [])])

    for item in report.get("module_skill_validations", []):
        if item.get("ok") is not True:
            critical.append(f"module {item.get('module_id')} validation did not pass")
        if item.get("tests_attempted") is not True:
            critical.append(f"module {item.get('module_id')} did not attempt tests")
        if item.get("warnings"):
            warnings.extend([f"module {item.get('module_id')}: {warning}" for warning in item.get("warnings", [])])

    runtime = report.get("runtime_handoff", {})
    for blocker in runtime.get("blockers", []) if isinstance(runtime.get("blockers"), list) else []:
        notes.append(f"runtime blocker: {blocker}")

    if not critical and not warnings and not notes:
        notes.append("No blocking issues were reported by the available gates.")

    return {
        "critical": critical,
        "warnings": warnings,
        "notes": notes,
    }


def wants_chinese(language_preference: str) -> bool:
    lowered = language_preference.lower()
    return "chinese" in lowered or "中文" in language_preference or "汉语" in language_preference


def markdown_report(report: dict[str, Any], issues: dict[str, list[str]]) -> str:
    manifest = report.get("manifest", {})
    module_plan = report.get("module_plan", {})
    recovery = report.get("recovery_result", {})
    analysis = report.get("analysis", {})
    final_validation = report.get("final_validation", {})
    language = str(report.get("language_preference") or "")
    chinese = wants_chinese(language)

    if chinese:
        lines = [
            "# Paper2Skills 最终报告",
            "",
            f"- 论文/运行: `{manifest.get('slug', module_plan.get('paper_id', 'unknown'))}`",
            f"- Distillation directory: `{report.get('distillation_dir', report.get('attempt_dir'))}`",
            f"- Generated skills: `{manifest.get('generated_skills_root', '')}`",
            f"- Recovery mode: `{manifest.get('recovery_mode', 'hard')}`",
            f"- Analysis decision: `{analysis.get('decision', 'unknown')}`",
            f"- Final validation ok: `{final_validation.get('ok')}`",
            "",
            "## Recovery",
            "",
            f"- Target: `{recovery.get('paper_target', module_plan.get('fast_recovery_target', {}))}`",
            f"- Metrics: `{recovery.get('metrics', {})}`",
            f"- Proxy: `{recovery.get('is_proxy', False)}`",
            "",
            "## Generated Skill Validation",
        ]
    else:
        lines = [
            "# Paper2Skills Final Report",
            "",
            f"- Paper/run: `{manifest.get('slug', module_plan.get('paper_id', 'unknown'))}`",
            f"- Distillation directory: `{report.get('distillation_dir', report.get('attempt_dir'))}`",
            f"- Generated skills: `{manifest.get('generated_skills_root', '')}`",
            f"- Recovery mode: `{manifest.get('recovery_mode', 'hard')}`",
            f"- Analysis decision: `{analysis.get('decision', 'unknown')}`",
            f"- Final validation ok: `{final_validation.get('ok')}`",
            "",
            "## Recovery",
            "",
            f"- Target: `{recovery.get('paper_target', module_plan.get('fast_recovery_target', {}))}`",
            f"- Metrics: `{recovery.get('metrics', {})}`",
            f"- Proxy: `{recovery.get('is_proxy', False)}`",
            "",
            "## Generated Skill Validation",
        ]

    validations = report.get("module_skill_validations", [])
    if validations:
        for item in validations:
            lines.append(
                f"- `{item.get('module_id')}` -> `{item.get('skill_name')}`: "
                f"ok=`{item.get('ok')}`, tests_attempted=`{item.get('tests_attempted')}`, tests_ok=`{item.get('tests_ok')}`"
            )
    else:
        lines.append("- No module validation summaries found.")

    lines.extend(["", "## Issues"])
    for label in ["critical", "warnings", "notes"]:
        lines.extend(["", f"### {label.title()}"])
        if issues[label]:
            lines.extend([f"- {item}" for item in issues[label]])
        else:
            lines.append("- None.")

    lines.extend(
        [
            "",
            "## Artifact Index",
            "",
            f"- Environment handoff: `{report.get('artifact_index', {}).get('runtime_handoff', '')}`",
            f"- Environment command log: `{report.get('artifact_index', {}).get('environment_command_log', '')}`",
            f"- Recovery validation: `{report.get('artifact_index', {}).get('recovery_gate', '')}`",
            f"- Analysis report: `{report.get('artifact_index', {}).get('analysis_report', '')}`",
            f"- Final validation: `{report.get('artifact_index', {}).get('final_validation', '')}`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_report(root: Path, language_preference: str) -> dict[str, Any]:
    manifest = optional_json(root / "run_manifest.json")
    run_config = optional_json(root / "run_config.normalized.json")
    module_plan = optional_json(root / "module_plan.json")
    final_validation = optional_json(root / "final_validation.json")
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "distillation_dir": str(root),
        "attempt_dir": str(root),
        "language_preference": language_preference or run_config.get("language_preference") or "English summary",
        "manifest": manifest,
        "run_config": run_config,
        "module_plan": module_plan,
        "module_skill_validations": load_module_validations(root, module_plan),
        "runtime_handoff": optional_json(root / "environment" / "runtime_handoff.json"),
        "environment_command_log": optional_json(root / "environment" / "logs" / "command_log.json"),
        "recovery_result": optional_json(root / "recovery" / "recovery_result.json"),
        "recovery_gate": optional_json(root / "recovery" / "experiment_validation.json"),
        "analysis": optional_json(root / "analysis" / "analysis_report.json"),
        "final_validation": final_validation,
        "artifact_index": {
            "runtime_handoff": "environment/runtime_handoff.json",
            "environment_command_log": "environment/logs/command_log.json",
            "recovery_gate": "recovery/experiment_validation.json",
            "analysis_report": "analysis/analysis_report.json",
            "final_validation": "final_validation.json",
            "final_report_json": "reports/final/final_report.json",
            "final_report_md": "reports/final/final_report.md",
        },
    }
    report["issues"] = issue_bucket(report)
    report["ok"] = (
        final_validation.get("ok") is True
        and not report["issues"]["critical"]
        and report["analysis"].get("decision") in {"accept", None}
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_dir", help="Distillation directory.")
    parser.add_argument("--language-preference", default="", help="Optional summary language preference.")
    parser.add_argument("--output-dir", default="", help="Report output dir. Defaults to <distillation_dir>/reports/final.")
    args = parser.parse_args(argv)

    root = Path(args.attempt_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else root / "reports" / "final"
    report = build_report(root, args.language_preference)
    issues = report["issues"]

    json_path = output_dir / "final_report.json"
    md_path = output_dir / "final_report.md"
    write_json(json_path, report)
    md_path.write_text(markdown_report(report, issues), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "json": str(json_path), "markdown": str(md_path), "issues": issues}, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
