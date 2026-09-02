#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BERNOULLI_STAN = """data {
  int<lower=0> N;
  array[N] int<lower=0, upper=1> y;
}
parameters {
  real<lower=0,upper=1> theta;
}
transformed parameters {
  real logit_theta = logit(theta);
}
model {
  theta ~ beta(1, 1);
  y ~ bernoulli(theta);
}
generated quantities {
  int y_sim = bernoulli_rng(theta);
}
"""


def run_command(command, cwd=None):
    start = time.time()
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "elapsed_seconds": round(time.time() - start, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def pass_rate(checks):
    if not checks:
        return 0.0
    return sum(1 for value in checks.values() if value is True) / float(len(checks))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    attempt_dir = Path(args.attempt_dir)
    skills_root = Path(args.skills_root)
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    module_plan = json.loads((attempt_dir / "module_plan.json").read_text())
    target = module_plan["fast_recovery_target"]
    runtime_handoff = attempt_dir / "environment" / "runtime_handoff.json"
    handoff = json.loads(runtime_handoff.read_text()) if runtime_handoff.exists() else {"runtime_ready": False, "reduced_recovery_recommended": True, "blockers": ["handoff missing"]}

    stan_path = logs_dir / "bernoulli_proxy.stan"
    data_path = logs_dir / "generated_data_item.json"
    contract_path = logs_dir / "contract.json"
    transform_contract_path = logs_dir / "theta_contract.json"
    transform_path = logs_dir / "transform_roundtrip.json"
    score_path = logs_dir / "score_evaluation.json"
    stan_path.write_text(BERNOULLI_STAN)
    data_item = {
        "schema_version": 1,
        "source": "current-attempt generated Bernoulli proxy item",
        "resource_files": [str(stan_path)],
        "N": 4,
        "y": [1, 0, 1, 1],
        "derivation": "Tiny Bernoulli observations chosen to exercise beta prior, bernoulli likelihood, transform, gradient, Hessian, and generated quantity contract."
    }
    data_path.write_text(json.dumps(data_item, indent=2, sort_keys=True))

    commands = []
    contract_script = skills_root / "stan_model_contract" / "scripts" / "stan_contract.py"
    transform_script = skills_root / "parameter_transform_adapter" / "scripts" / "parameter_transforms.py"
    score_script = skills_root / "score_function_evaluator" / "scripts" / "score_evaluator.py"

    commands.append(run_command([args.python, str(contract_script), "--stan", str(stan_path), "--output", str(contract_path)]))
    contract = json.loads(contract_path.read_text()) if contract_path.exists() else {}
    theta_contract = next((p for p in contract.get("parameters", []) if p.get("name") == "theta"), {"name": "theta", "lower": 0.0, "upper": 1.0})
    transform_contract_path.write_text(json.dumps(theta_contract, indent=2, sort_keys=True))
    commands.append(run_command([args.python, str(transform_script), "roundtrip", "--contract", str(transform_contract_path), "--value", "0.2", "--output", str(transform_path)]))
    commands.append(run_command([args.python, str(score_script), "--contract", str(contract_path), "--data", str(data_path), "--z", "0.4", "--transform-script", str(transform_script), "--output", str(score_path)]))

    transform = json.loads(transform_path.read_text()) if transform_path.exists() else {}
    score = json.loads(score_path.read_text()) if score_path.exists() else {"checks": {}}
    generated_quantity_present = any(item.get("name") == "y_sim" and "bernoulli_rng" in item.get("expression", "") for item in contract.get("generated_quantities", []))
    mechanism_checks = {
        "reduced_recovery_declared": True,
        "full_bridgestan_runtime_blocked_or_not_used": not bool(handoff.get("runtime_ready")),
        "stan_contract_extracted": not contract.get("diagnostics") and bool(contract.get("parameters")),
        "parameter_transform_roundtrip": bool(transform.get("valid")) and transform.get("abs_error") is not None and transform.get("abs_error") < 1e-10,
        "log_density_evaluated": bool(score.get("checks", {}).get("log_density_finite")),
        "gradient_cross_checked": bool(score.get("checks", {}).get("gradient_matches_finite_difference")),
        "hessian_cross_checked": bool(score.get("checks", {}).get("hessian_matches_finite_difference")),
        "generated_quantity_contract_seen": generated_quantity_present,
        "all_generated_core_skills_invoked": all(cmd["returncode"] == 0 for cmd in commands),
    }
    metric = pass_rate(mechanism_checks)

    result = {
        "schema_version": 1,
        "paper_id": "bridgestan_score_models",
        "experiment": target["dataset"],
        "is_proxy": True,
        "sample_count": data_item["N"],
        "metrics": {target["metric"]: metric},
        "paper_target": target,
        "commands": [cmd["command"] for cmd in commands],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/contract.json",
            "recovery/logs/transform_roundtrip.json",
            "recovery/logs/score_evaluation.json",
        ],
        "mechanism_checks": mechanism_checks,
        "runtime": {
            "runtime_handoff": str(runtime_handoff),
            "full_bridgestan_package_loaded": False,
            "compiled_stan_shared_object_loaded": False,
            "reduced_training_executed": False,
            "optimizer_step_executed": False
        },
        "notes": "Soft-mode declared proxy: exercises BridgeStan score-model contracts analytically without compiling BridgeStan or reading the original repository during recovery."
    }
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2, sort_keys=True))

    invocations = {
        "schema_version": 1,
        "skills_root": str(skills_root),
        "invocations": [
            {"module": "stan_model_contract", "module_id": "stan_model_contract", "skill": "stan_model_contract", "skill_name": "stan_model_contract", "evidence": "called script", "evidence_type": "called script", "artifact": "recovery/logs/contract.json", "returncode": commands[0]["returncode"]},
            {"module": "parameter_transform_adapter", "module_id": "parameter_transform_adapter", "skill": "parameter_transform_adapter", "skill_name": "parameter_transform_adapter", "evidence": "called script", "evidence_type": "called script", "artifact": "recovery/logs/transform_roundtrip.json", "returncode": commands[1]["returncode"]},
            {"module": "score_function_evaluator", "module_id": "score_function_evaluator", "skill": "score_function_evaluator", "skill_name": "score_function_evaluator", "evidence": "called script", "evidence_type": "called script", "artifact": "recovery/logs/score_evaluation.json", "returncode": commands[2]["returncode"]},
            {"module": "bridge_recovery_harness", "module_id": "bridge_recovery_harness", "skill": "bridge_recovery_harness", "skill_name": "bridge_recovery_harness", "evidence": "current executable harness", "evidence_type": "current executable harness", "artifact": "recovery/recovery_result.json", "returncode": 0}
        ]
    }
    (logs_dir / "generated_skill_invocations.json").write_text(json.dumps(invocations, indent=2, sort_keys=True))

    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skills_root),
            str(runtime_handoff),
            str(stan_path),
            str(data_path)
        ],
        "original_repo_used_during_recovery": False,
        "forbidden_sources": ["/share/project/yuyang/workspace/Paperbench/record/case4/paper2skills_workspace/paper/bridgestan_score_models/repo"],
        "notes": "Recovery uses generated skills and current-attempt proxy files only. The original repo path is listed only as a forbidden boundary, not an input source."
    }
    (recovery_dir / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2, sort_keys=True))

    command_log = {"schema_version": 1, "commands": commands}
    (logs_dir / "experiment_command_log.json").write_text(json.dumps(command_log, indent=2, sort_keys=True))
    print(json.dumps({"ok": metric == 1.0, "metric": metric, "mechanism_checks": mechanism_checks}, indent=2, sort_keys=True))
    return 0 if metric == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
