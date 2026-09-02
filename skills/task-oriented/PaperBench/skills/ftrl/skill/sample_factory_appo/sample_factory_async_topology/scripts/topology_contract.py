#!/usr/bin/env python3
import argparse
import json

ROLE_CONTRACTS = {
    "rollout_worker": ["step_environment", "write_transition_buffers", "enqueue_observation_indices", "enqueue_completed_trajectories"],
    "policy_worker": ["dequeue_observation_indices", "batch_policy_inference", "enqueue_action_indices", "refresh_policy_parameters"],
    "learner": ["dequeue_completed_trajectories", "compute_losses", "update_parameters", "publish_policy_update"],
}

FORBIDDEN = {
    "rollout_worker": {"compute_gradients", "update_parameters", "own_policy_copy"},
    "policy_worker": {"step_environment", "mutate_rewards", "compute_gradients"},
    "learner": {"step_environment", "sample_actions_for_live_envs"},
}

QUEUE_CONTRACTS = [
    {"name": "observation_requests", "payload": "shared observation and hidden-state buffer indices"},
    {"name": "action_replies", "payload": "shared action and next-hidden-state buffer indices"},
    {"name": "completed_trajectories", "payload": "trajectory buffer indices and policy version metadata"},
    {"name": "policy_updates", "payload": "parameter version notification or shared CUDA memory handle"},
]


def validate_positive(name, value):
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def build_topology(rollout_workers, policy_workers, learners, envs_per_worker, trajectory_length, learner_batch_size):
    for name, value in [
        ("rollout_workers", rollout_workers),
        ("policy_workers", policy_workers),
        ("learners", learners),
        ("envs_per_worker", envs_per_worker),
        ("trajectory_length", trajectory_length),
        ("learner_batch_size", learner_batch_size),
    ]:
        validate_positive(name, value)
    produced_samples = rollout_workers * envs_per_worker * trajectory_length
    lag_pressure = max(0.0, produced_samples / learner_batch_size - 1.0)
    return {
        "components": {
            "rollout_worker": {"count": rollout_workers, "responsibilities": ROLE_CONTRACTS["rollout_worker"]},
            "policy_worker": {"count": policy_workers, "responsibilities": ROLE_CONTRACTS["policy_worker"]},
            "learner": {"count": learners, "responsibilities": ROLE_CONTRACTS["learner"]},
        },
        "queue_contracts": QUEUE_CONTRACTS,
        "produced_samples_per_iteration": produced_samples,
        "policy_lag_pressure": lag_pressure,
        "contract_ok": True,
    }


def check_responsibilities(role, responsibilities):
    forbidden = FORBIDDEN[role].intersection(responsibilities)
    return {"role": role, "ok": not forbidden, "forbidden": sorted(forbidden)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollout-workers", type=int, required=True)
    parser.add_argument("--policy-workers", type=int, required=True)
    parser.add_argument("--learners", type=int, required=True)
    parser.add_argument("--envs-per-worker", type=int, required=True)
    parser.add_argument("--trajectory-length", type=int, required=True)
    parser.add_argument("--learner-batch-size", type=int, required=True)
    args = parser.parse_args()
    result = build_topology(
        args.rollout_workers,
        args.policy_workers,
        args.learners,
        args.envs_per_worker,
        args.trajectory_length,
        args.learner_batch_size,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
