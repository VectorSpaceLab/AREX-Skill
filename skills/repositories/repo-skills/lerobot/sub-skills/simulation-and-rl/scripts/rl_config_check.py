#!/usr/bin/env python3
"""Run bounded, static checks on a LeRobot RL JSON configuration.

This tool validates common TrainRLServerPipelineConfig/SAC/HIL-SERL fields
without importing a policy, constructing an environment, starting gRPC, loading
weights, contacting the Hub, or running a training step.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


KNOWN_REWARD_TYPES = {"reward_classifier", "sarm", "robometer", "topreward"}
KNOWN_ALGORITHMS = {"sac"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _add_error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _check_positive_number(data: dict[str, Any], key: str, errors: list[str], *, allow_zero: bool = False) -> None:
    if key not in data:
        return
    value = data[key]
    if not _is_number(value) or (value < 0 if allow_zero else value <= 0):
        bound = "non-negative" if allow_zero else "positive"
        _add_error(errors, key, f"must be a {bound} number, got {value!r}")


def _check_nested_number(
    data: dict[str, Any], path: str, key: str, errors: list[str], *, allow_zero: bool = False
) -> None:
    value = data.get(key)
    if value is None:
        return
    if not _is_number(value) or (value < 0 if allow_zero else value <= 0):
        bound = "non-negative" if allow_zero else "positive"
        _add_error(errors, f"{path}.{key}", f"must be a {bound} number, got {value!r}")


def validate_config(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    effective = dict(config)
    effective.update({key: value for key, value in overrides.items() if value is not None})

    algorithm_value = effective.get("algorithm", "sac")
    if isinstance(algorithm_value, str):
        algorithm_type = algorithm_value
        algorithm = {}
    elif isinstance(algorithm_value, dict):
        algorithm = algorithm_value
        algorithm_type = algorithm.get("type", "sac")
    else:
        algorithm = {}
        algorithm_type = None
        _add_error(errors, "algorithm", "must be a string or object")

    if algorithm_type not in KNOWN_ALGORITHMS:
        _add_error(errors, "algorithm.type", f"unsupported algorithm {algorithm_type!r}; known={sorted(KNOWN_ALGORITHMS)}")

    mixer = effective.get("mixer", "online_offline")
    if mixer != "online_offline":
        _add_error(errors, "mixer", "only 'online_offline' is supported by the built-in RL pipeline")

    ratio = effective.get("online_ratio", 0.5)
    if not _is_number(ratio) or not 0.0 <= ratio <= 1.0:
        _add_error(errors, "online_ratio", f"must be a number in [0, 1], got {ratio!r}")

    batch_size = effective.get("batch_size")
    if batch_size is not None and (not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size <= 0):
        _add_error(errors, "batch_size", f"must be a positive integer, got {batch_size!r}")

    policy = effective.get("policy", {})
    if policy is not None and not isinstance(policy, dict):
        _add_error(errors, "policy", "must be an object when supplied")
        policy = {}
    env = effective.get("env", {})
    if env is not None and not isinstance(env, dict):
        _add_error(errors, "env", "must be an object when supplied")
        env = {}
    reward = effective.get("reward_model")
    if reward is not None:
        if not isinstance(reward, dict):
            _add_error(errors, "reward_model", "must be an object when supplied")
        else:
            reward_type = reward.get("type")
            if reward_type is not None and reward_type not in KNOWN_REWARD_TYPES:
                warnings.append(
                    f"reward_model.type={reward_type!r} is not one of the four built-in types; a plugin may provide it"
                )

    if isinstance(env, dict):
        if "type" not in env:
            warnings.append("env.type is not set; static RL checks cannot select a simulator")
        _check_positive_number(env, "fps", errors)
        _check_positive_number(env, "episode_length", errors)
        n_envs = env.get("n_envs")
        if n_envs is not None and (not isinstance(n_envs, int) or isinstance(n_envs, bool) or n_envs < 1):
            _add_error(errors, "env.n_envs", f"must be a positive integer, got {n_envs!r}")

    if isinstance(policy, dict):
        _check_positive_number(policy, "online_steps", errors, allow_zero=True)
        _check_positive_number(policy, "online_step_before_learning", errors, allow_zero=True)
        actor_cfg = policy.get("actor_learner_config", {})
        if actor_cfg is not None and not isinstance(actor_cfg, dict):
            _add_error(errors, "policy.actor_learner_config", "must be an object")
        elif isinstance(actor_cfg, dict):
            port = actor_cfg.get("learner_port")
            if port is not None and (not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535):
                _add_error(errors, "policy.actor_learner_config.learner_port", "must be an integer in 1..65535")
            _check_nested_number(actor_cfg, "policy.actor_learner_config", "policy_parameters_push_frequency", errors)
            _check_nested_number(actor_cfg, "policy.actor_learner_config", "queue_get_timeout", errors)

    for key in (
        "actor_lr",
        "critic_lr",
        "temperature_lr",
        "temperature_init",
        "critic_target_update_weight",
        "grad_clip_norm",
    ):
        _check_nested_number(algorithm, "algorithm", key, errors)
    for key in ("num_critics", "utd_ratio", "policy_update_freq"):
        value = algorithm.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            _add_error(errors, f"algorithm.{key}", f"must be a positive integer, got {value!r}")
    discount = algorithm.get("discount")
    if discount is not None and (not _is_number(discount) or not 0.0 <= discount <= 1.0):
        _add_error(errors, "algorithm.discount", f"must be a number in [0, 1], got {discount!r}")
    target_entropy = algorithm.get("target_entropy")
    if target_entropy is not None and not _is_number(target_entropy):
        _add_error(errors, "algorithm.target_entropy", "must be numeric or null")
    if "use_torch_compile" in algorithm and not isinstance(algorithm["use_torch_compile"], bool):
        _add_error(errors, "algorithm.use_torch_compile", "must be boolean")

    if algorithm.get("policy_config") is None and isinstance(algorithm_value, dict):
        warnings.append("algorithm.policy_config is unset; TrainRLServerPipelineConfig.validate normally fills it from policy")
    device_value = policy.get("device", effective.get("device")) if isinstance(policy, dict) else effective.get("device")
    if isinstance(device_value, str) and (device_value == "cuda" or device_value.startswith("cuda:")):
        warnings.append("GPU policy device requested; this check does not verify CUDA, renderer, or VRAM readiness")
    if effective.get("online_steps") is not None or (isinstance(policy, dict) and "online_steps" in policy):
        warnings.append("online RL requested; this check does not start an actor, learner, environment, or gRPC service")

    return {
        "check": "rl-config-static",
        "safety": {
            "starts_training": False,
            "starts_actor_or_learner": False,
            "constructs_environment": False,
            "loads_policy_or_reward_weights": False,
            "uses_network_or_credentials": False,
        },
        "status": "ok" if not errors else "invalid",
        "effective": {
            "algorithm_type": algorithm_type,
            "mixer": mixer,
            "online_ratio": ratio,
            "batch_size": batch_size,
            "env_type": env.get("type") if isinstance(env, dict) else None,
            "reward_type": reward.get("type") if isinstance(reward, dict) else None,
        },
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate common LeRobot RL/SAC/HIL-SERL JSON fields without training or starting services."
    )
    parser.add_argument("--config", type=Path, required=True, help="Path to a JSON RL configuration file.")
    parser.add_argument("--algorithm", help="Optional static override for algorithm type.")
    parser.add_argument("--online-ratio", type=float, help="Optional static override in [0, 1].")
    parser.add_argument("--batch-size", type=int, help="Optional positive batch-size override.")
    parser.add_argument("--device", help="Optional device label; only reported, never initialized.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with args.config.open(encoding="utf-8") as handle:
            config = json.load(handle)
        if not isinstance(config, dict):
            raise ValueError("top-level JSON value must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"check": "rl-config-static", "status": "invalid-input", "error": str(exc)}, indent=2))
        return 2

    overrides = {
        "algorithm": args.algorithm,
        "online_ratio": args.online_ratio,
        "batch_size": args.batch_size,
        "device": args.device,
    }
    result = validate_config(config, overrides)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
