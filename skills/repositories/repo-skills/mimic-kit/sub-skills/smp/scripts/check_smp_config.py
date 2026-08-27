#!/usr/bin/env python3
"""Validate MimicKit SMP prior/policy config compatibility without simulators.

The checker reads YAML files from an explicit MimicKit checkout and reports
layout mismatches that ``SMPAgent`` would assert on at runtime. It does not
import Isaac Gym, Isaac Lab, Newton, or Warp.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Missing dependency PyYAML: {exc}")

EXTERNAL_ASSET_PREFIXES = (
    "data/motions/",
    "data/models/",
    "data/logs/",
    "data/assets/objects/",
    "output/",
)

TASK_OBJECT_ASSETS = {
    "task_location": ["data/assets/objects/location_marker.xml"],
    "task_steering": ["data/assets/objects/steering_marker.xml"],
    "task_dodgeball": ["data/assets/objects/dodgeball.xml"],
}

SMP_REQUIRED_AGENT_KEYS = [
    "smp_eval_batch_size",
    "sds_loss_scale",
    "diffusion_steps",
    "task_reward_weight",
    "smp_reward_weight",
    "smp_prior_cfg",
    "smp_prior_model",
]

PRIOR_ENV_KEYS = [
    ("global_obs", False),
    ("root_height_obs", True),
    ("enable_tar_obs", False),
    ("num_disc_obs_steps", None),
    ("disc_dof_vel_obs", False),
]

SMP_ENV_NAMES = {"smp", "task_location", "task_steering", "task_dodgeball"}


def resolve(repo_root: Path, raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def rel(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"YAML did not contain a mapping: {path}")
    return data


def is_external(repo_root: Path, path: Path) -> bool:
    name = rel(repo_root, path)
    return any(name.startswith(prefix) for prefix in EXTERNAL_ASSET_PREFIXES)


def add_path_check(repo_root: Path, raw: str, label: str, warnings: list[str], errors: list[str], strict_assets: bool) -> Path:
    path = resolve(repo_root, raw)
    if not path.exists():
        msg = f"{label} does not exist: {rel(repo_root, path)}"
        if strict_assets or not is_external(repo_root, path):
            errors.append(msg)
        else:
            warnings.append(msg)
    return path


def compare_env_value(key: str, prior_env: dict[str, Any], policy_env: dict[str, Any], default: Any, errors: list[str]) -> None:
    prior_val = prior_env.get(key, default)
    policy_val = policy_env.get(key, default)
    if prior_val != policy_val:
        errors.append(f"prior/policy env mismatch for {key}: prior={prior_val!r}, policy={policy_val!r}")


def validate(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not repo_root.is_dir():
        return {"ok": False, "errors": [f"repo root is not a directory: {repo_root}"], "warnings": []}, 1

    agent_path = resolve(repo_root, args.agent_config)
    env_path = resolve(repo_root, args.env_config)
    engine_path = resolve(repo_root, args.engine_config)

    for label, path in (("agent_config", agent_path), ("env_config", env_path), ("engine_config", engine_path)):
        if not path.is_file():
            errors.append(f"{label} does not exist: {rel(repo_root, path)}")

    agent: dict[str, Any] = {}
    env: dict[str, Any] = {}
    engine: dict[str, Any] = {}
    if not errors:
        try:
            agent = load_yaml(agent_path)
            env = load_yaml(env_path)
            engine = load_yaml(engine_path)
        except Exception as exc:
            errors.append(f"failed to load YAML: {type(exc).__name__}: {exc}")

    if agent:
        if agent.get("agent_name") != "SMP":
            errors.append(f"agent_name must be 'SMP' for this checker, got {agent.get('agent_name')!r}")
        for key in SMP_REQUIRED_AGENT_KEYS:
            if key not in agent:
                errors.append(f"SMP agent config missing key: {key}")

    if env:
        env_name = env.get("env_name")
        if env_name not in SMP_ENV_NAMES:
            errors.append(f"env_name is not an SMP-compatible env for this checker: {env_name!r}")
        if env.get("char_file"):
            add_path_check(repo_root, str(env["char_file"]), "character asset", warnings, errors, args.strict_assets)
        for asset_rel in TASK_OBJECT_ASSETS.get(str(env_name), []):
            add_path_check(repo_root, asset_rel, f"task object asset for {env_name}", warnings, errors, args.strict_assets)

    prior_cfg_path = None
    prior_cfg: dict[str, Any] = {}
    prior_env: dict[str, Any] = {}
    if agent.get("smp_prior_cfg"):
        prior_cfg_path = add_path_check(repo_root, str(agent["smp_prior_cfg"]), "smp_prior_cfg", warnings, errors, True)
        if prior_cfg_path.is_file():
            try:
                prior_cfg = load_yaml(prior_cfg_path)
            except Exception as exc:
                errors.append(f"failed to load smp_prior_cfg: {type(exc).__name__}: {exc}")
    if agent.get("smp_prior_model"):
        add_path_check(repo_root, str(agent["smp_prior_model"]), "smp_prior_model", warnings, errors, args.strict_assets)

    if prior_cfg.get("env_config"):
        prior_env_path = add_path_check(repo_root, str(prior_cfg["env_config"]), "prior env_config", warnings, errors, True)
        if prior_env_path.is_file():
            try:
                prior_env = load_yaml(prior_env_path)
            except Exception as exc:
                errors.append(f"failed to load prior env_config: {type(exc).__name__}: {exc}")

    if prior_env and env:
        for key, default in PRIOR_ENV_KEYS:
            compare_env_value(key, prior_env, env, default, errors)
        prior_key_bodies = prior_env.get("key_bodies", [])
        env_key_bodies = env.get("key_bodies", [])
        if len(prior_key_bodies) != len(env_key_bodies):
            errors.append(f"key_bodies length mismatch: prior={len(prior_key_bodies)}, policy={len(env_key_bodies)}")

    if prior_cfg and engine:
        prior_control_freq = prior_cfg.get("control_freq")
        engine_control_freq = engine.get("control_freq")
        if prior_control_freq != engine_control_freq:
            errors.append(f"control_freq mismatch: prior={prior_control_freq!r}, engine={engine_control_freq!r}")

    if agent.get("enable_gsi", False):
        if env.get("env_name") not in SMP_ENV_NAMES:
            errors.append("enable_gsi requires an SMP env with init_gsi_buffer support")
        if env.get("enable_tar_obs", False):
            errors.append("enable_gsi requires env enable_tar_obs: False")
        if env.get("pose_termination", False):
            errors.append("enable_gsi requires env pose_termination: False")
        gsi_buffer_size = int(agent.get("gsi_buffer_size", 4096))
        gsi_regen = int(agent.get("gsi_regen_num_motions", 1024))
        gsi_batch = int(agent.get("gsi_batch_size", 256))
        if not (gsi_buffer_size >= gsi_regen >= gsi_batch > 0):
            errors.append(
                "GSI sizes must satisfy gsi_buffer_size >= gsi_regen_num_motions >= gsi_batch_size > 0"
            )

    summary = {
        "ok": not errors,
        "repo_root": str(repo_root),
        "agent_config": rel(repo_root, agent_path),
        "env_config": rel(repo_root, env_path),
        "engine_config": rel(repo_root, engine_path),
        "smp_prior_cfg": rel(repo_root, prior_cfg_path) if prior_cfg_path else None,
        "env_name": env.get("env_name"),
        "agent_name": agent.get("agent_name"),
        "engine_name": engine.get("engine_name"),
        "control_freq": engine.get("control_freq"),
        "enable_gsi": bool(agent.get("enable_gsi", False)),
        "warnings": warnings,
        "errors": errors,
    }
    return summary, 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate SMP prior/policy config compatibility without simulator imports.")
    parser.add_argument("--repo-root", required=True, help="Target MimicKit checkout root")
    parser.add_argument("--agent-config", required=True, help="SMP agent config, relative to repo root unless absolute")
    parser.add_argument("--env-config", required=True, help="SMP env config, relative to repo root unless absolute")
    parser.add_argument("--engine-config", required=True, help="Engine config, relative to repo root unless absolute")
    parser.add_argument("--strict-assets", action="store_true", help="Treat missing downloaded models/motions/object assets as errors")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary, code = validate(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("MimicKit SMP config check")
        print(f"status: {'OK' if summary.get('ok') else 'FAIL'}")
        print(f"agent_config: {summary.get('agent_config')}")
        print(f"env_config: {summary.get('env_config')}")
        print(f"engine_config: {summary.get('engine_config')}")
        print(f"smp_prior_cfg: {summary.get('smp_prior_cfg')}")
        print(f"env_name: {summary.get('env_name')}  agent_name: {summary.get('agent_name')}  engine_name: {summary.get('engine_name')}")
        for item in summary.get("warnings", []):
            print(f"warning: {item}")
        for item in summary.get("errors", []):
            print(f"error: {item}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
