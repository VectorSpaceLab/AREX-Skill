#!/usr/bin/env python3
"""Bounded dependency, artifact, and config checks for MyoSuite training plans.

This checker intentionally never installs, downloads, deserializes, trains,
starts Hydra/Submitit, contacts a logging service, or writes a file.  It is a
preflight/reporting helper, not a launcher.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import math
import os
import pathlib
import sys
import zipfile
from typing import Any


BASE = [
    ("MyoSuite", "myosuite", "MyoSuite"),
    ("MuJoCo", "mujoco", "mujoco"),
    ("Gymnasium", "gymnasium", "gymnasium"),
]
FRAMEWORKS = {
    "base": [],
    "sb3": [("Stable-Baselines3", "stable_baselines3", "stable-baselines3"), ("PyTorch", "torch", "torch")],
    "mjrl": [("MJRL", "mjrl", "mjrl"), ("PyTorch", "torch", "torch")],
    "torchrl": [("TorchRL", "torchrl", "torchrl"), ("TensorDict", "tensordict", "tensordict"), ("PyTorch", "torch", "torch")],
    "deprl": [("DEP-RL", "deprl", "deprl"), ("PyTorch", "torch", "torch")],
    "mjx": [("JAX", "jax", "jax"), ("MJX", "mjx", "mujoco-mjx")],
}
LAUNCHERS = {
    "hydra-local": [
        ("Hydra", "hydra", "hydra-core"),
        ("OmegaConf", "omegaconf", "omegaconf"),
        ("Submitit", "submitit", "submitit"),
        ("Hydra Submitit plugin", "hydra_plugins.hydra_submitit_launcher", "hydra-submitit-launcher"),
    ],
    "hydra-slurm": [
        ("Hydra", "hydra", "hydra-core"),
        ("OmegaConf", "omegaconf", "omegaconf"),
        ("Submitit", "submitit", "submitit"),
        ("Hydra Submitit plugin", "hydra_plugins.hydra_submitit_launcher", "hydra-submitit-launcher"),
    ],
}
LOGGING = {
    "tensorboard": [("TensorBoard", "tensorboard", "tensorboard")],
    "wandb": [("Weights & Biases", "wandb", "wandb")],
}


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def version_for(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def check_requirements(requirements: list[tuple[str, str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for label, module, distribution in requirements:
        if (module, distribution) in seen:
            continue
        seen.add((module, distribution))
        available = module_available(module)
        version = version_for(distribution)
        row = {"name": label, "module": module, "distribution": distribution, "available": available, "version": version}
        rows.append(row)
        if not available:
            errors.append(f"missing {label}: import {module!r} / distribution {distribution!r}")
    return rows, errors


def load_mapping(path: pathlib.Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"cannot read config {path}: {exc}"
    try:
        if path.suffix.lower() == ".json":
            value = json.loads(text)
        else:
            try:
                import yaml  # type: ignore

                value = yaml.safe_load(text)
            except ImportError:
                try:
                    from omegaconf import OmegaConf  # type: ignore

                    value = OmegaConf.to_container(OmegaConf.create(text), resolve=False)
                except Exception as exc:  # pragma: no cover - depends on optional parser
                    return None, f"YAML config needs PyYAML or OmegaConf: {exc}"
    except Exception as exc:
        return None, f"cannot parse config {path}: {exc}"
    if not isinstance(value, dict):
        return None, "config root must be a mapping"
    return value, None


def lookup(mapping: dict[str, Any], dotted: str) -> Any:
    value: Any = mapping
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def positive_int(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) > 0 and float(value) == int(value)
    except (TypeError, ValueError):
        return False


def nonnegative_int(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) >= 0 and float(value) == int(value)
    except (TypeError, ValueError):
        return False


def validate_config(data: dict[str, Any], framework: str, max_steps: int) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, Any] = {}

    def required(key: str) -> Any:
        value = lookup(data, key)
        if value is None:
            errors.append(f"config missing required field {key!r}")
        return value

    def require_positive(key: str) -> Any:
        value = required(key)
        if value is not None and not positive_int(value):
            errors.append(f"config field {key!r} must be a positive integer")
        return value

    if framework == "sb3":
        env = required("env")
        algorithm = required("algorithm")
        required("policy")
        seed = required("seed")
        if seed is not None and not nonnegative_int(seed):
            errors.append("config field 'seed' must be a non-negative integer")
        n_env = require_positive("n_env")
        require_positive("n_eval_env")
        learning_rate = required("learning_rate")
        if learning_rate is not None and (not finite_number(learning_rate) or float(learning_rate) <= 0):
            errors.append("config field 'learning_rate' must be positive finite numeric data")
        batch_size = require_positive("batch_size")
        gamma = required("gamma")
        if gamma is not None and (not finite_number(gamma) or float(gamma) <= 0):
            errors.append("config field 'gamma' must be positive finite numeric data")
        total = require_positive("total_timesteps")
        if algorithm not in ("PPO", "SAC"):
            errors.append("SB3 algorithm must be PPO or SAC")
        facts.update({"env": env, "algorithm": algorithm, "seed": seed, "total_timesteps": total, "n_env": n_env})
        if isinstance(total, (int, float)) and int(total) > max_steps:
            warnings.append(f"total_timesteps={total} exceeds bounded checker budget {max_steps}")
        if isinstance(n_env, (int, float)) and int(n_env) > 8:
            warnings.append(f"n_env={n_env} exceeds the conservative worker guardrail 8")
    elif framework == "mjrl":
        for key in ("env", "algorithm", "sample_mode", "job_name"):
            required(key)
        seed = required("seed")
        if seed is not None and not nonnegative_int(seed):
            errors.append("config field 'seed' must be a non-negative integer")
        for key in ("num_cpu", "rl_num_iter", "save_freq", "eval_rollouts"):
            require_positive(key)
        mode = lookup(data, "sample_mode")
        if mode not in ("samples", "trajectories"):
            errors.append("MJRL sample_mode must be samples or trajectories")
        require_positive("rl_num_samples" if mode == "samples" else "rl_num_traj")
        iterations = lookup(data, "rl_num_iter")
        facts.update({"env": lookup(data, "env"), "algorithm": lookup(data, "algorithm"), "seed": seed, "rl_num_iter": iterations, "sample_mode": mode})
        if isinstance(iterations, (int, float)) and int(iterations) > max(1, max_steps // 1000):
            warnings.append(f"rl_num_iter={iterations} is above the bounded planning guardrail")
        workers = lookup(data, "num_cpu")
        if isinstance(workers, (int, float)) and int(workers) > 2:
            warnings.append(f"num_cpu={workers} requires explicit resource approval")
    elif framework == "torchrl":
        for key in ("env.env_name", "collector.frames_per_batch", "collector.total_frames", "optim.lr", "loss.gamma", "loss.mini_batch_size", "loss.ppo_epochs"):
            required(key)
        frames = lookup(data, "collector.total_frames")
        require_positive("collector.frames_per_batch")
        require_positive("collector.total_frames")
        facts.update({"env": lookup(data, "env.env_name"), "total_frames": frames})
        if isinstance(frames, (int, float)) and int(frames) > max_steps:
            warnings.append(f"collector.total_frames={frames} exceeds bounded checker budget {max_steps}")
    elif framework == "deprl":
        tonic = data.get("tonic")
        if not isinstance(tonic, dict):
            errors.append("DEP-RL config needs a tonic mapping")
        else:
            for key in ("environment", "trainer", "parallel", "sequential", "seed"):
                if key not in tonic:
                    errors.append(f"DEP-RL config missing tonic.{key!s}")
            parallel, sequential = tonic.get("parallel"), tonic.get("sequential")
            facts.update({"parallel": parallel, "sequential": sequential})
            if positive_int(parallel) and positive_int(sequential):
                workers = int(parallel) * int(sequential)
                facts["worker_product"] = workers
                if workers > 4:
                    warnings.append(f"parallel*sequential={workers} exceeds bounded worker guardrail 4")
            trainer = str(tonic.get("trainer", ""))
            if "steps=" in trainer:
                warnings.append("DEP-RL trainer contains an executable step expression; validate its bound manually")
    elif framework == "mjx":
        env = required("env")
        facts["env"] = env
        warnings.append("MJX config validation is structural; JAX backend execution is not performed")
    else:  # base: a config may be useful, but no framework schema is assumed.
        warnings.append("base framework does not impose a learner config schema")

    return errors, warnings, facts


def check_policy(path_text: str, framework: str) -> tuple[dict[str, Any], list[str], list[str]]:
    path = pathlib.Path(path_text)
    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {"path": path_text, "exists": path.exists(), "deserialized": False}
    if not path.exists():
        errors.append(f"policy artifact does not exist: {path_text}")
        return result, errors, warnings
    if path.is_dir():
        names = {child.name for child in path.iterdir()}
        result.update({"kind": "directory", "entries": sorted(names & {"checkpoints", "config.yaml", "config.json"})})
        if framework == "deprl" and not ({"checkpoints", "config.yaml"} <= names):
            errors.append("DEP-RL policy directory should contain checkpoints/ and config.yaml")
        warnings.append("directory contents checked only; no external policy loader was invoked")
        return result, errors, warnings
    try:
        size = path.stat().st_size
    except OSError as exc:
        errors.append(f"cannot stat policy artifact: {exc}")
        return result, errors, warnings
    result["size_bytes"] = size
    if size == 0:
        errors.append("policy artifact is empty")
        return result, errors, warnings
    suffix = path.suffix.lower()
    result["kind"] = suffix.lstrip(".") or "unknown-file"
    if suffix == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                result["archive_members"] = len(archive.namelist())
                if bad:
                    errors.append(f"policy zip is corrupt near member {bad!r}")
        except (OSError, zipfile.BadZipFile) as exc:
            errors.append(f"policy zip is unreadable: {exc}")
        if framework != "sb3":
            warnings.append("zip artifact is normally SB3-shaped; use the matching framework loader")
    elif suffix in (".pickle", ".pkl"):
        warnings.append("pickle is executable during load; structural check only and trusted provenance is required")
    elif suffix in (".pt", ".pth", ".ckpt"):
        warnings.append("torch checkpoint was not deserialized; loader, architecture, and companion config remain to be checked")
    else:
        warnings.append("unknown policy suffix; structural existence check only")
    return result, errors, warnings


def shape_summary(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): shape_summary(item) for key, item in value.items()}
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            return list(shape)
        except TypeError:
            return str(shape)
    return type(value).__name__


def probe_environment(env_id: str, seed: int | None) -> tuple[dict[str, Any], str | None]:
    try:
        from myosuite.utils import gym  # type: ignore

        env = gym.make(env_id)
    except Exception as exc:
        return {}, f"environment probe could not create {env_id!r}: {type(exc).__name__}: {exc}"
    try:
        try:
            reset_value = env.reset(seed=seed)
        except TypeError:
            reset_value = env.reset()
        obs = reset_value[0] if isinstance(reset_value, tuple) else reset_value
        return {
            "env_id": env_id,
            "observation": shape_summary(obs),
            "observation_space": shape_summary(env.observation_space),
            "action_space": shape_summary(env.action_space),
            "stepped": False,
        }, None
    except Exception as exc:
        return {}, f"environment probe reset failed: {type(exc).__name__}: {exc}"
    finally:
        try:
            env.close()
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check optional MyoSuite training dependencies and artifacts without launching work.")
    parser.add_argument("--framework", choices=sorted(FRAMEWORKS), default="base")
    parser.add_argument("--launcher", choices=("none", *sorted(LAUNCHERS)), default="none")
    parser.add_argument("--logging", choices=("none", *sorted(LOGGING)), default="none")
    parser.add_argument("--config", type=pathlib.Path, help="local JSON/YAML config; never composed or executed")
    parser.add_argument("--policy", metavar="PATH", help="local policy/checkpoint; checked without deserialization")
    parser.add_argument("--env", metavar="ENV_ID", help="environment id for --probe-env")
    parser.add_argument("--probe-env", action="store_true", help="create/reset/close one environment; never steps")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--max-steps", type=int, default=10000, help="bounded planning guardrail; does not launch training")
    parser.add_argument("--json", action="store_true", help="emit one JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_steps <= 0:
        print("--max-steps must be positive", file=sys.stderr)
        return 2
    if args.probe_env and not args.env:
        print("--probe-env requires --env ENV_ID", file=sys.stderr)
        return 2

    requirements = BASE + FRAMEWORKS[args.framework]
    if args.launcher != "none":
        requirements += LAUNCHERS[args.launcher]
    if args.logging != "none":
        requirements += LOGGING[args.logging]
    dependency_rows, errors = check_requirements(requirements)
    warnings: list[str] = []
    result: dict[str, Any] = {
        "framework": args.framework,
        "launcher": args.launcher,
        "logging": args.logging,
        "dependencies": dependency_rows,
        "config": None,
        "policy": None,
        "environment_probe": None,
        "launch_performed": False,
        "training_started": False,
        "writes_performed": False,
        "errors": errors,
        "warnings": warnings,
        "bounded_for_agent_session": True,
    }

    if args.config:
        if not args.config.is_file():
            errors.append(f"config file does not exist: {args.config}")
        else:
            data, config_error = load_mapping(args.config)
            if config_error:
                errors.append(config_error)
            else:
                config_errors, config_warnings, facts = validate_config(data or {}, args.framework, args.max_steps)
                errors.extend(config_errors)
                warnings.extend(config_warnings)
                result["config"] = {"path": str(args.config), "parsed": True, "facts": facts}
                if config_warnings:
                    result["bounded_for_agent_session"] = False

    if args.policy:
        policy, policy_errors, policy_warnings = check_policy(args.policy, args.framework)
        result["policy"] = policy
        errors.extend(policy_errors)
        warnings.extend(policy_warnings)

    if args.probe_env:
        probe, probe_error = probe_environment(args.env, args.seed)
        if probe_error:
            errors.append(probe_error)
        else:
            result["environment_probe"] = probe

    result["errors"] = errors
    result["warnings"] = warnings
    result["ok"] = not errors
    if not args.json:
        print(f"framework={args.framework} launcher={args.launcher} logging={args.logging}")
        print(f"ok={result['ok']} bounded_for_agent_session={result['bounded_for_agent_session']}")
        for row in dependency_rows:
            status = "available" if row["available"] else "MISSING"
            suffix = f" ({row['version']})" if row["version"] else ""
            print(f"  {status}: {row['name']}{suffix}")
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in warnings:
            print(f"WARNING: {message}")
        print("No launch, training, download, deserialization, or file write was performed.")
    else:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))

    if errors:
        return 1
    if not result["bounded_for_agent_session"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
