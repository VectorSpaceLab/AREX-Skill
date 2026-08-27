#!/usr/bin/env python3
"""Validate async inference scalar configuration without starting gRPC or a robot."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

KNOWN_AGGREGATES = {"weighted_average", "latest_only", "average", "conservative"}
SERVER_KEYS = {"host", "port", "fps", "inference_latency", "obs_queue_timeout"}
CLIENT_KEYS = {
    "policy_type",
    "pretrained_name_or_path",
    "robot",
    "actions_per_chunk",
    "task",
    "server_address",
    "policy_device",
    "client_device",
    "chunk_size_threshold",
    "fps",
    "aggregate_fn_name",
    "debug_visualize_queue_size",
}


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ValueError("YAML input needs PyYAML; use JSON or install the YAML dependency.") from exc
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError("configuration must contain a mapping/object at the top level")
    return value


def _port(value: Any, label: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
        errors.append(f"{label} must be an integer in [1, 65535]")
        return None
    return value


def _server_address(value: Any, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append("server_address must be a non-empty host:port string")
        return
    address = value.rsplit(":", 1)
    if len(address) != 2 or not address[0] or not re.fullmatch(r"[0-9]+", address[1]):
        errors.append("server_address must use host:port syntax, without an URL scheme")
        return
    _port(int(address[1]), "server_address port", errors)


def _positive_number(value: Any, label: str, errors: list[str], *, allow_zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{label} must be a number")
    elif value < 0 or (not allow_zero and value == 0):
        comparator = ">= 0" if allow_zero else "> 0"
        errors.append(f"{label} must be {comparator}")


def _validate_server(config: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    unknown = sorted(set(config) - SERVER_KEYS)
    if unknown:
        errors.append(f"unknown server keys: {unknown}")
    host = config.get("host", "localhost")
    if not isinstance(host, str) or not host.strip():
        errors.append("host must be a non-empty string")
    _port(config.get("port", 8080), "port", errors)
    _positive_number(config.get("fps", 30), "fps", errors)
    _positive_number(config.get("inference_latency", 0.0), "inference_latency", errors, allow_zero=True)
    _positive_number(config.get("obs_queue_timeout", 1.0), "obs_queue_timeout", errors, allow_zero=True)
    return {
        "role": "server",
        "host_present": bool(isinstance(host, str) and host.strip()),
        "port": config.get("port", 8080),
        "fps": config.get("fps", 30),
        "network_checked": False,
        "daemon_started": False,
    }


def _validate_client(config: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    unknown = sorted(set(config) - CLIENT_KEYS)
    if unknown:
        errors.append(f"unknown client keys: {unknown}")
    for key in ("policy_type", "pretrained_name_or_path"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            errors.append(f"{key} must be a non-empty string")
    for key in ("policy_device", "client_device"):
        device = config.get(key, "cpu")
        if not isinstance(device, str) or not device.strip():
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(config.get("robot"), dict):
        errors.append("robot must be a concrete robot config mapping; it is not constructed by this check")
    _server_address(config.get("server_address", "localhost:8080"), errors)
    _positive_number(config.get("fps", 30), "fps", errors)
    _positive_number(config.get("actions_per_chunk"), "actions_per_chunk", errors)
    threshold = config.get("chunk_size_threshold", 0.5)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
        errors.append("chunk_size_threshold must be a number in [0, 1]")
    aggregate = config.get("aggregate_fn_name", "weighted_average")
    if aggregate not in KNOWN_AGGREGATES:
        errors.append(f"aggregate_fn_name must be one of {sorted(KNOWN_AGGREGATES)}")
    return {
        "role": "client",
        "server_address_present": bool(config.get("server_address", "localhost:8080")),
        "policy_type_present": bool(config.get("policy_type")),
        "checkpoint_present": bool(config.get("pretrained_name_or_path")),
        "robot_constructed": False,
        "network_checked": False,
        "daemon_started": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check local PolicyServerConfig or RobotClientConfig scalar fields. "
            "This never imports a robot, contacts server_address, downloads a policy, or starts a daemon."
        )
    )
    parser.add_argument("--role", choices=("server", "client"), required=True)
    parser.add_argument("--config", type=Path, help="Local JSON/YAML mapping for the selected role.")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--inference-latency", type=float, dest="inference_latency")
    parser.add_argument("--obs-queue-timeout", type=float, dest="obs_queue_timeout")
    parser.add_argument("--server-address")
    parser.add_argument("--policy-type")
    parser.add_argument("--pretrained-name-or-path")
    parser.add_argument(
        "--robot-json",
        help="JSON robot mapping presence check only; it is never instantiated or connected.",
    )
    parser.add_argument("--policy-device")
    parser.add_argument("--client-device")
    parser.add_argument("--actions-per-chunk", type=int)
    parser.add_argument("--chunk-size-threshold", type=float)
    parser.add_argument("--aggregate-fn-name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = _load_mapping(args.config) if args.config else {}
    cli = vars(args)
    for key, value in cli.items():
        if key in {"role", "config", "robot_json"} or value is None:
            continue
        config[key] = value
    errors: list[str] = []
    if args.robot_json is not None:
        try:
            robot = json.loads(args.robot_json)
        except ValueError as exc:
            errors.append(f"robot-json must be valid JSON: {exc}")
        else:
            if not isinstance(robot, dict):
                errors.append("robot-json must contain a JSON object")
            else:
                config["robot"] = robot
    summary = _validate_server(config, errors) if args.role == "server" else _validate_client(config, errors)
    if errors:
        print("INVALID async configuration", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("No endpoint, daemon, robot, checkpoint, or credential was contacted.", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("Local scalar validation passed; endpoint, model, plugin, and hardware gates remain unchecked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
