#!/usr/bin/env python3
"""Validate a robosuite composite controller JSON config.

This validator performs safe structural checks without requiring a simulation.
It best-effort imports robosuite registries when available and falls back to
static built-in controller names when they are not.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

BUILTIN_COMPOSITE_TYPES = {
    "BASIC",
    "HYBRID_MOBILE_BASE",
    "WHOLE_BODY_COMPOSITE",
    "WHOLE_BODY_IK",
    "WHOLE_BODY_MINK_IK",
}
BUILTIN_PART_TYPES = {
    "IK_POSE",
    "JOINT_POSITION",
    "JOINT_TORQUE",
    "JOINT_VELOCITY",
    "JOINT_VELOCITY_LEGACY",
    "OSC_POSE",
    "OSC_POSITION",
    "GRIP",
}
REQUIRED_WHOLE_BODY_KEYS = {"ref_name", "actuation_part_names"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a robosuite composite controller JSON file.")
    parser.add_argument("path", help="Path to the controller JSON file to validate.")
    parser.add_argument(
        "--allow-custom-type",
        action="store_true",
        help="Treat an unknown top-level controller type as informational instead of an error.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def best_effort_registry() -> tuple[set[str], set[str], list[str]]:
    composite_types: set[str] = set()
    part_types: set[str] = set()
    warnings: list[str] = []

    try:
        from robosuite.controllers.composite import ALL_COMPOSITE_CONTROLLERS

        composite_types.update(str(name) for name in ALL_COMPOSITE_CONTROLLERS)
    except Exception as exc:  # pragma: no cover - import availability varies by environment
        warnings.append(f"Could not import robosuite composite registry: {exc}")

    try:
        from robosuite.controllers import ALL_PART_CONTROLLERS

        part_types.update(str(name) for name in ALL_PART_CONTROLLERS)
    except Exception as exc:  # pragma: no cover - import availability varies by environment
        warnings.append(f"Could not import robosuite part registry: {exc}")

    return composite_types, part_types, warnings


def validate_controller_type(
    config: dict,
    composite_types: set[str],
    part_types: set[str],
    allow_custom_type: bool,
    warnings: list[str],
    errors: list[str],
) -> str | None:
    controller_type = config.get("type")
    if not isinstance(controller_type, str) or not controller_type.strip():
        errors.append("Missing or invalid top-level 'type' string.")
        return None

    known_types = BUILTIN_COMPOSITE_TYPES | composite_types
    if controller_type not in known_types:
        message = f"Unknown top-level controller type '{controller_type}'."
        if allow_custom_type:
            warnings.append(message + " Allowed because --allow-custom-type was set.")
        else:
            errors.append(message)

    return controller_type


def validate_body_part(name: str, node: Any, part_types: set[str], warnings: list[str], errors: list[str]) -> None:
    if not isinstance(node, dict):
        errors.append(f"Body part '{name}' must map to an object, got {type(node).__name__}.")
        return

    controller_type = node.get("type")
    if not isinstance(controller_type, str) or not controller_type.strip():
        errors.append(f"Body part '{name}' is missing a 'type' string.")
    else:
        known_part_types = BUILTIN_PART_TYPES | part_types
        if controller_type not in known_part_types:
            warnings.append(
                f"Body part '{name}' uses unknown controller type '{controller_type}'. "
                "This may be fine for a custom extension, but verify the module is imported."
            )

    if name.endswith("_gripper"):
        if controller_type not in {"GRIP", "JOINT_POSITION"}:
            warnings.append(
                f"Gripper part '{name}' usually uses 'GRIP' or 'JOINT_POSITION', got '{controller_type}'."
            )
        return

    if name in {"right", "left"}:
        gripper = node.get("gripper")
        if gripper is not None:
            if not isinstance(gripper, dict):
                errors.append(f"Arm '{name}' gripper config must be an object.")
            elif not isinstance(gripper.get("type"), str):
                errors.append(f"Arm '{name}' gripper config is missing a 'type' string.")
        else:
            warnings.append(f"Arm '{name}' has no nested gripper config. That is only correct for gripper-less robots.")

    if name in {"base", "torso", "head", "legs"} and controller_type == "JOINT_POSITION" and name == "base":
        warnings.append("Base controllers usually use JOINT_VELOCITY; JOINT_POSITION is not implemented for mobile bases.")


def iter_body_parts(body_parts: dict) -> Iterable[tuple[str, Any]]:
    for name, node in body_parts.items():
        if name == "arms" and isinstance(node, dict):
            for arm_name, arm_node in node.items():
                yield arm_name, arm_node
        else:
            yield name, node


def validate_whole_body_specifics(
    controller_type: str | None,
    config: dict,
    warnings: list[str],
    errors: list[str],
) -> None:
    if controller_type not in {"WHOLE_BODY_IK", "WHOLE_BODY_MINK_IK", "WHOLE_BODY_COMPOSITE"}:
        return

    specific = config.get("composite_controller_specific_configs")
    if not isinstance(specific, dict):
        errors.append(
            f"Controller type '{controller_type}' expects 'composite_controller_specific_configs' to be a mapping."
        )
        return

    for key in REQUIRED_WHOLE_BODY_KEYS:
        value = specific.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"Whole-body config is missing a non-empty list for '{key}'.")

    if controller_type == "WHOLE_BODY_MINK_IK":
        try:
            import mink  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional dependency
            warnings.append(f"WHOLE_BODY_MINK_IK is optional and mink is unavailable: {exc}")


def validate(config: Any, allow_custom_type: bool) -> dict:
    report = {
        "ok": False,
        "errors": [],
        "warnings": [],
        "known_composite_types": sorted(BUILTIN_COMPOSITE_TYPES),
        "known_part_types": sorted(BUILTIN_PART_TYPES),
        "registry_composite_types": [],
        "registry_part_types": [],
        "registry_source": {
            "composite_imported": False,
            "part_imported": False,
        },
    }

    composite_types, part_types, import_warnings = best_effort_registry()
    report["warnings"].extend(import_warnings)
    report["registry_source"]["composite_imported"] = bool(composite_types)
    report["registry_source"]["part_imported"] = bool(part_types)
    report["registry_composite_types"] = sorted(composite_types)
    report["registry_part_types"] = sorted(part_types)
    report["known_composite_types"] = sorted(BUILTIN_COMPOSITE_TYPES | composite_types)
    report["known_part_types"] = sorted(BUILTIN_PART_TYPES | part_types)

    errors = report["errors"]
    warnings = report["warnings"]

    if not isinstance(config, dict):
        errors.append(f"Top-level JSON value must be an object, got {type(config).__name__}.")
        return report

    controller_type = validate_controller_type(config, composite_types, part_types, allow_custom_type, warnings, errors)

    body_parts = config.get("body_parts")
    if not isinstance(body_parts, dict):
        errors.append("Missing or invalid top-level 'body_parts' mapping.")
    else:
        for part_name, part_node in iter_body_parts(body_parts):
            validate_body_part(part_name, part_node, part_types, warnings, errors)

    validate_whole_body_specifics(controller_type, config, warnings, errors)

    report["ok"] = len(errors) == 0
    if controller_type is not None:
        report["controller_type"] = controller_type
    return report


def main() -> int:
    args = parse_args()
    path = Path(args.path)

    if not path.is_file():
        report = {
            "ok": False,
            "path": str(path),
            "errors": [f"Controller config file not found: {path}"],
            "warnings": [],
        }
        print(json.dumps(report, indent=2, sort_keys=False))
        return 1

    try:
        config = load_json(path)
    except Exception as exc:
        report = {
            "ok": False,
            "path": str(path),
            "errors": [f"Failed to parse JSON: {exc}"],
            "warnings": [],
        }
        print(json.dumps(report, indent=2, sort_keys=False))
        return 1

    report = validate(config, allow_custom_type=args.allow_custom_type)
    report["path"] = str(path)
    print(json.dumps(report, indent=2, sort_keys=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
