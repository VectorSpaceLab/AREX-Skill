#!/usr/bin/env python3
"""Validate a custom robosuite robot XML or a registered robot model.

The helper checks the joint naming convention used by robosuite robot assets,
prints the detected body-part split, and optionally loads a registered robot to
confirm that the expected end-effector mount bodies exist.

Examples:
    python check_custom_robot_model.py --robot-xml-file custom_robot.xml
    python check_custom_robot_model.py --robot Panda
"""

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

NON_ARM_PARTS = ("torso", "head", "leg", "gripper", "base")


def _resolve_xml_path(raw_path):
    path = Path(raw_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"XML file does not exist: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"XML path is not a file: {path}")
    return path.resolve()


def _load_xml_root(xml_path):
    try:
        return ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"failed to parse XML file {xml_path}: {exc}") from exc


def _arm_order_looks_left_first(arm_joint_names):
    def _side_index(tokens):
        for idx, name in enumerate(arm_joint_names):
            if any(token in name for token in tokens):
                return idx
        return None

    right_idx = _side_index(("r_", "right"))
    left_idx = _side_index(("l_", "left"))
    return left_idx is not None and right_idx is not None and left_idx < right_idx


def check_xml_definition(root, source_label="XML"):
    errors = 0
    world_body = root.find(".//worldbody")
    if world_body is None:
        print(f"Error: {source_label} is missing a <worldbody> element.", file=sys.stderr)
        return 1

    all_joints = world_body.findall(".//joint")
    if not all_joints:
        print(f"Error: {source_label} does not define any joints.", file=sys.stderr)
        return 1

    parts = {part_name: [] for part_name in NON_ARM_PARTS}
    parts["arm"] = []
    named_joint_count = 0
    for joint in all_joints:
        joint_name = joint.get("name")
        if not joint_name:
            print(f"Error: {source_label} contains an unnamed joint.", file=sys.stderr)
            errors += 1
            continue

        named_joint_count += 1
        matched = False
        for part_name in NON_ARM_PARTS:
            if part_name in joint_name:
                parts[part_name].append(joint_name)
                matched = True
                break
        if not matched:
            parts["arm"].append(joint_name)

    counted = sum(len(v) for v in parts.values())
    if counted != named_joint_count:
        print(
            f"Error: {source_label} counted {counted} named joints but found {named_joint_count} named joints.",
            file=sys.stderr,
        )
        errors += 1
    else:
        print(f"{source_label}: robosuite joint groups")
        for part_name in (*NON_ARM_PARTS, "arm"):
            if parts[part_name]:
                print(f"  - {part_name}: {len(parts[part_name])} joints -> {parts[part_name]}")

    if _arm_order_looks_left_first(parts["arm"]):
        print(
            f"Warning: {source_label} arm joints appear to start with a left-arm joint. "
            "Robosuite custom robots usually expect right-arm joints first.",
            file=sys.stderr,
        )

    return errors


def check_robot_xml_file(xml_file):
    try:
        xml_path = _resolve_xml_path(xml_file)
        root = _load_xml_root(xml_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return check_xml_definition(root, source_label=f"robot XML {xml_path}")


def check_registered_robot(robot_name):
    try:
        from robosuite.controllers import load_composite_controller_config
        from robosuite.robots import ROBOT_CLASS_MAPPING
        from robosuite.robots.robot import Robot
    except Exception as exc:
        print(f"Error: could not import robosuite robot APIs: {exc}", file=sys.stderr)
        return 1

    if robot_name not in ROBOT_CLASS_MAPPING:
        available = ", ".join(sorted(ROBOT_CLASS_MAPPING))
        print(f"Error: unknown registered robot '{robot_name}'. Available names: {available}", file=sys.stderr)
        return 1

    try:
        controller_config = load_composite_controller_config(controller="BASIC", robot=robot_name)
        robot = Robot(robot_type=robot_name, composite_controller_config=controller_config, gripper_type=None)
        robot.load_model()
    except Exception as exc:
        print(f"Error: failed to load registered robot '{robot_name}': {exc}", file=sys.stderr)
        return 1

    root = robot.robot_model.tree.getroot()
    errors = check_xml_definition(root, source_label=f"registered robot {robot_name}")

    world_body = root.find(".//worldbody")
    eef_names = getattr(robot.robot_model, "eef_name", None)
    if world_body is not None and eef_names:
        if isinstance(eef_names, dict):
            eef_items = eef_names.items()
        else:
            eef_items = [("eef", eef_names)]

        for arm_name, eef_name in eef_items:
            eef_body = world_body.find(f".//body[@name='{eef_name}']")
            if eef_body is None:
                print(
                    f"Error: registered robot '{robot_name}' is missing end-effector mount body '{eef_name}' "
                    f"for arm '{arm_name}'.",
                    file=sys.stderr,
                )
                errors += 1
    elif not eef_names:
        print(
            f"Warning: registered robot '{robot_name}' does not expose eef_name; skipped end-effector mount checks.",
            file=sys.stderr,
        )

    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a custom robosuite robot XML or a registered robot model."
    )
    parser.add_argument("--robot", type=str, default=None, help="Registered robosuite robot name to load and check.")
    parser.add_argument(
        "--robot-xml-file",
        type=str,
        default=None,
        help="Path to a custom robot XML file to validate.",
    )
    args = parser.parse_args(argv)

    if args.robot is None and args.robot_xml_file is None:
        print("Error: provide --robot, --robot-xml-file, or both.", file=sys.stderr)
        return 1

    errors = 0
    if args.robot_xml_file is not None:
        errors += check_robot_xml_file(args.robot_xml_file)
    if args.robot is not None:
        errors += check_registered_robot(args.robot)

    if errors == 0:
        print("Robot model checks completed successfully.")
    else:
        print(f"Robot model checks completed with {errors} error(s).", file=sys.stderr)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
