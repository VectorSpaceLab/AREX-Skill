#!/usr/bin/env python3
"""Compare a recovery result with a declared target and emit an analysis report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def existing_training_trace(logs_dir: Path) -> Path | None:
    candidates = [
        logs_dir / "training_trace.json",
        logs_dir / "training_log.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def trace_params_changed(trace: dict) -> bool:
    before = trace.get("params_before", trace.get("parameters_before"))
    after = trace.get("params_after", trace.get("parameters_after"))
    return before is not None and after is not None and before != after


def manifest_path_exists(value: object, attempt_dir: Path, manifest_dir: Path) -> bool:
    if not value:
        return False
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path.exists()
    return (attempt_dir / path).exists() or (manifest_dir / path).exists()


def file_contains(path: Path, needle: str) -> bool:
    if not needle or not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8", errors="replace")


def command_entries(command_log: dict) -> list[dict]:
    commands = command_log.get("commands")
    if not isinstance(commands, list):
        return []
    return [entry for entry in commands if isinstance(entry, dict)]


def command_labels(command_log: dict) -> set[str]:
    return {str(entry.get("label") or "") for entry in command_entries(command_log)}


def environment_setup(runtime_handoff: dict) -> dict:
    environment = runtime_handoff.get("environment")
    if not isinstance(environment, dict):
        return {}
    setup = environment.get("setup")
    return setup if isinstance(setup, dict) else {}


def setup_actions(runtime_handoff: dict) -> list[dict]:
    actions = environment_setup(runtime_handoff).get("actions")
    if not isinstance(actions, list):
        return []
    return [action for action in actions if isinstance(action, dict)]


def blocker_text(*values: object) -> str:
    fragments: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, str):
            fragments.append(value)
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    for value in values:
        collect(value)
    return " ".join(fragments).lower()


def mentions_user_request(text: str) -> bool:
    return any(token in text for token in ["ask", "asked", "user", "permission", "credential", "api key", "token"])


def has_isolated_env_attempt(runtime_handoff: dict, command_log: dict) -> bool:
    labels = command_labels(command_log)
    if any(label.startswith("create_isolated_") for label in labels):
        return True
    for action in setup_actions(runtime_handoff):
        action_name = str(action.get("action") or "")
        if action_name.startswith(("create_isolated_", "reuse_isolated_")):
            return True
    return False


def package_install_attempted(import_name: str, runtime_handoff: dict, command_log: dict) -> bool:
    expected_label = f"pip_install_{import_name}"
    if expected_label in command_labels(command_log):
        return True
    for action in setup_actions(runtime_handoff):
        if action.get("action") == "pip_install" and action.get("import_name") == import_name:
            return True
    return False


def runtime_setup_evidence_issues(runtime_handoff: dict, command_log: dict) -> list[str]:
    issues: list[str] = []
    isolated_attempted = has_isolated_env_attempt(runtime_handoff, command_log)
    packages = runtime_handoff.get("packages")
    if isinstance(packages, dict):
        missing_packages = [str(name) for name, present in packages.items() if present is False]
    else:
        missing_packages = []
    mutation_allowed = bool(runtime_handoff.get("environment_mutation_allowed"))

    if missing_packages and mutation_allowed:
        if not isolated_attempted:
            issues.append(
                "packages are missing, but environment setup did not record isolated environment creation/reuse before blocking: "
                + ", ".join(missing_packages)
            )
        for package in missing_packages:
            if not package_install_attempted(package, runtime_handoff, command_log):
                issues.append(f"missing package '{package}' has no recorded targeted pip install attempt")

    models = runtime_handoff.get("models")
    if isinstance(models, dict) and models.get("required") and not models.get("preferred_ready"):
        download = models.get("download") if isinstance(models.get("download"), dict) else {}
        cache_hits = models.get("cache_hits") if isinstance(models.get("cache_hits"), list) else []
        model_issue_text = blocker_text(models.get("blockers"), download.get("blockers"), runtime_handoff.get("blockers"))
        if not cache_hits and not download.get("attempted") and "model_snapshot_download" not in command_labels(command_log):
            if not mentions_user_request(model_issue_text):
                issues.append(
                    "required model is unavailable, but environment setup did not record a bounded model download attempt or a user permission/credential request"
                )

    datasets = runtime_handoff.get("datasets")
    if isinstance(datasets, dict):
        for dataset_name, dataset in datasets.items():
            if not isinstance(dataset, dict) or not dataset.get("required"):
                continue
            paths = dataset.get("paths") if isinstance(dataset.get("paths"), list) else []
            downloaded = dataset.get("downloaded_files") if isinstance(dataset.get("downloaded_files"), list) else []
            urls = dataset.get("urls") if isinstance(dataset.get("urls"), list) else []
            dataset_issue_text = blocker_text(dataset.get("blockers"), runtime_handoff.get("blockers"))
            if paths or downloaded:
                continue
            if urls and not dataset.get("download_attempted"):
                issues.append(f"required dataset '{dataset_name}' has URLs but no recorded bounded download attempt")
            elif not urls and not mentions_user_request(dataset_issue_text):
                issues.append(
                    f"required dataset '{dataset_name}' is unavailable, but setup did not record a source URL/path request"
                )

    return issues


def recovery_uses_handoff_python(runtime_handoff: dict, recovery_dir: Path, source_manifest_path: Path | None) -> tuple[bool, str]:
    environment = runtime_handoff.get("environment") or {}
    python_block = runtime_handoff.get("python") or {}
    manager = str(environment.get("manager") or "current")
    executable = str(environment.get("python") or python_block.get("executable") or "")
    host_executable = str(python_block.get("host_executable") or "")
    if not executable or manager == "current" or executable == host_executable:
        return True, ""

    experiment_log = recovery_dir / "logs" / "experiment_command_log.json"
    if file_contains(experiment_log, executable):
        return True, ""
    if source_manifest_path and file_contains(source_manifest_path, executable):
        return True, ""
    return False, f"recovery did not record use of private recovery Python: {executable}"


def normalized_metric_value(value: object) -> float | None:
    try:
        number = float(value)
    except Exception:
        return None
    if number > 1.0:
        number = number / 100.0
    return number


def normalized_text(value: object) -> str:
    return " ".join(str(value or "").lower().split())


def run_recovery_experiment_gate(attempt_dir: Path) -> dict:
    script = Path(__file__).resolve().parents[2] / "recover-paper-result" / "scripts" / "validate_recovery_experiment.py"
    if not script.exists():
        return {"ok": False, "errors": [f"recovery experiment gate script is missing: {script}"]}
    proc = subprocess.run(
        [sys.executable, str(script), str(attempt_dir), "--output", str(attempt_dir / "recovery" / "experiment_validation.json")],
        text=True,
        capture_output=True,
        timeout=120,
    )
    try:
        data = json.loads(proc.stdout)
    except Exception:
        data = {"ok": False, "errors": ["recovery experiment gate did not emit valid JSON"], "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]}
    if proc.returncode != 0 and data.get("ok") is not False:
        data["ok"] = False
        data.setdefault("errors", []).append(f"recovery experiment gate exited with {proc.returncode}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-plan", required=True, help="module_plan.json path.")
    parser.add_argument("--recovery-result", required=True, help="recovery_result.json path.")
    parser.add_argument("--source-manifest", default="", help="Optional recovery source manifest.")
    parser.add_argument("--runtime-handoff", default="", help="Optional environment/runtime_handoff.json path.")
    parser.add_argument("--validation-dir", default="", help="Optional directory of module validation JSON files.")
    parser.add_argument("--output", required=True, help="Output analysis_report.json.")
    parser.add_argument("--tolerance", type=float, default=0.05, help="Allowed absolute metric gap for full reproduction.")
    parser.add_argument("--proxy-min", type=float, default=0.8, help="Minimum primary metric for proxy acceptance.")
    args = parser.parse_args()

    recovery_result_path = Path(args.recovery_result).expanduser().resolve()
    module_plan = load_json(Path(args.module_plan).expanduser().resolve())
    recovery = load_json(recovery_result_path)
    recovery_dir = recovery_result_path.parent
    attempt_dir = recovery_dir.parent if recovery_dir.name == "recovery" else recovery_dir
    logs_dir = recovery_dir / "logs"
    target = module_plan.get("fast_recovery_target", {}) or recovery.get("paper_target", {})
    recovery_target = recovery.get("paper_target", {})
    metric_name = str(target.get("metric", recovery.get("primary_metric", "f1"))).lower()
    metrics = recovery.get("metrics", {})
    recovered_value = metrics.get(metric_name)
    if recovered_value is None and metrics:
        metric_name, recovered_value = next(iter(metrics.items()))
    try:
        recovered_float = float(recovered_value)
    except Exception:
        recovered_float = None

    paper_value_raw = target.get("paper_value", target.get("value"))
    paper_value = normalized_metric_value(paper_value_raw)

    target_consistency_ok = True
    target_issues: list[str] = []
    if target and recovery_target:
        plan_metric = normalized_text(target.get("metric"))
        recovery_metric = normalized_text(recovery_target.get("metric"))
        if plan_metric and recovery_metric and plan_metric != recovery_metric:
            target_consistency_ok = False
            target_issues.append(f"target metric mismatch: module_plan={plan_metric}, recovery_result={recovery_metric}")

        plan_dataset = normalized_text(target.get("dataset"))
        recovery_dataset = normalized_text(recovery_target.get("dataset"))
        if plan_dataset and recovery_dataset and plan_dataset != recovery_dataset:
            target_consistency_ok = False
            target_issues.append(
                f"target dataset mismatch: module_plan={target.get('dataset')}, recovery_result={recovery_target.get('dataset')}"
            )

        recovery_paper_value = normalized_metric_value(recovery_target.get("paper_value", recovery_target.get("value")))
        if paper_value is not None and recovery_paper_value is not None and abs(paper_value - recovery_paper_value) > 1e-6:
            target_consistency_ok = False
            target_issues.append(
                f"target value mismatch: module_plan={paper_value:.6f}, recovery_result={recovery_paper_value:.6f}"
            )

    source_boundary_ok = True
    source_issues: list[str] = []
    runtime_handoff = {}
    runtime_handoff_path = Path(args.runtime_handoff).expanduser().resolve() if args.runtime_handoff else recovery_dir.parent / "environment" / "runtime_handoff.json"
    source_manifest_path: Path | None = None
    if runtime_handoff_path.exists():
        try:
            runtime_handoff = load_json(runtime_handoff_path)
        except Exception as exc:
            source_boundary_ok = False
            source_issues.append(f"could not parse runtime handoff: {exc}")
        command_log = {}
        command_log_path = runtime_handoff_path.parent / "logs" / "command_log.json"
        if not command_log_path.exists():
            source_boundary_ok = False
            source_issues.append("environment/logs/command_log.json is missing.")
        else:
            try:
                command_log = load_json(command_log_path)
            except Exception as exc:
                source_boundary_ok = False
                source_issues.append(f"could not parse environment command log: {exc}")
            else:
                if not isinstance(command_log.get("commands"), list):
                    source_boundary_ok = False
                    source_issues.append("environment/logs/command_log.json does not contain a commands list.")
        if runtime_handoff:
            setup_issues = runtime_setup_evidence_issues(runtime_handoff, command_log)
            if setup_issues:
                source_boundary_ok = False
                source_issues.extend(setup_issues)
    if args.source_manifest:
        source_manifest_path = Path(args.source_manifest).expanduser().resolve()
        source_manifest = load_json(source_manifest_path)
        forbidden = source_manifest.get("forbidden_sources_detected", [])
        if forbidden:
            source_boundary_ok = False
            source_issues.extend([str(item) for item in forbidden])
        manifest_text = source_manifest_path.read_text(encoding="utf-8", errors="replace")
        if runtime_handoff_path.exists() and "runtime_handoff.json" not in manifest_text:
            source_boundary_ok = False
            source_issues.append("source manifest does not mention environment/runtime_handoff.json.")
        benchmark_sources = source_manifest.get("benchmark_sources", {})
        reused_values = [
            value
            for key, value in benchmark_sources.items()
            if "reused" in key and value
        ]
        if reused_values:
            blocker = any("blocker" in key and value for key, value in benchmark_sources.items())
            resource_files = benchmark_sources.get("alfworld_resource_files_used") or benchmark_sources.get("resource_files_used")
            snapshot = benchmark_sources.get("alfworld_snapshot_dir") or benchmark_sources.get("snapshot_dir")
            if not blocker:
                source_boundary_ok = False
                source_issues.append("reused benchmark checkout is recorded without the fresh-fetch blocker.")
            if not resource_files:
                source_boundary_ok = False
                source_issues.append("reused benchmark checkout is recorded without concrete resource files used.")
            if not manifest_path_exists(snapshot, attempt_dir, source_manifest_path.parent):
                source_boundary_ok = False
                source_issues.append("reused benchmark checkout is recorded without a current-attempt resource snapshot.")

    if runtime_handoff:
        uses_handoff_python, handoff_python_issue = recovery_uses_handoff_python(
            runtime_handoff,
            recovery_dir,
            source_manifest_path,
        )
        if not uses_handoff_python:
            source_boundary_ok = False
            source_issues.append(handoff_python_issue)

    validation_ok = True
    validation_issues: list[str] = []
    if args.validation_dir:
        validation_dir = Path(args.validation_dir).expanduser().resolve()
        for path in sorted(validation_dir.glob("*.json")):
            try:
                data = load_json(path)
            except Exception as exc:
                validation_ok = False
                validation_issues.append(f"{path.name}: could not parse ({exc})")
                continue
            if not data.get("ok", False):
                validation_ok = False
                validation_issues.append(f"{path.name}: validation failed")
    experiment_gate = run_recovery_experiment_gate(attempt_dir)
    if not experiment_gate.get("ok", False):
        validation_ok = False
        validation_issues.extend([f"recovery experiment gate: {issue}" for issue in experiment_gate.get("errors", [])])

    is_proxy = bool(recovery.get("is_proxy", target.get("proxy", False)))
    mechanism_checks = recovery.get("mechanism_checks", {}) or {}
    mechanism_ok = True
    mechanism_issues: list[str] = []
    if is_proxy and not mechanism_checks:
        mechanism_ok = False
        mechanism_issues.append("proxy recovery did not provide mechanism_checks, so it cannot demonstrate that the paper mechanism was exercised.")
    if mechanism_checks:
        if runtime_handoff:
            model_ready = bool((runtime_handoff.get("models") or {}).get("preferred_ready"))
            if mechanism_checks.get("qwen3_model_loaded") is True and not model_ready:
                mechanism_ok = False
                mechanism_issues.append("qwen3_model_loaded is true but runtime_handoff.models.preferred_ready is not true.")
        if (
            mechanism_checks.get("alfworld_repo_obtained") is True
            and mechanism_checks.get("benchmark_resource_provenance_recorded") is False
        ):
            mechanism_ok = False
            mechanism_issues.append("benchmark source was obtained but benchmark_resource_provenance_recorded is false.")
        if (
            mechanism_checks.get("qwen3_model_loaded") is False
            and mechanism_checks.get("training_step_executed") is True
        ):
            mechanism_ok = False
            mechanism_issues.append("full training_step_executed is true even though the required Qwen model was not loaded.")
        if mechanism_checks.get("reduced_training_executed") is True:
            data_item = logs_dir / "generated_data_item.json"
            if not data_item.exists():
                mechanism_ok = False
                mechanism_issues.append("reduced recovery did not save recovery/logs/generated_data_item.json.")
            trace_path = existing_training_trace(logs_dir)
            if trace_path is None:
                mechanism_ok = False
                mechanism_issues.append("reduced recovery did not save recovery/logs/training_trace.json or training_log.json.")
            else:
                try:
                    trace = load_json(trace_path)
                except Exception as exc:
                    mechanism_ok = False
                    mechanism_issues.append(f"could not parse reduced training trace {trace_path.name}: {exc}")
                else:
                    has_loss = "loss_before" in trace and "loss_after" in trace
                    has_metric = any(str(key).endswith("_before") for key in trace) and any(
                        str(key).endswith("_after") for key in trace
                    )
                    params_changed = trace_params_changed(trace)
                    optimizer_changed = bool(trace.get("optimizer_state_changed"))
                    if not (has_loss or has_metric):
                        mechanism_ok = False
                        mechanism_issues.append("reduced training trace lacks before/after loss or metric values.")
                    if mechanism_checks.get("optimizer_step_executed") is True and not (params_changed or optimizer_changed):
                        mechanism_ok = False
                        mechanism_issues.append("optimizer_step_executed is true but the trace shows no parameter or optimizer-state change.")
        if mechanism_checks.get("required_queries_ok") is False:
            mechanism_ok = False
            covered = mechanism_checks.get("covered_requirements", {})
            mechanism_issues.append(f"required search requirements were not covered: {covered}")
        if mechanism_checks.get("grounding_ok") is False:
            mechanism_ok = False
            mechanism_issues.append("Reason-in-Documents produced unsupported downstream facts; inspect mechanism_checks.grounding_issues.")
        live_search_count = mechanism_checks.get("live_search_count")
        try:
            if int(live_search_count) <= 0:
                mechanism_ok = False
                mechanism_issues.append("recovery did not execute any live or recorded search events.")
        except Exception:
            pass
    gap = None
    metric_ok = False
    if recovered_float is not None:
        if is_proxy:
            metric_ok = recovered_float >= args.proxy_min
        elif paper_value is not None:
            gap = abs(recovered_float - paper_value)
            metric_ok = gap <= args.tolerance
        else:
            metric_ok = recovered_float > 0.0

    decision = "accept" if source_boundary_ok and validation_ok and target_consistency_ok and mechanism_ok and metric_ok else "refine"
    feedback = []
    if not target_consistency_ok:
        feedback.append("Recovery target metadata does not match module_plan.fast_recovery_target; update the plan or rerun recovery against the declared target.")
    if not source_boundary_ok:
        if any("forbidden" in issue.lower() or "original" in issue.lower() for issue in source_issues):
            feedback.append("Recovery used forbidden original repository sources; rerun recovery with only paper, module docs, generated skills, and datasets.")
        else:
            feedback.append("Recovery source or runtime provenance is incomplete; fix the listed source_issues and rerun analysis.")
    if not validation_ok:
        if any("recovery experiment gate" in issue for issue in validation_issues):
            feedback.append("Recovery experiment evidence is incomplete or not executable; fix experiment_plan, experiment_command_log, generated_skill_invocations, data/training traces, or the recovery harness before acceptance.")
        else:
            feedback.append("At least one generated module skill failed validation; inspect generated_skills_validation and fix the failing skill.")
    if not mechanism_ok:
        feedback.append("Recovery metric passed but mechanism checks failed; refine the relevant module skill and rerun recovery.")
    if recovered_float is None:
        feedback.append("Recovery did not produce a numeric primary metric.")
    elif not metric_ok and is_proxy:
        feedback.append(f"Proxy metric {metric_name}={recovered_float:.4f} is below proxy minimum {args.proxy_min:.4f}; strengthen the recovery harness or module behavior.")
    elif not metric_ok:
        feedback.append(f"Recovered {metric_name}={recovered_float:.4f} is outside tolerance for paper target {paper_value}.")
    if not feedback:
        feedback.append("No blocking issues found. Keep the generated skills and record the proxy/full reproduction scope clearly.")

    report = {
        "schema_version": 1,
        "decision": decision,
        "is_proxy": is_proxy,
        "metric": metric_name,
        "recovered_value": recovered_float,
        "paper_value": paper_value,
        "gap": gap,
        "tolerance": args.tolerance,
        "proxy_min": args.proxy_min,
        "target_consistency_ok": target_consistency_ok,
        "target_issues": target_issues,
        "target_dataset": target.get("dataset"),
        "recovery_target": recovery_target,
        "mechanism_ok": mechanism_ok,
        "mechanism_issues": mechanism_issues,
        "mechanism_checks": mechanism_checks,
        "runtime_handoff_checked": runtime_handoff_path.exists(),
        "source_boundary_ok": source_boundary_ok,
        "validation_ok": validation_ok,
        "source_issues": source_issues,
        "validation_issues": validation_issues,
        "experiment_gate": experiment_gate,
        "feedback": feedback,
    }
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if decision == "accept" else 2


if __name__ == "__main__":
    raise SystemExit(main())
