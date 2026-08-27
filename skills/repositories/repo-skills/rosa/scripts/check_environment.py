#!/usr/bin/env python3
"""Safely inspect ROSA package and optional ROS command availability.

This diagnostic performs no network calls, model calls, ROS actions, daemon
startup, file writes, or credential reads. It can be run from any directory.
Use ``--ros-version 1`` or ``--ros-version 2`` to make one middleware family a
required check; otherwise missing ROS runtimes are reported as optional.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version


def module_status(name: str) -> dict[str, object]:
    available = importlib.util.find_spec(name) is not None
    return {"available": available}


def import_status(name: str) -> dict[str, object]:
    result = module_status(name)
    if not result["available"]:
        return result
    try:
        module = importlib.import_module(name)
        result["imported"] = True
        result["module"] = getattr(module, "__name__", name)
    except Exception as exc:  # diagnostic output should explain optional failures
        result["imported"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check ROSA package import and optional ROS family prerequisites without side effects."
    )
    parser.add_argument(
        "--ros-version",
        choices=("1", "2"),
        help="Require the selected ROS family instead of reporting it as optional.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "package": {},
        "ros1": {
            "required": args.ros_version == "1",
            "commands": {name: shutil.which(name) is not None for name in ("roscore", "rosrun")},
            "modules": {name: import_status(name) for name in ("rosgraph", "rospy", "rosnode", "rostopic")},
        },
        "ros2": {
            "required": args.ros_version == "2",
            "commands": {"ros2": shutil.which("ros2") is not None},
            "modules": {"rclpy": import_status("rclpy")},
        },
    }

    try:
        report["package"] = {"distribution": "jpl-rosa", "version": version("jpl-rosa")}
    except PackageNotFoundError:
        report["package"] = {
            "distribution": "jpl-rosa",
            "installed": False,
            "error": "Install jpl-rosa before using ROSA.",
        }
    try:
        import rosa  # noqa: F401

        report["package"]["imported"] = True  # type: ignore[index]
        report["package"]["exports"] = list(rosa.__all__)  # type: ignore[name-defined,index]
    except Exception as exc:
        report["package"]["imported"] = False  # type: ignore[index]
        report["package"]["error"] = f"{type(exc).__name__}: {exc}"  # type: ignore[index]

    required = report["ros1"] if args.ros_version == "1" else report["ros2"] if args.ros_version == "2" else None
    if required is not None:
        command_ok = all(required["commands"].values())  # type: ignore[union-attr]
        module_ok = all(item.get("imported", False) for item in required["modules"].values())  # type: ignore[union-attr]
        package_ok = bool(report["package"].get("imported"))  # type: ignore[union-attr]
        report["required_check"] = {"passed": package_ok and command_ok and module_ok}
    else:
        report["required_check"] = {"passed": bool(report["package"].get("imported"))}  # type: ignore[union-attr]

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["required_check"]["passed"] else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
