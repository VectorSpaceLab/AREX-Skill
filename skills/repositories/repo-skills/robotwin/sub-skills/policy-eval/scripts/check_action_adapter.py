#!/usr/bin/env python3
"""Validate RoboTwin policy-adapter observation and action shapes.

This helper is synthetic: it does not import XPolicyLab, does not start any
policy process, and only inspects local config files plus optional JSON payloads.
"""

from __future__ import annotations

import argparse
import json
import numbers
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency error path
    raise SystemExit("PyYAML is required to validate RoboTwin eval configs.") from exc


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


class ConfigError(ValueError):
    pass


class ActionError(ValueError):
    pass


class ObservationError(ValueError):
    pass


class ShapeError(ValueError):
    pass


class PayloadError(TypeError):
    pass


class RobotLayout(dict):
    env_cfg_type: str
    robot_name: str
    arm_dim: tuple[int, int]
    ee_dim: tuple[int, int]
    qpos_dim: int
    ee_action_dim: int



def is_scalar(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool)



def is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))



def is_flat_numeric_sequence(value: Any) -> bool:
    return is_sequence(value) and all(is_scalar(item) for item in value)



def infer_shape(value: Any) -> tuple[int, ...]:
    if is_scalar(value):
        return ()
    if not is_sequence(value):
        raise ShapeError(f"Expected a numeric sequence, got {type(value).__name__}.")
    shapes = [infer_shape(item) for item in value]
    if not shapes:
        return (0,)
    first = shapes[0]
    for shape in shapes[1:]:
        if shape != first:
            raise ShapeError("Ragged nested sequences are not supported.")
    return (len(shapes),) + first



def coerce_numeric_vector(value: Any, *, name: str) -> list[float]:
    if is_scalar(value):
        return [float(value)]
    if is_flat_numeric_sequence(value):
        return [float(item) for item in value]
    try:
        shape = infer_shape(value)
    except Exception as exc:
        raise ShapeError(f"{name} must be a flat numeric vector.") from exc
    raise ShapeError(f"{name} must be a flat numeric vector, got shape {shape!r}.")



def read_json_source(value: str | None, label: str) -> Any:
    if value is None:
        return None
    path = Path(value)
    text: str
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = value
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise PayloadError(f"Could not parse {label} as JSON: {exc}") from exc



def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Could not read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse {path}: {exc}") from exc



def load_robot_layout(repo_root: Path, env_cfg_type: str) -> dict[str, Any]:
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
            raise ConfigError(
                f"Could not resolve config.robot from {env_cfg_path}."
            ) from exc
    else:
        robot_name = ENV_TO_ROBOT_FALLBACK.get(env_cfg_type)
        if robot_name is None:
            raise ConfigError(
                f"Could not find env_cfg/{env_cfg_type}.yml and no fallback profile exists."
            )

    robot_info: Mapping[str, Any] | None = None
    if robot_info_path.is_file():
        robot_info = load_yaml(robot_info_path)
        if not isinstance(robot_info, Mapping):
            raise ConfigError(f"{robot_info_path} must contain a mapping root.")
    else:
        robot_info = ROBOT_INFO_FALLBACK

    raw_layout = robot_info.get(robot_name)
    if raw_layout is None:
        raw_layout = ROBOT_INFO_FALLBACK.get(robot_name)
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
    raise ActionError("action_type must be one of: joint, qpos, ee, endpose.")



def first_present(data: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None



def extract_vector(
    payload: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    fallback: Any,
    name: str,
    expected_len: int | None = None,
) -> list[float]:
    value = first_present(payload, keys)
    if value is None:
        if fallback is None:
            raise ActionError(f"Missing {name}; tried keys: {keys!r}.")
        value = fallback
    vector = coerce_numeric_vector(value, name=name)
    if expected_len is not None and len(vector) != expected_len:
        raise ActionError(f"{name} must have length {expected_len}, got {len(vector)}.")
    return vector



def extract_scalar(
    payload: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    fallback: Any,
    name: str,
) -> float:
    value = first_present(payload, keys)
    if value is None:
        if fallback is None:
            raise ActionError(f"Missing {name}; tried keys: {keys!r}.")
        value = fallback
    vector = coerce_numeric_vector(value, name=name)
    if len(vector) != 1:
        raise ActionError(f"{name} must be scalar for RoboTwin, got length {len(vector)}.")
    return float(vector[0])



def normalize_action_chunk(payload: Any) -> list[Any]:
    if payload is None:
        return []
    if isinstance(payload, Mapping):
        if "actions" in payload:
            return normalize_action_chunk(payload["actions"])
        return [payload]
    if is_flat_numeric_sequence(payload):
        return [payload]
    if is_sequence(payload):
        if len(payload) == 0:
            return []
        if all(isinstance(item, Mapping) for item in payload):
            return list(payload)
        if all(is_flat_numeric_sequence(item) for item in payload):
            return list(payload)
    if is_scalar(payload):
        return [[payload]]
    raise PayloadError(
        "Unsupported action payload nesting; use a mapping, a flat numeric vector, or a list of those."
    )



def observation_fallbacks(observation: Mapping[str, Any] | None) -> dict[str, Any]:
    if observation is None or not isinstance(observation, Mapping):
        return {}
    joint_action = observation.get("joint_action", {})
    endpose = observation.get("endpose", {})
    return {
        "left_joint": joint_action.get("left_arm"),
        "right_joint": joint_action.get("right_arm"),
        "left_gripper": joint_action.get("left_gripper", endpose.get("left_gripper")),
        "right_gripper": joint_action.get("right_gripper", endpose.get("right_gripper")),
        "left_endpose": endpose.get("left_endpose"),
        "right_endpose": endpose.get("right_endpose"),
    }



def validate_action_item(
    item: Any,
    *,
    layout: Mapping[str, Any],
    default_action_type: str,
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    fallbacks = observation_fallbacks(observation)
    if not isinstance(item, Mapping):
        flat = coerce_numeric_vector(item, name="action vector")
        expected_len = layout["qpos_dim"] if default_action_type == "qpos" else layout["ee_action_dim"]
        if len(flat) != expected_len:
            raise ActionError(
                f"Flat action vector must have length {expected_len}, got {len(flat)}."
            )
        return {
            "action_type": default_action_type,
            "flat_length": len(flat),
            "source": "flat",
        }

    action_type = normalize_action_type(item.get("action_type", default_action_type))
    if action_type == "qpos":
        left = extract_vector(
            item,
            ("left_arm_joint_state", "left_arm_joint", "left_joint_state", "arm_joint_state", "joint_state"),
            fallback=fallbacks.get("left_joint"),
            name="left arm joint action",
            expected_len=layout["arm_dim"][0],
        )
        right = extract_vector(
            item,
            ("right_arm_joint_state", "right_arm_joint", "right_joint_state"),
            fallback=fallbacks.get("right_joint"),
            name="right arm joint action",
            expected_len=layout["arm_dim"][1],
        )
        left_gripper = extract_scalar(
            item,
            ("left_ee_joint_state", "left_gripper", "left_gripper_pos", "ee_joint_state"),
            fallback=fallbacks.get("left_gripper"),
            name="left gripper action",
        )
        right_gripper = extract_scalar(
            item,
            ("right_ee_joint_state", "right_gripper", "right_gripper_pos"),
            fallback=fallbacks.get("right_gripper"),
            name="right gripper action",
        )
        flat = left + [left_gripper] + right + [right_gripper]
        expected_len = layout["qpos_dim"]
    else:
        left = extract_vector(
            item,
            ("left_ee_pose", "left_endpose", "ee_pose"),
            fallback=fallbacks.get("left_endpose"),
            name="left ee action",
            expected_len=7,
        )
        right = extract_vector(
            item,
            ("right_ee_pose", "right_endpose"),
            fallback=fallbacks.get("right_endpose"),
            name="right ee action",
            expected_len=7,
        )
        left_gripper = extract_scalar(
            item,
            ("left_ee_joint_state", "left_gripper", "left_gripper_pos", "ee_joint_state"),
            fallback=fallbacks.get("left_gripper"),
            name="left gripper action",
        )
        right_gripper = extract_scalar(
            item,
            ("right_ee_joint_state", "right_gripper", "right_gripper_pos"),
            fallback=fallbacks.get("right_gripper"),
            name="right gripper action",
        )
        flat = left + [left_gripper] + right + [right_gripper]
        expected_len = layout["ee_action_dim"]

    if len(flat) != expected_len:
        raise ActionError(
            f"Flattened action length must be {expected_len} for {action_type} mode, got {len(flat)}."
        )
    return {
        "action_type": action_type,
        "flat_length": len(flat),
        "source": "mapping",
    }



def validate_observation_sample(
    observation: Mapping[str, Any] | None,
    *,
    layout: Mapping[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if observation is None:
        return warnings
    if not isinstance(observation, Mapping):
        raise ObservationError("The observation sample must be a mapping.")

    obs_block = observation.get("observation", {})
    if obs_block and not isinstance(obs_block, Mapping):
        raise ObservationError("observation.observation must be a mapping when present.")

    if isinstance(obs_block, Mapping):
        for camera_name, camera in obs_block.items():
            if not isinstance(camera, Mapping):
                raise ObservationError(f"Camera {camera_name!r} must be a mapping.")
            rgb = camera.get("rgb")
            if rgb is not None:
                shape = infer_shape(rgb)
                if len(shape) != 3 or shape[-1] != 3:
                    raise ObservationError(
                        f"Camera {camera_name!r} rgb must have shape HxWx3, got {shape!r}."
                    )

    third_view = observation.get("third_view_rgb")
    if third_view is not None:
        shape = infer_shape(third_view)
        if len(shape) != 3 or shape[-1] != 3:
            raise ObservationError(f"third_view_rgb must have shape HxWx3, got {shape!r}.")

    joint_action = observation.get("joint_action")
    if joint_action is not None and not isinstance(joint_action, Mapping):
        raise ObservationError("joint_action must be a mapping when present.")
    if isinstance(joint_action, Mapping):
        for key, expected_len in (
            ("left_arm", layout["arm_dim"][0]),
            ("right_arm", layout["arm_dim"][1]),
            ("vector", layout["qpos_dim"]),
        ):
            if key in joint_action:
                vec = coerce_numeric_vector(joint_action[key], name=f"joint_action.{key}")
                if len(vec) != expected_len:
                    raise ObservationError(
                        f"joint_action.{key} must have length {expected_len}, got {len(vec)}."
                    )
        for key in ("left_gripper", "right_gripper"):
            if key in joint_action:
                vec = coerce_numeric_vector(joint_action[key], name=f"joint_action.{key}")
                if len(vec) != 1:
                    raise ObservationError(
                        f"joint_action.{key} must be scalar, got length {len(vec)}."
                    )

    endpose = observation.get("endpose")
    if endpose is not None and not isinstance(endpose, Mapping):
        raise ObservationError("endpose must be a mapping when present.")
    if isinstance(endpose, Mapping):
        for key in ("left_endpose", "right_endpose"):
            if key in endpose:
                vec = coerce_numeric_vector(endpose[key], name=f"endpose.{key}")
                if len(vec) != 7:
                    raise ObservationError(
                        f"endpose.{key} must have length 7, got {len(vec)}."
                    )
        for key in ("left_gripper", "right_gripper"):
            if key in endpose:
                vec = coerce_numeric_vector(endpose[key], name=f"endpose.{key}")
                if len(vec) != 1:
                    raise ObservationError(
                        f"endpose.{key} must be scalar, got length {len(vec)}."
                    )

    if not any(key in observation for key in ("observation", "joint_action", "endpose")):
        warnings.append("Observation sample has no RoboTwin keys to validate.")

    return warnings



def build_summary(
    *,
    repo_root: Path,
    layout: Mapping[str, Any],
    action_type: str,
    action_summary: list[dict[str, Any]] | None,
    observation_warnings: list[str],
) -> dict[str, Any]:
    return {
        "repo_root": str(repo_root),
        "env_cfg_type": layout["env_cfg_type"],
        "robot_name": layout["robot_name"],
        "arm_dim": list(layout["arm_dim"]),
        "ee_dim": list(layout["ee_dim"]),
        "action_type": action_type,
        "expected_flat_dims": {
            "qpos": layout["qpos_dim"],
            "ee": layout["ee_action_dim"],
        },
        "action_chunks": action_summary or [],
        "observation_warnings": observation_warnings,
    }



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate RoboTwin policy-adapter observation and action shapes."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--env-cfg-type", required=True)
    parser.add_argument(
        "--action-type",
        default="joint",
        choices=("joint", "qpos", "ee", "endpose"),
        help="Default action type to assume when the payload omits action_type.",
    )
    parser.add_argument("--action-file", type=str)
    parser.add_argument("--action-json", type=str)
    parser.add_argument("--observation-file", type=str)
    parser.add_argument("--observation-json", type=str)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    layout = load_robot_layout(repo_root, args.env_cfg_type)
    default_action_type = normalize_action_type(args.action_type)

    action_source = args.action_json or args.action_file
    observation_source = args.observation_json or args.observation_file
    action_payload = read_json_source(action_source, "action payload") if action_source else None
    observation_payload = (
        read_json_source(observation_source, "observation payload") if observation_source else None
    )

    action_summary: list[dict[str, Any]] | None = None
    if action_payload is not None:
        action_summary = []
        chunk = normalize_action_chunk(action_payload)
        for index, item in enumerate(chunk):
            try:
                item_summary = validate_action_item(
                    item,
                    layout=layout,
                    default_action_type=default_action_type,
                    observation=observation_payload if isinstance(observation_payload, Mapping) else None,
                )
            except Exception as exc:
                raise ActionError(f"Action chunk {index}: {exc}") from exc
            item_summary["chunk_index"] = index
            action_summary.append(item_summary)

    observation_warnings = validate_observation_sample(
        observation_payload if isinstance(observation_payload, Mapping) else None,
        layout=layout,
    )

    summary = build_summary(
        repo_root=repo_root,
        layout=layout,
        action_type=default_action_type,
        action_summary=action_summary,
        observation_warnings=observation_warnings,
    )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Repo root: {summary['repo_root']}")
        print(f"Env cfg type: {summary['env_cfg_type']}")
        print(f"Robot profile: {summary['robot_name']}")
        print(f"Arm dims: {summary['arm_dim']}")
        print(f"EE dims: {summary['ee_dim']}")
        print(f"Default action type: {summary['action_type']}")
        print(
            "Expected flattened dims: "
            f"qpos={summary['expected_flat_dims']['qpos']}, "
            f"ee={summary['expected_flat_dims']['ee']}"
        )
        if action_summary:
            for item in action_summary:
                print(
                    f"[chunk {item['chunk_index']}] type={item['action_type']} "
                    f"flat_length={item['flat_length']} source={item['source']}"
                )
        else:
            print("No action payload supplied; printed the expected contract only.")
        for warning in observation_warnings:
            print(f"[warn] {warning}")
        print("Adapter check passed.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, ActionError, ObservationError, ShapeError, PayloadError) as exc:
        print(f"[policy-eval][ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2)
