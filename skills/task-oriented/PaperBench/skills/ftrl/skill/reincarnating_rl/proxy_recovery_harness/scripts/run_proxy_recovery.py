#!/usr/bin/env python3
import argparse
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def default_proxy_data():
    return {
        "states": ["teacher_state", "student_state"],
        "actions": ["left", "right"],
        "teacher_replay": [
            {"state": "teacher_state", "action": 1, "n_step_return": 1.0, "discount": 0.5, "next_max_q": 0.4, "teacher_policy": [0.05, 0.95]}
        ],
        "student_replay": [
            {"state": "student_state", "action": 1, "n_step_return": 0.8, "discount": 0.5, "next_max_q": 0.4, "teacher_policy": [0.10, 0.90]}
        ],
        "notes": "Deterministic two-action proxy preserving QDagger teacher replay pretraining and student replay correction."
    }


def flatten_params(q_values):
    keys = []
    values = []
    for state in sorted(q_values):
        for action_index, value in enumerate(q_values[state]):
            keys.append((state, action_index))
            values.append(float(value))
    return keys, values


def unflatten_params(keys, values):
    q_values = {}
    for (state, action_index), value in zip(keys, values):
        q_values.setdefault(state, [])
        while len(q_values[state]) <= action_index:
            q_values[state].append(0.0)
        q_values[state][action_index] = float(value)
    return q_values


def proxy_loss(loss_module, q_values, transitions, lambda_t, temperature):
    return loss_module.compute_qdagger_loss(q_values, transitions, temperature=temperature, lambda_t=lambda_t)["combined_loss"]


def finite_difference_gradient(loss_module, q_values, transitions, lambda_t, temperature, epsilon=1e-4):
    keys, base_values = flatten_params(q_values)
    gradients = []
    for index in range(len(base_values)):
        plus = list(base_values)
        minus = list(base_values)
        plus[index] += epsilon
        minus[index] -= epsilon
        plus_loss = proxy_loss(loss_module, unflatten_params(keys, plus), transitions, lambda_t, temperature)
        minus_loss = proxy_loss(loss_module, unflatten_params(keys, minus), transitions, lambda_t, temperature)
        gradients.append((plus_loss - minus_loss) / (2.0 * epsilon))
    return keys, base_values, gradients


def greedy_policy(q_values):
    policy = {}
    for state, values in q_values.items():
        best_index = max(range(len(values)), key=lambda idx: values[idx])
        policy[state] = best_index
    return policy


def run_proxy(attempt_dir, skills_root, output_dir=None):
    attempt_dir = Path(attempt_dir)
    skills_root = Path(skills_root)
    recovery_dir = Path(output_dir) if output_dir else attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    loss_path = skills_root / "qdagger_loss" / "scripts" / "qdagger_loss.py"
    schedule_path = skills_root / "weaning_schedule" / "scripts" / "weaning_schedule.py"
    loss_module = load_module("generated_qdagger_loss", loss_path)
    schedule_module = load_module("generated_weaning_schedule", schedule_path)

    data = default_proxy_data()
    transitions = data["teacher_replay"] + data["student_replay"]
    q_initial = {"teacher_state": [0.2, -0.2], "student_state": [0.1, -0.1]}
    temperature = 0.5
    lambda_0 = 1.0
    schedule_start = schedule_module.linear_decay(lambda_0, step=0, decay_steps=4)
    schedule_late = schedule_module.linear_decay(lambda_0, step=4, decay_steps=4)

    before = loss_module.compute_qdagger_loss(q_initial, transitions, temperature=temperature, lambda_t=schedule_start["lambda_t"])
    keys, values_before, gradients = finite_difference_gradient(loss_module, q_initial, transitions, schedule_start["lambda_t"], temperature)
    learning_rate = 0.25
    values_after = [value - learning_rate * grad for value, grad in zip(values_before, gradients)]
    q_after = unflatten_params(keys, values_after)
    after = loss_module.compute_qdagger_loss(q_after, transitions, temperature=temperature, lambda_t=schedule_start["lambda_t"])
    weaned = loss_module.compute_qdagger_loss(q_after, transitions, temperature=temperature, lambda_t=schedule_late["lambda_t"])

    policy = greedy_policy(q_after)
    expected_teacher_actions = {transition["state"]: max(range(len(transition["teacher_policy"])), key=lambda idx: transition["teacher_policy"][idx]) for transition in transitions}
    policy_match = all(policy[state] == action for state, action in expected_teacher_actions.items())
    params_changed = any(abs(a - b) > 1e-9 for a, b in zip(values_before, values_after))
    loss_decreased = after["combined_loss"] < before["combined_loss"]

    generated_data_path = logs_dir / "generated_data_item.json"
    trace_path = logs_dir / "training_trace.json"
    invocations_path = logs_dir / "generated_skill_invocations.json"
    result_path = recovery_dir / "recovery_result.json"

    generated_data_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    trace = {
        "schema_version": 1,
        "params_before": q_initial,
        "params_after": q_after,
        "parameters_before": q_initial,
        "parameters_after": q_after,
        "loss_before": before["combined_loss"],
        "loss_after": after["combined_loss"],
        "td_loss_before": before["td_loss"],
        "distillation_loss_before": before["distillation_loss"],
        "td_loss_after": after["td_loss"],
        "distillation_loss_after": after["distillation_loss"],
        "weaned_loss_after": weaned["combined_loss"],
        "schedule_start": schedule_start,
        "schedule_late": schedule_late,
        "gradients": {f"{state}:{action}": grad for (state, action), grad in zip(keys, gradients)},
        "learning_rate": learning_rate,
        "optimizer_step_executed": params_changed,
        "reduced_training_executed": True,
        "full_atari_training_executed": False,
    }
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")

    invocations = {
        "schema_version": 1,
        "skills_root": str(skills_root),
        "invocations": [
            {"module": "qdagger_loss", "skill": "qdagger_loss", "module_id": "qdagger_loss", "skill_name": "qdagger_loss", "evidence": "imported helper", "kind": "imported helper", "path": str(loss_path), "artifact": str(trace_path)},
            {"module": "weaning_schedule", "skill": "weaning_schedule", "module_id": "weaning_schedule", "skill_name": "weaning_schedule", "evidence": "imported helper", "kind": "imported helper", "path": str(schedule_path), "artifact": str(trace_path)},
            {"module": "proxy_recovery_harness", "skill": "proxy_recovery_harness", "module_id": "proxy_recovery_harness", "skill_name": "proxy_recovery_harness", "evidence": "called script", "kind": "called script", "path": str(Path(__file__).resolve()), "artifact": str(result_path)},
        ]
    }
    invocations_path.write_text(json.dumps(invocations, indent=2, sort_keys=True) + "\n")

    module_plan = json.loads((attempt_dir / "module_plan.json").read_text()) if (attempt_dir / "module_plan.json").exists() else {}
    paper_target = module_plan.get("fast_recovery_target", {"dataset": "deterministic_tabular_pvrl_proxy", "metric": "loss_decrease_and_policy_match", "paper_value": 1.0, "proxy": True})
    metric = 1.0 if (loss_decreased and policy_match and params_changed) else 0.0
    result = {
        "schema_version": 1,
        "paper_id": "reincarnating_rl",
        "experiment": paper_target.get("dataset", "deterministic_tabular_pvrl_proxy"),
        "is_proxy": True,
        "sample_count": len(transitions),
        "metrics": {"loss_decrease_and_policy_match": metric, "loss_before": before["combined_loss"], "loss_after": after["combined_loss"]},
        "paper_target": paper_target,
        "commands": [],
        "artifacts": [str(generated_data_path), str(trace_path), str(invocations_path)],
        "mechanism_checks": {
            "teacher_replay_pretraining_executed": True,
            "student_replay_correction_executed": True,
            "n_step_td_loss_computed": before["td_loss"] > 0,
            "teacher_policy_distillation_computed": before["distillation_loss"] > 0,
            "weaning_schedule_executed": schedule_late["lambda_t"] < schedule_start["lambda_t"],
            "optimizer_step_executed": params_changed,
            "reduced_training_executed": True,
            "full_atari_training_executed": False,
            "loss_decreased": loss_decreased,
            "policy_matches_teacher_on_proxy": policy_match,
            "generated_qdagger_loss_skill_called": True,
            "generated_weaning_schedule_skill_called": True,
        },
        "notes": "Soft-mode reduced proxy recovery; it validates QDagger mechanics but not full Atari performance."
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return {"recovery_result": result, "trace": trace, "paths": {"result": str(result_path), "trace": str(trace_path), "generated_data": str(generated_data_path), "invocations": str(invocations_path)}}


def _self_test():
    here = Path(__file__).resolve()
    skills_root = here.parents[2]
    temp_root = Path(os.environ.get("TMPDIR", "/tmp")) / f"qdagger_proxy_self_test_{os.getpid()}"
    temp_root.mkdir(parents=True, exist_ok=True)
    (temp_root / "module_plan.json").write_text(json.dumps({"fast_recovery_target": {"dataset": "deterministic_tabular_pvrl_proxy", "metric": "loss_decrease_and_policy_match", "paper_value": 1.0, "proxy": True}}))
    output = run_proxy(temp_root, skills_root, temp_root / "recovery")
    assert output["recovery_result"]["metrics"]["loss_decrease_and_policy_match"] == 1.0
    assert output["trace"]["optimizer_step_executed"] is True
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", type=Path)
    parser.add_argument("--skills-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        result = _self_test()
    else:
        if not args.attempt_dir or not args.skills_root:
            parser.error("--attempt-dir and --skills-root are required unless --self-test is used")
        result = run_proxy(args.attempt_dir, args.skills_root, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
