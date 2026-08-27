#!/usr/bin/env python3
"""Validate the artifact contract for a distillation attempt."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


STAGE_REQUIREMENTS = {
    "initialized": ["run_manifest.json"],
    "modularized": [
        "run_manifest.json",
        "paper_profile.md",
        "module_plan.json",
        "modules",
    ],
    "skills": [
        "run_manifest.json",
        "paper_profile.md",
        "module_plan.json",
        "modules",
        "generated_skills_validation",
    ],
    "recovered": [
        "run_manifest.json",
        "paper_profile.md",
        "module_plan.json",
        "modules",
        "generated_skills_validation",
        "environment/runtime_handoff.json",
        "recovery/source_manifest.json",
        "recovery/recovery_result.json",
    ],
    "analyzed": [
        "run_manifest.json",
        "paper_profile.md",
        "module_plan.json",
        "modules",
        "generated_skills_validation",
        "environment/runtime_handoff.json",
        "recovery/source_manifest.json",
        "recovery/recovery_result.json",
        "analysis/analysis_report.json",
        "analysis/feedback.md",
    ],
    "reported": [
        "run_manifest.json",
        "paper_profile.md",
        "module_plan.json",
        "modules",
        "generated_skills_validation",
        "environment/runtime_handoff.json",
        "recovery/experiment_validation.json",
        "recovery/source_manifest.json",
        "recovery/recovery_result.json",
        "analysis/analysis_report.json",
        "analysis/feedback.md",
        "final_validation.json",
        "reports/final/final_report.md",
        "reports/final/final_report.json",
    ],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def training_trace_exists(logs_dir: Path) -> bool:
    return (logs_dir / "training_trace.json").exists() or (logs_dir / "training_log.json").exists()


def existing_training_trace(logs_dir: Path) -> Path | None:
    for name in ["training_trace.json", "training_log.json"]:
        path = logs_dir / name
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


def runtime_constraints_require_isolated_env(manifest: dict, run_config: dict) -> bool:
    text = " ".join(
        str(value or "")
        for value in [
            manifest.get("runtime_constraints"),
            run_config.get("runtime_constraints"),
        ]
    ).lower()
    return (
        "isolated env" in text
        or "isolated environment" in text
        or "use isolated" in text
        or "private recovery env" in text
        or "do not mutate shared conda" in text
    )


def has_isolated_env_attempt(runtime_handoff: dict, command_log: dict) -> bool:
    labels = command_labels(command_log)
    if any(label.startswith("create_isolated_") for label in labels):
        return True
    for action in setup_actions(runtime_handoff):
        action_name = str(action.get("action") or "")
        if action_name.startswith(("create_isolated_", "reuse_isolated_")):
            return True
    return False


def selected_private_python(runtime_handoff: dict) -> bool:
    environment = runtime_handoff.get("environment") or {}
    python_block = runtime_handoff.get("python") or {}
    manager = str(environment.get("manager") or "current")
    executable = str(environment.get("python") or python_block.get("executable") or "")
    host_executable = str(python_block.get("host_executable") or "")
    return bool(executable and manager != "current" and executable != host_executable)


def package_install_attempted(import_name: str, runtime_handoff: dict, command_log: dict) -> bool:
    expected_label = f"pip_install_{import_name}"
    if expected_label in command_labels(command_log):
        return True
    for action in setup_actions(runtime_handoff):
        if action.get("action") == "pip_install" and action.get("import_name") == import_name:
            return True
    return False


def runtime_setup_evidence_issues(runtime_handoff: dict, command_log: dict, manifest: dict, run_config: dict) -> list[str]:
    issues: list[str] = []
    setup = environment_setup(runtime_handoff)
    setup_text = blocker_text(setup.get("blockers"), runtime_handoff.get("blockers"))
    isolated_required = runtime_constraints_require_isolated_env(manifest, run_config)
    isolated_attempted = has_isolated_env_attempt(runtime_handoff, command_log)

    if isolated_required:
        if not isolated_attempted:
            issues.append(
                "runtime constraints require an isolated recovery env, but environment setup did not record a create/reuse isolated-env attempt"
            )
        elif not selected_private_python(runtime_handoff) and not setup_text:
            issues.append(
                "runtime constraints require an isolated recovery env, but runtime_handoff selected host/current Python without a logged isolated-env blocker"
            )

    packages = runtime_handoff.get("packages")
    if isinstance(packages, dict):
        missing_packages = [str(name) for name, present in packages.items() if present is False]
    else:
        missing_packages = []
    mutation_allowed = bool(runtime_handoff.get("environment_mutation_allowed")) or isolated_required
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


def recovery_uses_handoff_python(runtime_handoff: dict, root: Path, source_manifest_path: Path | None) -> tuple[bool, str]:
    environment = runtime_handoff.get("environment") or {}
    python_block = runtime_handoff.get("python") or {}
    manager = str(environment.get("manager") or "current")
    executable = str(environment.get("python") or python_block.get("executable") or "")
    host_executable = str(python_block.get("host_executable") or "")
    if not executable or manager == "current" or executable == host_executable:
        return True, ""
    experiment_log = root / "recovery" / "logs" / "experiment_command_log.json"
    if file_contains(experiment_log, executable):
        return True, ""
    if source_manifest_path and file_contains(source_manifest_path, executable):
        return True, ""
    return False, f"recovery did not record use of private recovery Python: {executable}"


def run_recovery_experiment_gate(root: Path) -> dict:
    script = Path(__file__).resolve().parents[1] / ".." / "recover-paper-result" / "scripts" / "validate_recovery_experiment.py"
    script = script.resolve()
    if not script.exists():
        return {"ok": False, "errors": [f"recovery experiment gate script is missing: {script}"]}
    proc = subprocess.run(
        [sys.executable, str(script), str(root), "--output", str(root / "recovery" / "experiment_validation.json")],
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


def valid_recovery_mode(value: object) -> bool:
    return value in {"hard", "soft"}


def effective_recovery_mode(manifest: dict, run_config: dict) -> str:
    if valid_recovery_mode(run_config.get("recovery_mode")):
        return str(run_config["recovery_mode"])
    if valid_recovery_mode(manifest.get("recovery_mode")):
        return str(manifest["recovery_mode"])
    return "hard"


def planned_modules(root: Path, errors: list[str]) -> list[dict]:
    plan_path = root / "module_plan.json"
    if not plan_path.exists():
        return []
    try:
        plan = load_json(plan_path)
    except Exception as exc:
        errors.append(f"module_plan.json is not valid JSON: {exc}")
        return []
    modules = plan.get("modules")
    if not isinstance(modules, list):
        errors.append("module_plan.json modules must be a list")
        return []
    return [module for module in modules if isinstance(module, dict)]


def module_skill_validations(root: Path, modules: list[dict], errors: list[str], present: list[str]) -> None:
    validation_dir = root / "generated_skills_validation"
    if not modules:
        return
    for module in modules:
        module_id = str(module.get("id") or "").strip()
        skill_name = str(module.get("skill_name") or module_id).strip()
        label = module_id or skill_name or "<unknown>"
        if not module_id:
            errors.append("module_plan.json contains a module without id")
            continue
        path = validation_dir / f"{module_id}.json"
        rel = f"generated_skills_validation/{module_id}.json"
        if not path.exists():
            errors.append(f"missing generated skill validation for module {label}: {rel}")
            continue
        if rel not in present:
            present.append(rel)
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(f"{rel} is not valid JSON: {exc}")
            continue
        if data.get("ok") is not True:
            errors.append(f"{rel} does not report ok: true")
        tests = data.get("tests")
        if not isinstance(tests, dict):
            errors.append(f"{rel} does not include tests result metadata")
            continue
        if tests.get("attempted") is not True:
            errors.append(f"{rel} did not attempt generated skill tests or smoke checks")
        if tests.get("ok") is False:
            errors.append(f"{rel} reports failing generated skill tests")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_dir", help="Distillation directory to validate.")
    parser.add_argument(
        "--stage",
        choices=sorted(STAGE_REQUIREMENTS),
        default="analyzed",
        help="Validation stage.",
    )
    parser.add_argument("--output", default="", help="Optional path to save the validation JSON.")
    args = parser.parse_args(argv)

    root = Path(args.attempt_dir).expanduser().resolve()
    missing = []
    present = []
    errors = []
    warnings = []
    for rel in STAGE_REQUIREMENTS[args.stage]:
        path = root / rel
        if path.exists():
            present.append(rel)
        else:
            missing.append(rel)

    modules: list[dict] = []
    if args.stage in {"skills", "recovered", "analyzed", "reported"}:
        modules = planned_modules(root, errors)
        module_skill_validations(root, modules, errors, present)

    manifest_path = root / "run_manifest.json"
    manifest: dict = {}
    run_config: dict = {}
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
        except Exception as exc:
            errors.append(f"run_manifest.json is not valid JSON: {exc}")
            manifest = {}
        if "iteration_budget" in manifest:
            budget = manifest.get("iteration_budget")
            if not isinstance(budget, int) or budget < 0:
                errors.append("run_manifest.json iteration_budget must be a non-negative integer")
        else:
            warnings.append("run_manifest.json does not record iteration_budget; default is 10 for new runs")
        if "recovery_mode" in manifest:
            if not valid_recovery_mode(manifest.get("recovery_mode")):
                errors.append("run_manifest.json recovery_mode must be 'hard' or 'soft'")
        else:
            warnings.append("run_manifest.json does not record recovery_mode; default is hard for new runs")

    run_config_path = root / "run_config.normalized.json"
    if run_config_path.exists():
        present.append("run_config.normalized.json")
        try:
            run_config = load_json(run_config_path)
        except Exception as exc:
            errors.append(f"run_config.normalized.json is not valid JSON: {exc}")
            run_config = {}
        for key in ["workspace_root", "paper_slug", "paper_source", "iteration_budget", "recovery_mode"]:
            if key not in run_config:
                errors.append(f"run_config.normalized.json is missing {key}")
        budget = run_config.get("iteration_budget")
        if not isinstance(budget, int) or budget < 0:
            errors.append("run_config.normalized.json iteration_budget must be a non-negative integer")
        if manifest and "iteration_budget" in manifest and isinstance(budget, int) and budget != manifest.get("iteration_budget"):
            errors.append("run_config.normalized.json iteration_budget does not match run_manifest.json")
        if "recovery_mode" in run_config and not valid_recovery_mode(run_config.get("recovery_mode")):
            errors.append("run_config.normalized.json recovery_mode must be 'hard' or 'soft'")
        if (
            manifest
            and "recovery_mode" in manifest
            and "recovery_mode" in run_config
            and valid_recovery_mode(manifest.get("recovery_mode"))
            and valid_recovery_mode(run_config.get("recovery_mode"))
            and manifest.get("recovery_mode") != run_config.get("recovery_mode")
        ):
            errors.append("run_config.normalized.json recovery_mode does not match run_manifest.json")

    if args.stage in {"recovered", "analyzed", "reported"}:
        runtime_handoff_path = root / "environment" / "runtime_handoff.json"
        command_log_path = root / "environment" / "logs" / "command_log.json"
        experiment_validation_path = root / "recovery" / "experiment_validation.json"
        recovery_result_path = root / "recovery" / "recovery_result.json"
        source_manifest_path = root / "recovery" / "source_manifest.json"
        logs_dir = root / "recovery" / "logs"
        runtime_handoff = {}
        command_log = {}
        mode = effective_recovery_mode(manifest, run_config)
        if runtime_handoff_path.exists():
            try:
                runtime_handoff = load_json(runtime_handoff_path)
            except Exception as exc:
                errors.append(f"environment/runtime_handoff.json is not valid JSON: {exc}")
        if not command_log_path.exists():
            errors.append("environment/logs/command_log.json is missing")
        else:
            try:
                command_log = load_json(command_log_path)
            except Exception as exc:
                errors.append(f"environment/logs/command_log.json is not valid JSON: {exc}")
                command_log = {}
            if not isinstance(command_log.get("commands"), list):
                errors.append("environment/logs/command_log.json does not contain a commands list")
        if runtime_handoff:
            errors.extend(runtime_setup_evidence_issues(runtime_handoff, command_log, manifest, run_config))
        stages = manifest.get("stages", {}) if isinstance(manifest, dict) else {}
        prepare_stage = stages.get("prepare_environment") if isinstance(stages, dict) else None
        if prepare_stage not in {"complete", "blocked"}:
            errors.append("run_manifest.json stages.prepare_environment must be complete or blocked before recovery")
        if recovery_result_path.exists():
            try:
                recovery = load_json(recovery_result_path)
            except Exception as exc:
                errors.append(f"recovery/recovery_result.json is not valid JSON: {exc}")
                recovery = {}
            mechanism_checks = recovery.get("mechanism_checks", {}) or {}
            if mode == "hard":
                if recovery.get("is_proxy") is True:
                    errors.append("hard recovery mode does not allow accepting proxy recovery as success")
                if mechanism_checks.get("reduced_training_executed") is True:
                    errors.append("hard recovery mode does not allow accepting reduced training as success")
                if mechanism_checks.get("fallback_used") is True or mechanism_checks.get("toy_or_proxy_fallback_used") is True:
                    errors.append("hard recovery mode does not allow accepting fallback recovery as success")
            if mechanism_checks.get("reduced_training_executed") is True:
                if not (logs_dir / "generated_data_item.json").exists():
                    errors.append("reduced recovery is missing recovery/logs/generated_data_item.json")
                trace_path = existing_training_trace(logs_dir)
                if trace_path is None:
                    errors.append("reduced recovery is missing recovery/logs/training_trace.json or training_log.json")
                else:
                    try:
                        trace = load_json(trace_path)
                    except Exception as exc:
                        errors.append(f"reduced recovery training trace is not valid JSON: {exc}")
                        trace = {}
                    if "loss_before" not in trace or "loss_after" not in trace:
                        errors.append("reduced recovery training trace lacks loss_before/loss_after")
                    if mechanism_checks.get("optimizer_step_executed") is True:
                        optimizer_changed = bool(trace.get("optimizer_state_changed"))
                        if not trace_params_changed(trace) and not optimizer_changed:
                            errors.append(
                                "optimizer_step_executed is true but training trace shows no parameter or optimizer-state change"
                            )
                if mechanism_checks.get("training_step_executed") is True and mechanism_checks.get("qwen3_model_loaded") is False:
                    errors.append("full training_step_executed is true even though the required model was not loaded")
            if runtime_handoff:
                model_ready = bool((runtime_handoff.get("models") or {}).get("preferred_ready"))
                if mechanism_checks.get("qwen3_model_loaded") is True and not model_ready:
                    errors.append("qwen3_model_loaded is true but runtime_handoff.models.preferred_ready is not true")
        if recovery_result_path.exists():
            gate = run_recovery_experiment_gate(root)
            if experiment_validation_path.exists() and "recovery/experiment_validation.json" not in present:
                present.append("recovery/experiment_validation.json")
            if not gate.get("ok", False):
                errors.extend([f"recovery experiment gate: {issue}" for issue in gate.get("errors", [])])
        if source_manifest_path.exists():
            try:
                source_manifest = load_json(source_manifest_path)
            except Exception as exc:
                errors.append(f"recovery/source_manifest.json is not valid JSON: {exc}")
                source_manifest = {}
            forbidden = source_manifest.get("forbidden_sources_detected", [])
            if forbidden:
                errors.append(f"source manifest reports forbidden sources: {forbidden}")
            manifest_text = source_manifest_path.read_text(encoding="utf-8", errors="replace")
            if runtime_handoff_path.exists() and "runtime_handoff.json" not in manifest_text:
                errors.append("source manifest does not mention environment/runtime_handoff.json")
            benchmark_sources = source_manifest.get("benchmark_sources", {})
            reused_values = [
                value
                for key, value in benchmark_sources.items()
                if "reused" in key and value
            ]
            if reused_values:
                resource_files = benchmark_sources.get("alfworld_resource_files_used") or benchmark_sources.get("resource_files_used")
                snapshot = benchmark_sources.get("alfworld_snapshot_dir") or benchmark_sources.get("snapshot_dir")
                if not any("blocker" in key and value for key, value in benchmark_sources.items()):
                    errors.append("reused benchmark source is missing a fresh-fetch blocker")
                if not resource_files:
                    errors.append("reused benchmark source is missing concrete resource files used")
                if not manifest_path_exists(snapshot, root, source_manifest_path.parent):
                    errors.append("reused benchmark source is missing a current-attempt resource snapshot")
        if runtime_handoff:
            uses_handoff_python, handoff_python_issue = recovery_uses_handoff_python(
                runtime_handoff,
                root,
                source_manifest_path if source_manifest_path.exists() else None,
            )
            if not uses_handoff_python:
                errors.append(handoff_python_issue)
        if not logs_dir.exists():
            warnings.append("recovery/logs directory is missing")

    result = {
        "ok": not missing and not errors,
        "stage": args.stage,
        "attempt_dir": str(root),
        "present": present,
        "missing": missing,
        "errors": errors,
        "warnings": warnings,
    }
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
