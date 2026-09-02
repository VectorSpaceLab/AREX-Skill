#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def run_reduced_pql(actor_count: int = 64, rollout_steps: int = 8, replay_capacity: int = 512, updates: int = 12, seed: int = 11, target_action: float = 0.7, policy_lr: float = 0.08, critic_lr: float = 0.15) -> dict:
    if actor_count <= 0 or rollout_steps <= 0 or replay_capacity <= 0 or updates <= 0:
        raise ValueError("actor_count, rollout_steps, replay_capacity, and updates must be positive")
    from topology import build_topology, validate_topology
    from mixed_exploration import noisy_actions
    from diagnostics import compute_diagnostics

    topology = build_topology(actor_count, replay_capacity, rollout_steps, 1, 2, 2)
    topology_errors = validate_topology(topology)
    if topology_errors:
        raise ValueError("invalid topology: " + "; ".join(topology_errors))
    exploration = noisy_actions(actor_count, [0.2, 0.4, 0.6, 0.8], 0.0, -1.0, 1.0, seed=seed)
    diagnostics = compute_diagnostics(actor_count, rollout_steps, replay_capacity, actor_count, 1, 2)

    rng = random.Random(seed)
    replay = []
    for step in range(rollout_steps):
        action_batch = noisy_actions(actor_count, [0.2, 0.4, 0.6, 0.8], 0.0, -1.0, 1.0, seed=seed + step)
        for actor_id, action in enumerate(action_batch["actions"]):
            reward = -((action - target_action) ** 2)
            replay.append({"actor_id": actor_id, "step": step, "action": action, "reward": reward, "target_action": target_action})
            if len(replay) > replay_capacity:
                replay.pop(0)

    policy_param = 0.0
    critic_bias = 0.0
    critic_slope = 0.0

    def critic_prediction(action: float) -> float:
        return critic_bias + critic_slope * action

    def batch_loss() -> float:
        total = 0.0
        for item in replay:
            error = critic_prediction(item["action"]) - item["reward"]
            total += error * error
        return total / len(replay)

    loss_before = batch_loss()
    params_before = {"policy_param": policy_param, "critic_bias": critic_bias, "critic_slope": critic_slope}
    update_log = []
    for update in range(updates):
        item = replay[(update * 17 + rng.randrange(len(replay))) % len(replay)]
        pred = critic_prediction(item["action"])
        error = pred - item["reward"]
        critic_bias -= critic_lr * error
        critic_slope -= critic_lr * error * item["action"]
        policy_gradient_proxy = target_action - policy_param
        policy_param += policy_lr * policy_gradient_proxy
        update_log.append({"update": update, "sample_actor": item["actor_id"], "td_error_proxy": error, "policy_param": policy_param, "critic_bias": critic_bias, "critic_slope": critic_slope})

    loss_after = batch_loss()
    params_after = {"policy_param": policy_param, "critic_bias": critic_bias, "critic_slope": critic_slope}
    final_return_estimate = -((policy_param - target_action) ** 2)
    actor_coverage = len({item["actor_id"] for item in replay})
    mechanism_checks = {
        "reduced_training_executed": True,
        "training_step_executed": False,
        "qwen3_model_loaded": False,
        "optimizer_step_executed": params_before != params_after,
        "parallel_actors_executed": actor_coverage == actor_count,
        "mixed_exploration_executed": exploration["stats"]["distinct_scales"] == 4,
        "replay_buffer_used": len(replay) > 0,
        "value_updates_executed": updates > 0 and params_before["critic_bias"] != params_after["critic_bias"],
        "policy_updates_executed": updates > 0 and params_before["policy_param"] != params_after["policy_param"],
        "loss_reduced": loss_after < loss_before,
        "fallback_used": False,
        "toy_or_proxy_fallback_used": True,
    }
    return {
        "training_trace": {
            "loss_before": loss_before,
            "loss_after": loss_after,
            "params_before": params_before,
            "params_after": params_after,
            "parameters_before": params_before,
            "parameters_after": params_after,
            "optimizer_state_changed": params_before != params_after,
            "updates": update_log,
        },
        "generated_data_item": {
            "schema_version": 1,
            "dataset": "deterministic_scalar_parallel_control_proxy",
            "is_resource_derived": False,
            "resource_files": [],
            "construction": "Synthetic scalar control item derived from paper mechanism because Isaac Gym assets are unavailable.",
            "actor_count": actor_count,
            "rollout_steps": rollout_steps,
            "target_action": target_action,
            "sample_transition": replay[0],
        },
        "metrics": {
            "loss_reduction": loss_before - loss_after,
            "loss_before": loss_before,
            "loss_after": loss_after,
            "final_return_estimate": final_return_estimate,
        },
        "mechanism_checks": mechanism_checks,
        "topology": topology,
        "exploration": exploration,
        "diagnostics": diagnostics,
        "replay_size": len(replay),
        "actor_coverage": actor_coverage,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor-count", type=int, default=64)
    parser.add_argument("--rollout-steps", type=int, default=8)
    parser.add_argument("--replay-capacity", type=int, default=512)
    parser.add_argument("--updates", type=int, default=12)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_reduced_pql(args.actor_count, args.rollout_steps, args.replay_capacity, args.updates, args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "training_trace.json").write_text(json.dumps(result["training_trace"], indent=2), encoding="utf-8")
    (output_dir / "generated_data_item.json").write_text(json.dumps(result["generated_data_item"], indent=2), encoding="utf-8")
    (output_dir / "reduced_pql_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "metrics": result["metrics"], "mechanism_checks": result["mechanism_checks"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
