#!/usr/bin/env python3
"""Preflight the portable, task-facing subset of an IR-SIM YAML scene.

The checker intentionally does not import IR-SIM or construct a GUI. It uses
``yaml.safe_load`` and reports paths that can be fixed before ``irsim.make``.
It is stricter than the runtime's compatibility broadcasting for per-object
lists so that changing ``number`` cannot silently duplicate the last item.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on caller environment
    raise SystemExit("PyYAML is required; install the ir-sim base dependencies") from exc

ROOT_KEYS = {"world", "robot", "obstacle", "gui"}
WORLD_KEYS = {
    "name", "height", "width", "step_time", "sample_time", "offset",
    "step_mode", "control_mode", "collision_mode", "status", "obstacle_map",
    "mdownsample", "fog_map", "fog_map_resolution", "plot",
}
OBJECT_KEYS = {
    "number", "distribution", "name", "shape", "kinematics", "state",
    "velocity", "goal", "role", "color", "static", "vel_min", "vel_max",
    "acce", "angle_range", "behavior", "group_behavior", "goal_threshold",
    "sensors", "arrive_mode", "description", "group", "group_name",
    "state_dim", "vel_dim", "unobstructed", "fov", "fov_radius", "plot",
}
DISTRIBUTION_KEYS = {
    "name", "range_low", "range_high", "min_distance", "center", "radius", "3d",
}
KINEMATICS_KEYS = {"name", "noise", "alpha", "mode", "wheelbase"}
BEHAVIOR_KEYS = {
    "name", "wander", "loop", "target_roles", "range_low", "range_high",
    "angle_tolerance", "vxmax", "vymax", "acce", "factor", "mode",
    "neighbor_threshold", "vmax", "relaxation_time", "force_factor_desired",
    "force_factor_social", "force_factor_obstacle", "sigma_obstacle",
    "lambda_importance", "gamma", "n_angular", "n_velocity", "safety_radius",
}
GROUP_BEHAVIOR_KEYS = {
    "name", "wander", "range_low", "range_high", "neighborDist",
    "maxNeighbors", "timeHorizon", "timeHorizonObst", "safe_radius", "maxSpeed",
}
SHAPE_KEYS = {
    "name", "radius", "center", "random_shape", "radius_range", "length", "width",
    "wheelbase", "vertices", "is_convex", "parts", "pose", "center_range",
    "avg_radius_range", "irregularity_range", "spikeyness_range", "num_vertices_range",
}
SENSOR_KEYS = {
    "name", "type", "range_min", "range_max", "angle_range", "number", "scan_time",
    "noise", "std", "angle_std", "offset", "has_velocity", "motion_compensate",
    "velocity_noise_std", "plot", "alpha", "color", "velocity_color",
    "velocity_color_max", "velocity_linewidth", "no_hit_linewidth", "no_hit_alpha",
    "show_velocity_markers", "velocity_marker_size", "velocity_marker_edge_color",
    "velocity_marker_edge_width", "zero_velocity_color", "positive_velocity_color",
    "negative_velocity_color", "no_hit_color",
}

KINEMATICS: dict[str, tuple[int, int]] = {
    "diff": (3, 2),
    "omni": (3, 2),
    "omni_angular": (3, 3),
    "acker": (4, 2),
}
BEHAVIORS = {
    "diff": {"dash", "rvo", "sfm"},
    "omni": {"dash", "rvo", "sfm"},
    "omni_angular": {"dash"},
    "acker": {"dash"},
}
SHAPES = {"circle", "rectangle", "polygon", "compound", "linestring"}
COMPOUND_PARTS = {"circle", "rectangle", "polygon"}
DISTRIBUTIONS = {"manual", "random", "circle"}
SENSORS = {"lidar2d", "fmcw_lidar2d"}


def path_text(path: tuple[Any, ...]) -> str:
    text = "$"
    for part in path:
        text += f"[{part!r}]" if isinstance(part, int) else f".{part}"
    return text


def add(errors: list[str], path: tuple[Any, ...], message: str) -> None:
    errors.append(f"{path_text(path)}: {message}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_finite_number(value: Any) -> bool:
    return is_number(value) and math.isfinite(float(value))


def is_numeric_vector(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(is_number(x) for x in value)


def is_nested_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, list) for x in value)


def check_keys(value: Any, allowed: set[str], path: tuple[Any, ...], errors: list[str]) -> None:
    if not isinstance(value, dict):
        add(errors, path, "must be a mapping")
        return
    for key in value:
        if key not in allowed:
            add(errors, path + (key,), "unknown key")


def check_number(
    value: Any,
    path: tuple[Any, ...],
    errors: list[str],
    *,
    positive: bool = False,
    finite: bool = False,
) -> None:
    if not is_number(value):
        add(errors, path, "must be a number")
        return
    if finite and not math.isfinite(float(value)):
        add(errors, path, "must be finite")
    if isinstance(value, float) and math.isnan(value):
        add(errors, path, "must not be NaN")
    if positive and value <= 0:
        add(errors, path, "must be greater than zero")


def validate_vector(
    value: Any,
    path: tuple[Any, ...],
    errors: list[str],
    minimum: int,
    label: str,
    *,
    exact: int | None = None,
    finite: bool = False,
) -> None:
    if not is_numeric_vector(value):
        add(errors, path, f"must be a numeric vector ({label})")
        return
    expected = exact if exact is not None else minimum
    if exact is not None and len(value) != exact:
        add(errors, path, f"must contain exactly {exact} entries ({label})")
    elif len(value) < minimum:
        add(errors, path, f"must contain at least {minimum} entries ({label})")
    if finite and any(not math.isfinite(float(x)) for x in value):
        add(errors, path, "must contain only finite numbers")


def validate_pair(value: Any, path: tuple[Any, ...], errors: list[str]) -> None:
    validate_vector(value, path, errors, 2, "[low, high]", exact=2, finite=True)
    if is_numeric_vector(value) and len(value) == 2 and value[0] > value[1]:
        add(errors, path, "lower bound must not exceed upper bound")


def validate_vertices(value: Any, path: tuple[Any, ...], errors: list[str], minimum: int) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        add(errors, path, f"must contain at least {minimum} [x, y] vertices")
        return
    for index, vertex in enumerate(value):
        validate_vector(vertex, path + (index,), errors, 2, "[x, y]", exact=2, finite=True)


def validate_shape(
    shape: Any, path: tuple[Any, ...], errors: list[str], *, compound_part: bool = False
) -> None:
    if not isinstance(shape, dict):
        add(errors, path, "shape must be a mapping")
        return
    check_keys(shape, SHAPE_KEYS, path, errors)
    if "pose" in shape and not compound_part:
        add(errors, path + ("pose",), "pose is valid only on a compound part")
    name = shape.get("name")
    if not isinstance(name, str):
        add(errors, path + ("name",), "shape mappings require a name")
        return
    name = name.lower()
    if name not in SHAPES:
        add(errors, path + ("name",), f"unsupported shape {name!r}; use {sorted(SHAPES)}")
        return
    if name == "circle":
        if "radius" in shape:
            check_number(shape["radius"], path + ("radius",), errors, positive=True, finite=True)
        if "center" in shape:
            validate_vector(shape["center"], path + ("center",), errors, 2, "[x, y]", exact=2, finite=True)
        if shape.get("random_shape") and "radius_range" in shape:
            validate_pair(shape["radius_range"], path + ("radius_range",), errors)
    elif name == "rectangle":
        for key in ("length", "width"):
            if key in shape:
                check_number(shape[key], path + (key,), errors, positive=True, finite=True)
    elif name in {"polygon", "linestring"}:
        if "vertices" in shape:
            validate_vertices(shape["vertices"], path + ("vertices",), errors, 3 if name == "polygon" else 2)
        elif not shape.get("random_shape"):
            add(errors, path + ("vertices",), f"{name} needs vertices unless random_shape is true")
    elif name == "compound":
        parts = shape.get("parts")
        if not isinstance(parts, list) or not parts:
            add(errors, path + ("parts",), "compound requires a non-empty list")
            return
        for index, part in enumerate(parts):
            part_path = path + ("parts", index)
            validate_shape(part, part_path, errors, compound_part=True)
            if isinstance(part, dict):
                part_name = str(part.get("name", "")).lower()
                if part_name not in COMPOUND_PARTS:
                    add(errors, part_path + ("name",), "compound parts support only circle, rectangle, or polygon")
                if "pose" in part:
                    validate_vector(part["pose"], part_path + ("pose",), errors, 3, "finite [x, y, theta]", exact=3, finite=True)
                if "color" in part:
                    add(errors, part_path + ("color",), "compound parts cannot set color; set it on the owning object")


def validate_distribution(value: Any, path: tuple[Any, ...], errors: list[str]) -> None:
    if not isinstance(value, dict):
        add(errors, path, "distribution must be a mapping")
        return
    check_keys(value, DISTRIBUTION_KEYS, path, errors)
    name = value.get("name")
    if name not in DISTRIBUTIONS:
        if name == "uniform":
            add(errors, path + ("name",), "uniform is not implemented; use random or circle")
        else:
            add(errors, path + ("name",), f"unsupported distribution {name!r}; use {sorted(DISTRIBUTIONS)}")
    if name == "random":
        for key in ("range_low", "range_high"):
            if key in value:
                validate_vector(value[key], path + (key,), errors, 3, "[x, y, theta]", exact=3, finite=True)
        if "min_distance" in value:
            check_number(value["min_distance"], path + ("min_distance",), errors, positive=True, finite=True)
    elif name == "circle":
        if "center" in value:
            validate_vector(value["center"], path + ("center",), errors, 2, "[x, y] or [x, y, theta]", finite=True)
        if "radius" in value:
            check_number(value["radius"], path + ("radius",), errors, positive=True, finite=True)
    if value.get("3d") is True:
        add(errors, path + ("3d",), "3D state generation is not implemented in this release")


def validate_component_mapping(
    value: Any, path: tuple[Any, ...], errors: list[str], allowed: set[str]
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        add(errors, path, "must be a mapping")
        return None
    check_keys(value, allowed, path, errors)
    return value


def validate_kinematics(value: Any, path: tuple[Any, ...], errors: list[str]) -> str | None:
    mapping = validate_component_mapping(value, path, errors, KINEMATICS_KEYS)
    if mapping is None:
        return None
    name = mapping.get("name")
    if not isinstance(name, str):
        add(errors, path + ("name",), "kinematics mappings require a name")
        return None
    name = name.lower()
    if name not in KINEMATICS:
        add(errors, path + ("name",), f"unsupported kinematics {name!r}; use {sorted(KINEMATICS)}")
    if name == "acker" and mapping.get("mode") not in {None, "steer", "angular"}:
        add(errors, path + ("mode",), "must be steer or angular")
    if "alpha" in mapping:
        validate_vector(mapping["alpha"], path + ("alpha",), errors, 1, "noise parameters", finite=True)
    if "wheelbase" in mapping:
        check_number(mapping["wheelbase"], path + ("wheelbase",), errors, positive=True, finite=True)
    return name


def validate_behavior(value: Any, path: tuple[Any, ...], errors: list[str], kin: str | None) -> None:
    mapping = validate_component_mapping(value, path, errors, BEHAVIOR_KEYS)
    if mapping is None:
        return
    name = mapping.get("name")
    if not isinstance(name, str):
        add(errors, path + ("name",), "behavior mappings require a name")
        return
    name = name.lower()
    if kin not in KINEMATICS:
        add(errors, path, "a built-in behavior requires one of the four built-in kinematics")
    elif name not in BEHAVIORS.get(kin, set()):
        add(errors, path + ("name",), f"behavior {name!r} is not registered for {kin!r}; supported: {sorted(BEHAVIORS[kin])}")
    if mapping.get("target_roles") not in {None, "all", "robot", "obstacle"}:
        add(errors, path + ("target_roles",), "must be all, robot, or obstacle")
    if name == "rvo" and mapping.get("mode") not in {None, "rvo", "hrvo", "vo"}:
        add(errors, path + ("mode",), "must be rvo, hrvo, or vo")


def validate_group_behavior(value: Any, path: tuple[Any, ...], errors: list[str]) -> None:
    mapping = validate_component_mapping(value, path, errors, GROUP_BEHAVIOR_KEYS)
    if mapping is None:
        return
    if mapping.get("name") != "orca":
        add(errors, path + ("name",), "only the optional ORCA group behavior is built in; it requires pyrvo")


def validate_sensor(value: Any, path: tuple[Any, ...], errors: list[str]) -> None:
    if not isinstance(value, dict):
        add(errors, path, "each sensor must be a mapping")
        return
    check_keys(value, SENSOR_KEYS, path, errors)
    name = value.get("name", value.get("type"))
    if value.get("name") is not None and value.get("type") is not None and value["name"] != value["type"]:
        add(errors, path, "name and type must identify the same sensor")
    if name not in SENSORS:
        add(errors, path + ("name",), f"sensor name/type must be one of {sorted(SENSORS)}")
    for key in ("range_min", "range_max", "scan_time", "std", "angle_std", "velocity_noise_std"):
        if key in value:
            check_number(value[key], path + (key,), errors, positive=key in {"range_max", "scan_time"}, finite=True)
    if "range_min" in value and "range_max" in value and is_number(value["range_min"]) and is_number(value["range_max"]) and value["range_min"] >= value["range_max"]:
        add(errors, path, "range_min must be less than range_max")
    if "number" in value and (not isinstance(value["number"], int) or isinstance(value["number"], bool) or value["number"] < 1):
        add(errors, path + ("number",), "must be a positive integer")
    if "offset" in value:
        validate_vector(value["offset"], path + ("offset",), errors, 3, "[x, y, theta]", exact=3, finite=True)


def validate_per_object(
    value: Any,
    path: tuple[Any, ...],
    number: int,
    errors: list[str],
    kind: str,
    validator: Callable[[Any, tuple[Any, ...], list[str]], None],
) -> None:
    if isinstance(value, dict):
        validator(value, path, errors)
        return
    if not isinstance(value, list):
        add(errors, path, "must be a mapping, vector, or list")
        return
    if kind in {"state", "goal", "velocity", "vel_min", "vel_max", "acce"} and is_numeric_vector(value):
        validator(value, path, errors)
        return
    if kind == "sensors" and all(isinstance(item, dict) for item in value):
        for index, sensor in enumerate(value):
            validate_sensor(sensor, path + (index,), errors)
        return
    if len(value) != number:
        add(errors, path, f"per-object list has {len(value)} entries but number is {number}; give exactly one entry per object")
        return
    for index, item in enumerate(value):
        validator(item, path + (index,), errors)


def validate_gui(value: Any, path: tuple[Any, ...], errors: list[str]) -> None:
    if not isinstance(value, dict):
        add(errors, path, "must be a mapping")
        return
    check_keys(value, {"keyboard", "mouse"}, path, errors)
    keyboard = value.get("keyboard")
    if keyboard is not None:
        if not isinstance(keyboard, dict):
            add(errors, path + ("keyboard",), "must be a mapping")
        else:
            allowed = {"backend", "global_hook", "key_lv_max", "key_ang_max", "key_lv", "key_ang", "key_rot", "key_id"}
            check_keys(keyboard, allowed, path + ("keyboard",), errors)
            if keyboard.get("backend") not in {None, "pynput", "mpl"}:
                add(errors, path + ("keyboard", "backend"), "must be pynput or mpl")
    mouse = value.get("mouse")
    if mouse is not None:
        if not isinstance(mouse, dict):
            add(errors, path + ("mouse",), "must be a mapping")
        else:
            check_keys(mouse, {"zoom_factor"}, path + ("mouse",), errors)
            if "zoom_factor" in mouse:
                check_number(mouse["zoom_factor"], path + ("mouse", "zoom_factor"), errors, positive=True, finite=True)


def validate_object(group: Any, path: tuple[Any, ...], errors: list[str], names: list[str]) -> None:
    if not isinstance(group, dict):
        add(errors, path, "object group must be a mapping")
        return
    check_keys(group, OBJECT_KEYS, path, errors)
    if "role" in group:
        add(errors, path + ("role",), "role is inferred from the robot/obstacle section; omit it")
    number = group.get("number", 1)
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        add(errors, path + ("number",), "must be a positive integer")
        number = 1

    validate_distribution(group.get("distribution", {"name": "manual"}), path + ("distribution",), errors)

    kin_value = group.get("kinematics")
    kin_list: list[str | None]
    if isinstance(kin_value, list):
        if len(kin_value) != number:
            add(errors, path + ("kinematics",), f"per-object list has {len(kin_value)} entries but number is {number}")
        kin_list = [validate_kinematics(item, path + ("kinematics", index), errors) for index, item in enumerate(kin_value)]
        if len(kin_list) < number:
            kin_list.extend([None] * (number - len(kin_list)))
    elif kin_value is None:
        kin_list = [None] * number
    else:
        kin = validate_kinematics(kin_value, path + ("kinematics",), errors)
        kin_list = [kin] * number

    name_value = group.get("name")
    if isinstance(name_value, str):
        if not name_value:
            add(errors, path + ("name",), "must be a non-empty string")
        elif number > 1:
            add(errors, path + ("name",), "a multi-object group needs a list of unique names")
        names.append(name_value)
    elif isinstance(name_value, list):
        if len(name_value) != number:
            add(errors, path + ("name",), f"name list has {len(name_value)} entries but number is {number}")
        for index, name in enumerate(name_value):
            if not isinstance(name, str) or not name:
                add(errors, path + ("name", index), "must be a non-empty string")
            else:
                names.append(name)
    elif name_value is not None:
        add(errors, path + ("name",), "must be a string or a per-object list of strings")

    state_min = 2
    if "state" in group:
        state = group["state"]
        if is_numeric_vector(state):
            validate_vector(state, path + ("state",), errors, state_min, "[x, y, theta, ...]", finite=True)
        elif isinstance(state, list):
            validate_per_object(state, path + ("state",), number, errors, "state", lambda v, p, e: validate_vector(v, p, e, state_min, "[x, y, theta, ...]", finite=True))
        else:
            add(errors, path + ("state",), "must be a numeric vector or a per-object list")
    if "goal" in group:
        goal = group["goal"]
        if goal is None:
            pass
        elif is_numeric_vector(goal):
            validate_vector(goal, path + ("goal",), errors, 2, "[x, y, theta, ...]", finite=True)
        elif isinstance(goal, list):
            if number == 1 and len(goal) == 1 and is_nested_list(goal[0]):
                # The factory needs one outer item for one object's waypoint
                # deque: goal: [[[x, y, theta], [x2, y2, theta2]]].
                for index, item in enumerate(goal[0]):
                    validate_vector(item, path + ("goal", 0, index), errors, 2, "goal waypoint", finite=True)
            elif number == 1 and is_nested_list(goal) and len(goal) > 1:
                add(errors, path + ("goal",), "one object's sequential goals need one extra outer list; a plain list of vectors is truncated by the factory")
            else:
                validate_per_object(goal, path + ("goal",), number, errors, "goal", lambda v, p, e: validate_vector(v, p, e, 2, "goal vector", finite=True))
        else:
            add(errors, path + ("goal",), "must be a numeric vector, waypoint list, or null")

    def action_validator(item: Any, item_path: tuple[Any, ...], item_errors: list[str]) -> None:
        # A scalar kinematics mapping has one action dimension for all members.
        index = item_path[-1] if isinstance(kin_value, list) and isinstance(item_path[-1], int) else 0
        kin = kin_list[index] if index < len(kin_list) else None
        dim = KINEMATICS.get(kin, (3, 2))[1]
        validate_vector(
            item,
            item_path,
            item_errors,
            dim,
            f"control vector for {kin or 'static'}",
            exact=dim,
            # ``acce`` legitimately uses +/-inf as an unlimited bound;
            # velocity/state controls must remain finite.
            finite=key != "acce",
        )

    for key in ("velocity", "vel_min", "vel_max", "acce"):
        if key in group:
            validate_per_object(group[key], path + (key,), number, errors, key, action_validator)

    if "shape" in group:
        validate_per_object(group["shape"], path + ("shape",), number, errors, "shape", validate_shape)
    if "behavior" in group:
        behavior = group["behavior"]
        if isinstance(behavior, list):
            if len(behavior) != number:
                add(errors, path + ("behavior",), f"per-object list has {len(behavior)} entries but number is {number}")
            for index, item in enumerate(behavior):
                kin = kin_list[index] if index < len(kin_list) else None
                validate_behavior(item, path + ("behavior", index), errors, kin)
        else:
            behavior_kins = kin_list if isinstance(kin_value, list) else [kin_list[0]]
            for kin in behavior_kins:
                validate_behavior(behavior, path + ("behavior",), errors, kin)
    if "group_behavior" in group:
        validate_group_behavior(group["group_behavior"], path + ("group_behavior",), errors)
    if "sensors" in group:
        validate_per_object(group["sensors"], path + ("sensors",), number, errors, "sensors", validate_sensor)

    if group.get("arrive_mode") not in {None, "position", "state"}:
        add(errors, path + ("arrive_mode",), "must be position or state")
    if "angle_range" in group:
        validate_pair(group["angle_range"], path + ("angle_range",), errors)
    for key in ("state_dim", "vel_dim", "group"):
        if key in group and (not isinstance(group[key], int) or isinstance(group[key], bool)):
            add(errors, path + (key,), "must be an integer")
    if "goal_threshold" in group:
        check_number(group["goal_threshold"], path + ("goal_threshold",), errors, positive=True, finite=True)

    shape_value = group.get("shape")
    shapes = shape_value if isinstance(shape_value, list) else [shape_value]
    check_indices = range(number) if isinstance(kin_value, list) or isinstance(shape_value, list) else range(1)
    for index in check_indices:
        kin = kin_list[index] if index < len(kin_list) else None
        if kin not in KINEMATICS:
            continue
        natural_state, natural_action = KINEMATICS[kin]
        if isinstance(group.get("state_dim"), int) and group["state_dim"] < natural_state:
            add(errors, path + ("state_dim",), f"must be at least {natural_state} for {kin}")
        if isinstance(group.get("vel_dim"), int) and group["vel_dim"] != natural_action:
            add(errors, path + ("vel_dim",), f"must equal {natural_action} for {kin}")
        if kin == "acker":
            shape = shapes[index] if index < len(shapes) else (shapes[-1] if shapes else None)
            if not isinstance(shape, dict) or shape.get("name", "").lower() not in {"circle", "rectangle"}:
                add(errors, path + ("shape",), "Ackermann requires an explicit circle or rectangle shape with wheelbase")
            elif not is_finite_number(shape.get("wheelbase")) or shape["wheelbase"] <= 0:
                suffix = ("shape", index, "wheelbase") if isinstance(shape_value, list) else ("shape", "wheelbase")
                add(errors, path + suffix, "Ackermann requires an explicit positive wheelbase")


def validate_document(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["$: document must be a YAML mapping"]
    check_keys(document, ROOT_KEYS, (), errors)
    world = document.get("world", {})
    if not isinstance(world, dict):
        add(errors, ("world",), "must be a mapping")
    else:
        check_keys(world, WORLD_KEYS, ("world",), errors)
        for key in ("height", "width", "step_time"):
            if key in world:
                check_number(world[key], ("world", key), errors, positive=True, finite=True)
        if "sample_time" in world:
            check_number(world["sample_time"], ("world", "sample_time"), errors, positive=True, finite=True)
        if "offset" in world:
            validate_vector(world["offset"], ("world", "offset"), errors, 2, "[x, y]", exact=2, finite=True)
        if world.get("step_mode") not in {None, "internal", "external"}:
            add(errors, ("world", "step_mode"), "must be internal or external")
        if world.get("control_mode") not in {None, "auto", "keyboard"}:
            add(errors, ("world", "control_mode"), "must be auto or keyboard")
        if world.get("collision_mode") not in {None, "stop", "reactive", "unobstructed", "unobstructed_obstacles"}:
            add(errors, ("world", "collision_mode"), "unsupported collision mode")
        if "mdownsample" in world and (not isinstance(world["mdownsample"], int) or isinstance(world["mdownsample"], bool) or world["mdownsample"] < 1):
            add(errors, ("world", "mdownsample"), "must be a positive integer")
        if isinstance(world.get("obstacle_map"), dict) and not isinstance(world["obstacle_map"].get("name"), str):
            add(errors, ("world", "obstacle_map", "name"), "generator mappings require a name; map details belong to sensing-and-mapping")
    names: list[str] = []
    for role in ("robot", "obstacle"):
        value = document.get(role)
        if value is None:
            continue
        if not isinstance(value, (list, dict)):
            add(errors, (role,), "must be a mapping or list of mappings")
            continue
        groups = value if isinstance(value, list) else [value]
        for index, group in enumerate(groups):
            validate_object(group, (role, index) if isinstance(value, list) else (role,), errors, names)
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        add(errors, (), f"duplicate explicit object names: {duplicates}")
    if "gui" in document:
        validate_gui(document["gui"], ("gui",), errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely preflight an IR-SIM YAML scene without importing or running IR-SIM."
    )
    parser.add_argument("scene", type=Path, help="YAML scene file")
    args = parser.parse_args(argv)
    try:
        with args.scene.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except FileNotFoundError:
        print(f"ERROR: scene file not found: {args.scene}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"ERROR: YAML parse failed: {exc}", file=sys.stderr)
        return 2
    errors = validate_document(document)
    if errors:
        print(f"INVALID: {len(errors)} issue(s) found in {args.scene}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"VALID: {args.scene}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
