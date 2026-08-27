#!/usr/bin/env python3
"""Render and validate RoboTwin policy-eval configs without launching them.

This helper is synthetic: it does not import XPolicyLab and never starts a
policy or simulator process. It only validates the YAML config and prints the
resolved schedule or server plan.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency error path
    raise SystemExit("PyYAML is required to render RoboTwin eval configs.") from exc


ROBOT_INFO_FALLBACK: dict[str, dict[str, list[int]]] = {
    "franka": {"arm_dim": [7], "ee_dim": [1]},
    "piper": {"arm_dim": [6], "ee_dim": [1]},
    "x5": {"arm_dim": [6], "ee_dim": [1]},
    "aloha_agilex": {"arm_dim": [6, 6], "ee_dim": [1, 1]},
    "dual_x5": {"arm_dim": [6, 6], "ee_dim": [1, 1]},
    "dual_franka": {"arm_dim": [7, 7], "ee_dim": [1, 1]},
}

ENV_TO_ROBOT_FALLBACK = {
    "arx_x5": "dual_x5",
    "aloha_agilex": "aloha_agilex",
    "franka": "dual_franka",
}

PLACEHOLDER_RE = re.compile(r"<[^<>]+>")


class ConfigError(ValueError):
    pass



def is_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple))



def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Could not read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse {path}: {exc}") from exc



def parse_gpu_ids(raw_gpus: Any) -> list[int]:
    if isinstance(raw_gpus, list):
        entries = raw_gpus
    elif isinstance(raw_gpus, str):
        entries: list[int] = []
        for token in raw_gpus.split(","):
            token = token.strip()
            if re.fullmatch(r"\d+", token):
                entries.append(int(token))
                continue
            range_match = re.fullmatch(r"(\d+)-(\d+)", token)
            if range_match is None:
                raise ConfigError(
                    "gpu_ids must use a list, comma-separated IDs, or inclusive ranges such as '0-4'."
                )
            start, end = (int(value) for value in range_match.groups())
            if start > end:
                raise ConfigError(f"GPU range must be ascending: {token!r}")
            entries.extend(range(start, end + 1))
    else:
        raise ConfigError("gpu_ids must be a list or string.")

    if not entries:
        raise ConfigError("gpu_ids cannot be empty.")
    if any(isinstance(gpu_id, bool) or not isinstance(gpu_id, int) or gpu_id < 0 for gpu_id in entries):
        raise ConfigError("gpu_ids must contain non-negative integers.")
    if len(set(entries)) != len(entries):
        raise ConfigError("gpu_ids contains a duplicate GPU.")
    return entries



def config_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]



def build_policy_endpoints(raw_ips: Any, raw_ports: Any) -> list[dict[str, Any]]:
    ips = config_list(raw_ips)
    ports = config_list(raw_ports)
    if not ips or not ports:
        raise ConfigError("Remote evaluation requires policy_server_ip and policy_server_port.")

    normalized_ips: list[str] = []
    for raw_ip in ips:
        if not isinstance(raw_ip, str):
            raise ConfigError("policy_server_ip must be a hostname string or a list of strings.")
        policy_server_ip = raw_ip.strip()
        if not policy_server_ip or policy_server_ip in {"0.0.0.0", "::"}:
            raise ConfigError(
                "policy_server_ip must be a connectable address, not a server bind address."
            )
        normalized_ips.append(policy_server_ip)

    normalized_ports: list[int] = []
    for raw_port in ports:
        if isinstance(raw_port, bool):
            raise ConfigError("policy_server_port must contain integer ports.")
        try:
            policy_server_port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise ConfigError("policy_server_port must contain integer ports.") from exc
        if not 1 <= policy_server_port <= 65535:
            raise ConfigError("policy_server_port values must be between 1 and 65535.")
        normalized_ports.append(policy_server_port)

    endpoint_count = max(len(normalized_ips), len(normalized_ports))
    if len(normalized_ips) not in {1, endpoint_count}:
        raise ConfigError("policy_server_ip must contain one value or match policy_server_port length.")
    if len(normalized_ports) not in {1, endpoint_count}:
        raise ConfigError("policy_server_port must contain one value or match policy_server_ip length.")

    endpoints = []
    for index in range(endpoint_count):
        host = normalized_ips[0] if len(normalized_ips) == 1 else normalized_ips[index]
        port = normalized_ports[0] if len(normalized_ports) == 1 else normalized_ports[index]
        endpoints.append({"host": host, "port": port, "address": f"{host}:{port}"})

    addresses = [endpoint["address"] for endpoint in endpoints]
    if len(set(addresses)) != len(addresses):
        raise ConfigError("policy_server_ip and policy_server_port contain a duplicate endpoint.")
    return endpoints



def detect_placeholders(data: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(data, Mapping):
        for key, value in data.items():
            nested_prefix = f"{prefix}.{key}" if prefix else str(key)
            hits.extend(detect_placeholders(value, prefix=nested_prefix))
        return hits
    if isinstance(data, list):
        for index, value in enumerate(data):
            nested_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            hits.extend(detect_placeholders(value, prefix=nested_prefix))
        return hits
    if isinstance(data, str) and PLACEHOLDER_RE.fullmatch(data.strip()):
        hits.append(prefix or data.strip())
    return hits



def robot_layout(repo_root: Path, env_cfg_type: str) -> dict[str, Any]:
    env_cfg_path = repo_root / "env_cfg" / f"{env_cfg_type}.yml"
    robot_info_path = repo_root / "env_cfg" / "robot" / "_robot_info.json"

    robot_name: str | None = None
    if env_cfg_path.is_file():
        env_cfg = load_yaml(env_cfg_path) or {}
        if not isinstance(env_cfg, Mapping):
            raise ConfigError(f"{env_cfg_path} must contain a mapping root.")
        try:
            robot_name = str(env_cfg["config"]["robot"])
        except Exception as exc:
            raise ConfigError(f"Could not resolve config.robot from {env_cfg_path}.") from exc
    else:
        robot_name = ENV_TO_ROBOT_FALLBACK.get(env_cfg_type)
        if robot_name is None:
            raise ConfigError(
                f"Could not find env_cfg/{env_cfg_type}.yml and no fallback profile exists."
            )

    if robot_info_path.is_file():
        robot_info = load_yaml(robot_info_path)
        if not isinstance(robot_info, Mapping):
            raise ConfigError(f"{robot_info_path} must contain a mapping root.")
    else:
        robot_info = ROBOT_INFO_FALLBACK

    raw_layout = robot_info.get(robot_name) or ROBOT_INFO_FALLBACK.get(robot_name)
    if raw_layout is None:
        raise ConfigError(f"Unknown robot profile {robot_name!r} for {env_cfg_type!r}.")
    if not isinstance(raw_layout, Mapping):
        raise ConfigError(f"Robot profile {robot_name!r} must map to a layout mapping.")

    try:
        arm_dim = tuple(int(value) for value in raw_layout["arm_dim"])
        ee_dim = tuple(int(value) for value in raw_layout["ee_dim"])
    except Exception as exc:
        raise ConfigError(f"Robot profile {robot_name!r} is missing arm_dim/ee_dim lists.") from exc

    if len(arm_dim) != 2 or len(ee_dim) != 2:
        raise ConfigError(
            f"Policy eval expects a dual-arm profile; got arm_dim={arm_dim!r}, ee_dim={ee_dim!r}."
        )

    return {
        "env_cfg_type": env_cfg_type,
        "robot_name": robot_name,
        "arm_dim": arm_dim,
        "ee_dim": ee_dim,
        "qpos_dim": arm_dim[0] + 1 + arm_dim[1] + 1,
        "ee_action_dim": 7 + 1 + 7 + 1,
    }



def normalize_action_type(value: str | None) -> str:
    if value is None:
        return "qpos"
    lowered = str(value).strip().lower()
    if lowered in {"joint", "qpos"}:
        return "qpos"
    if lowered in {"ee", "endpose"}:
        return "ee"
    raise ConfigError("action_type must be one of: joint, qpos, ee, endpose.")



def render_command(parts: list[str]) -> str:
    return shlex.join(parts)



def render_multitask_preview(
    *,
    config_path: Path,
    config: Mapping[str, Any],
    args: argparse.Namespace,
    layout: Mapping[str, Any],
) -> dict[str, Any]:
    tasks = config.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ConfigError("tasks must be a non-empty list.")
    seen_tasks: set[str] = set()
    normalized_tasks: list[str] = []
    for task in tasks:
        if not isinstance(task, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", task):
            raise ConfigError(f"Unsupported task name: {task!r}")
        if task in seen_tasks:
            raise ConfigError(f"Task {task!r} is configured more than once.")
        seen_tasks.add(task)
        normalized_tasks.append(task)

    gpu_ids = parse_gpu_ids(config.get("gpu_ids"))
    jobs_per_gpu = config.get("jobs_per_gpu", 1)
    if isinstance(jobs_per_gpu, bool) or not isinstance(jobs_per_gpu, int) or jobs_per_gpu <= 0:
        raise ConfigError("jobs_per_gpu must be a positive integer.")
    num_workers = config.get("num_workers", 1)
    if isinstance(num_workers, bool) or not isinstance(num_workers, int) or num_workers <= 0:
        raise ConfigError("num_workers must be a positive integer.")

    remote_enabled = config.get("enable_remote", False)
    if not isinstance(remote_enabled, bool):
        raise ConfigError("enable_remote must be true or false.")
    if args.enable_remote is not None:
        remote_enabled = args.enable_remote

    endpoints: list[dict[str, Any]] = []
    if remote_enabled:
        raw_ips = args.policy_server_ip if args.policy_server_ip is not None else config.get("policy_server_ip")
        raw_ports = args.policy_server_port if args.policy_server_port is not None else config.get("policy_server_port")
        endpoints = build_policy_endpoints(raw_ips, raw_ports)

    policy_name = args.policy_name
    ckpt_name = args.ckpt_name
    env_cfg_type = args.env_cfg_type
    policy_conda_env = args.policy_conda_env
    eval_env_conda_env = args.eval_env_conda_env
    action_type = normalize_action_type(args.action_type)

    launch_parts = [
        "bash",
        "scripts/eval_policy.sh",
        "multitask",
        "--config",
        str(config_path),
        "--policy-name",
        policy_name,
        "--ckpt-name",
        ckpt_name,
        "--env-cfg-type",
        env_cfg_type,
        "--action-type",
        action_type,
        "--policy-conda-env",
        policy_conda_env,
        "--eval-env-conda-env",
        eval_env_conda_env,
        "--task-config",
        args.task_config,
        "--seed",
        str(args.seed),
        "--test-num",
        str(args.test_num),
    ]
    if args.num_workers is not None:
        launch_parts.extend(["--num-workers", str(args.num_workers)])
    if args.max_seed_attempts is not None:
        launch_parts.extend(["--max-seed-attempts", str(args.max_seed_attempts)])
    if remote_enabled:
        launch_parts.append("--enable-remote")
        for endpoint in endpoints:
            launch_parts.extend(["--policy-server-ip", endpoint["host"], "--policy-server-port", str(endpoint["port"])])

    gpu_slots = [str(gpu_id) for _ in range(jobs_per_gpu) for gpu_id in gpu_ids]
    job_previews: list[dict[str, Any]] = []
    for index, task in enumerate(normalized_tasks):
        gpu_id = gpu_slots[index % len(gpu_slots)]
        endpoint = endpoints[index % len(endpoints)] if endpoints else None
        job_previews.append(
            {
                "job_index": index,
                "task": task,
                "gpu_id": gpu_id,
                "endpoint": endpoint["address"] if endpoint else None,
                "command": render_command(
                    [
                        "bash",
                        "scripts/eval_policy.sh",
                        "multitask",
                        "--config",
                        str(config_path),
                        "--policy-name",
                        policy_name,
                        "--ckpt-name",
                        ckpt_name,
                        "--env-cfg-type",
                        env_cfg_type,
                        "--action-type",
                        action_type,
                        "--policy-conda-env",
                        policy_conda_env,
                        "--eval-env-conda-env",
                        eval_env_conda_env,
                        "--task-config",
                        args.task_config,
                        "--seed",
                        str(args.seed),
                        "--test-num",
                        str(args.test_num),
                    ]
                    + (["--num-workers", str(args.num_workers)] if args.num_workers is not None else [])
                    + (["--max-seed-attempts", str(args.max_seed_attempts)] if args.max_seed_attempts is not None else [])
                    + (["--enable-remote"] if remote_enabled else [])
                    + (
                        [
                            item
                            for endpoint in endpoints
                            for item in ("--policy-server-ip", endpoint["host"], "--policy-server-port", str(endpoint["port"]))
                        ]
                        if remote_enabled
                        else []
                    ),
                ),
            }
        )

    return {
        "mode": "multitask",
        "config_path": str(config_path),
        "robot_name": layout["robot_name"],
        "action_profile": args.env_cfg_type,
        "expected_dims": {
            "qpos": layout["qpos_dim"],
            "ee": layout["ee_action_dim"],
        },
        "gpu_ids": gpu_ids,
        "jobs_per_gpu": jobs_per_gpu,
        "num_workers": num_workers,
        "remote_enabled": remote_enabled,
        "endpoints": endpoints,
        "tasks": normalized_tasks,
        "launch_command": render_command(launch_parts),
        "job_previews": job_previews,
    }



def render_server_preview(
    *,
    config_path: Path,
    config: Mapping[str, Any],
    args: argparse.Namespace,
    layout: Mapping[str, Any],
) -> dict[str, Any]:
    placeholders = detect_placeholders(config)
    allowed_fields = {
        "policy_name",
        "checkpoint",
        "env_cfg_type",
        "action_type",
        "policy_env",
        "gpu_ids",
        "instances_per_gpu",
        "base_port",
        "bind_host",
        "bench_name",
        "server_task_name",
        "seed",
        "startup_timeout",
        "output_dir",
    }
    unknown = sorted(set(config) - allowed_fields)
    if unknown:
        raise ConfigError("Unsupported server config fields: " + ", ".join(unknown))

    if placeholders:
        return {
            "mode": "serve",
            "template_mode": True,
            "config_path": str(config_path),
            "robot_name": layout["robot_name"],
            "action_profile": str(config.get("env_cfg_type", args.env_cfg_type)),
            "expected_dims": {
                "qpos": layout["qpos_dim"],
                "ee": layout["ee_action_dim"],
            },
            "launch_command": render_command(
                ["bash", "scripts/eval_policy.sh", "serve", "--config", str(config_path)]
            ),
            "raw_config": dict(config),
            "placeholders": placeholders,
            "note": "Fill the placeholders to derive instance and endpoint previews.",
        }

    policy_name = str(config["policy_name"]).strip()
    checkpoint = str(config["checkpoint"]).strip()
    env_cfg_type = str(config["env_cfg_type"]).strip()
    action_type = normalize_action_type(str(config.get("action_type", args.action_type)))
    policy_env = str(config.get("policy_env", args.policy_conda_env)).strip()
    bench_name = str(config.get("bench_name", "RoboTwin")).strip() or "RoboTwin"
    server_task_name = str(config.get("server_task_name", "remote_multitask")).strip() or "remote_multitask"
    gpu_ids = parse_gpu_ids(config.get("gpu_ids", []))
    instances_per_gpu = config.get("instances_per_gpu", 1)
    if isinstance(instances_per_gpu, bool) or not isinstance(instances_per_gpu, int) or instances_per_gpu <= 0:
        raise ConfigError("instances_per_gpu must be a positive integer.")
    base_port = config.get("base_port", 18080)
    if isinstance(base_port, bool) or not isinstance(base_port, int) or base_port <= 0:
        raise ConfigError("base_port must be a positive integer.")
    startup_timeout = config.get("startup_timeout", 1200)
    if isinstance(startup_timeout, bool) or not isinstance(startup_timeout, int) or startup_timeout <= 0:
        raise ConfigError("startup_timeout must be a positive integer.")

    server_count = len(gpu_ids) * instances_per_gpu
    if base_port + server_count - 1 > 65535:
        raise ConfigError("The generated server port range exceeds 65535.")

    instances: list[dict[str, Any]] = []
    for gpu_id in gpu_ids:
        for instance_index in range(instances_per_gpu):
            index = len(instances)
            port = base_port + index
            instances.append(
                {
                    "instance_index": index,
                    "gpu_id": gpu_id,
                    "port": port,
                    "instance_id": f"server_{index:03d}_gpu{gpu_id}_port{port}",
                    "command": render_command(
                        [
                            "bash",
                            "scripts/eval_policy.sh",
                            "serve",
                            "--config",
                            str(config_path),
                        ]
                    ),
                }
            )

    client_config = {
        "enable_remote": True,
        "policy_server_ip": "<REMOTE_SERVER_IP>",
        "policy_server_port": [instance["port"] for instance in instances],
    }

    return {
        "mode": "serve",
        "template_mode": False,
        "config_path": str(config_path),
        "robot_name": layout["robot_name"],
        "action_profile": env_cfg_type,
        "expected_dims": {
            "qpos": layout["qpos_dim"],
            "ee": layout["ee_action_dim"],
        },
        "policy_name": policy_name,
        "checkpoint": checkpoint,
        "policy_env": policy_env,
        "bench_name": bench_name,
        "server_task_name": server_task_name,
        "action_type": action_type,
        "gpu_ids": gpu_ids,
        "instances_per_gpu": instances_per_gpu,
        "base_port": base_port,
        "startup_timeout": startup_timeout,
        "instances": instances,
        "client_config": client_config,
        "launch_command": render_command(
            ["bash", "scripts/eval_policy.sh", "serve", "--config", str(config_path)]
        ),
    }



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render and validate RoboTwin policy-eval configs without launching them."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--policy-name", default="<policy_name>")
    parser.add_argument("--ckpt-name", default="<checkpoint>")
    parser.add_argument("--env-cfg-type", default="arx_x5")
    parser.add_argument("--policy-conda-env", default="<policy_env>")
    parser.add_argument("--eval-env-conda-env", default="<robotwin_env>")
    parser.add_argument("--task-config", default="demo_clean")
    parser.add_argument(
        "--action-type",
        default="joint",
        choices=("joint", "qpos", "ee", "endpose"),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--test-num", type=int, default=100)
    parser.add_argument("--num-workers", type=int)
    parser.add_argument("--max-seed-attempts", type=int)
    parser.add_argument(
        "--enable-remote",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override the config's remote mode when rendering a multitask schedule.",
    )
    parser.add_argument("--policy-server-ip", action="append")
    parser.add_argument("--policy-server-port", action="append", type=int)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    config_path = args.config.expanduser().resolve()
    if not config_path.is_file():
        raise ConfigError(f"Config file does not exist: {config_path}")

    config = load_yaml(config_path) or {}
    if not isinstance(config, Mapping):
        raise ConfigError("The config root must be a mapping.")

    placeholders = detect_placeholders(config)

    allowed_multitask = {
        "gpu_ids",
        "jobs_per_gpu",
        "num_workers",
        "tasks",
        "enable_remote",
        "policy_server_ip",
        "policy_server_port",
    }
    allowed_server = {
        "policy_name",
        "checkpoint",
        "env_cfg_type",
        "action_type",
        "policy_env",
        "gpu_ids",
        "instances_per_gpu",
        "base_port",
        "bind_host",
        "bench_name",
        "server_task_name",
        "seed",
        "startup_timeout",
        "output_dir",
    }

    layout = robot_layout(args.repo_root.expanduser().resolve(), args.env_cfg_type)
    if "tasks" in config:
        unknown = sorted(set(config) - allowed_multitask)
        if unknown:
            raise ConfigError(
                "The scheduler config only accepts gpu_ids, jobs_per_gpu, num_workers, tasks, enable_remote, policy_server_ip, and policy_server_port; unsupported fields: "
                + ", ".join(unknown)
            )
        summary = render_multitask_preview(
            config_path=config_path,
            config=config,
            args=args,
            layout=layout,
        )
    else:
        unknown = sorted(set(config) - allowed_server)
        if unknown:
            raise ConfigError("Unsupported server config fields: " + ", ".join(unknown))
        summary = render_server_preview(
            config_path=config_path,
            config=config,
            args=args,
            layout=layout,
        )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Mode: {summary['mode']}")
        print(f"Config: {summary['config_path']}")
        print(f"Robot profile: {summary['robot_name']} (env_cfg_type={summary['action_profile']})")
        print(
            "Expected flattened dims: "
            f"qpos={summary['expected_dims']['qpos']}, ee={summary['expected_dims']['ee']}"
        )
        if summary["mode"] == "multitask":
            print(f"Tasks: {len(summary['tasks'])}")
            print(f"GPUs: {summary['gpu_ids']}  jobs_per_gpu={summary['jobs_per_gpu']}  num_workers={summary['num_workers']}")
            print(f"Remote: {summary['remote_enabled']}")
            if summary["remote_enabled"]:
                print("Endpoints: " + ", ".join(endpoint["address"] for endpoint in summary["endpoints"]))
            print("Launch command:")
            print(f"  {summary['launch_command']}")
            print("Job preview:")
            for job in summary["job_previews"]:
                endpoint = f" server={job['endpoint']}" if job["endpoint"] else ""
                print(f"  [{job['job_index']:03d}] task={job['task']} gpu={job['gpu_id']}{endpoint}")
                print(f"    {job['command']}")
        elif summary.get("template_mode"):
            print("Template mode: unresolved placeholders are present.")
            print("Raw config:")
            print(yaml.safe_dump(summary["raw_config"], sort_keys=False).rstrip())
            print("Placeholders:")
            for hit in summary["placeholders"]:
                print(f"  - {hit}")
            print("Launch command:")
            print(f"  {summary['launch_command']}")
            print("Fill the placeholders to derive instance and endpoint previews.")
        else:
            print(f"Policy: {summary['policy_name']}  checkpoint={summary['checkpoint']}")
            print(f"Policy env: {summary['policy_env']}  bench={summary['bench_name']}  server_task={summary['server_task_name']}")
            print(f"GPUs: {summary['gpu_ids']}  instances_per_gpu={summary['instances_per_gpu']}  base_port={summary['base_port']}")
            print(f"Startup timeout: {summary['startup_timeout']}")
            print("Launch command:")
            print(f"  {summary['launch_command']}")
            print("Client config snippet:")
            print(yaml.safe_dump(summary["client_config"], sort_keys=False).rstrip())
            print("Server instances:")
            for instance in summary["instances"]:
                print(f"  [{instance['instance_id']}] gpu={instance['gpu_id']} port={instance['port']}")
                print(f"    {instance['command']}")
        print("Render complete.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as exc:
        print(f"[policy-eval][ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2)
