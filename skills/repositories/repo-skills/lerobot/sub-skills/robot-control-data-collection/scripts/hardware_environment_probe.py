#!/usr/bin/env python3
"""Report hardware-related package/config prerequisites without opening devices."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path
from typing import Any

ROBOT_REQUIREMENTS: dict[str, list[tuple[str, str]]] = {
    "so100_follower": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk"), ("deepdiff", "deepdiff")],
    "so101_follower": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk"), ("deepdiff", "deepdiff")],
    "koch_follower": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk"), ("deepdiff", "deepdiff")],
    "bi_so_follower": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk"), ("deepdiff", "deepdiff")],
    "lekiwi": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk"), ("pyzmq", "zmq")],
    "lekiwi_client": [("pyzmq", "zmq")],
    "omx_follower": [("pyserial", "serial"), ("dynamixel-sdk", "dynamixel_sdk")],
    "hope_jr_hand": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk")],
    "hope_jr_arm": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk")],
    "reachy2": [("reachy2_sdk", "reachy2_sdk")],
    "openarm_follower": [("python-can", "can")],
    "bi_openarm_follower": [("python-can", "can")],
    "rebot_b601_follower": [("motorbridge", "motorbridge")],
    "bi_rebot_b601_follower": [("motorbridge", "motorbridge")],
    "unitree_g1": [("unitree-sdk2py", "unitree_sdk2py"), ("pyzmq", "zmq")],
}

TELEOP_REQUIREMENTS: dict[str, list[tuple[str, str]]] = {
    "so100_leader": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk")],
    "so101_leader": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk")],
    "koch_leader": [("pyserial", "serial"), ("feetech-servo-sdk", "scservo_sdk")],
    "omx_leader": [("pyserial", "serial"), ("dynamixel-sdk", "dynamixel_sdk")],
    "openarm_leader": [("python-can", "can")],
    "rebot_102_leader": [("motorbridge-smart-servo", "motorbridge_smart_servo")],
    "reachy2_teleoperator": [("reachy2_sdk", "reachy2_sdk")],
    "phone": [("hebi-py", "hebi"), ("teleop", "teleop")],
    "gamepad": [("pygame", "pygame")],
    "unitree_g1": [("pyserial", "serial")],
}

CAMERA_REQUIREMENTS: dict[str, list[tuple[str, str]]] = {
    "opencv": [("opencv-python-headless", "cv2")],
    "intelrealsense": [("pyrealsense2", "pyrealsense2")],
    "zmq": [("pyzmq", "zmq")],
    "reachy2_camera": [("reachy2_sdk", "reachy2_sdk")],
}


def _package_status(package: str, import_name: str) -> dict[str, Any]:
    # find_spec and metadata lookup do not import the module or open a device.
    importable = importlib.util.find_spec(import_name) is not None
    try:
        version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {"package": package, "import_name": import_name, "importable": importable, "version": version}


def _requirements(kind: str, selected: str | None) -> list[tuple[str, str]]:
    if not selected:
        return []
    table = {"robot": ROBOT_REQUIREMENTS, "teleop": TELEOP_REQUIREMENTS, "camera": CAMERA_REQUIREMENTS}[kind]
    return table.get(selected, [])


def _device_path_status(path_text: str | None) -> dict[str, Any] | None:
    if not path_text:
        return None
    path = Path(path_text).expanduser()
    return {"path": str(path), "exists": path.exists(), "is_char_device": path.is_char_device()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Non-opening environment probe for LeRobot hardware prerequisites."
    )
    parser.add_argument("--robot-type", help="Registered robot type; used only to select package checks")
    parser.add_argument("--teleop-type", help="Registered teleoperator type; used only to select package checks")
    parser.add_argument("--camera-type", help="Registered camera type; used only to select package checks")
    parser.add_argument("--serial-path", help="Optional path to check with stat only; no port is opened")
    parser.add_argument("--can-interface", help="Optional interface name to check under /sys/class/net only")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    requests: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, selected in (("robot", args.robot_type), ("teleop", args.teleop_type), ("camera", args.camera_type)):
        for item in _requirements(kind, selected):
            if item not in seen:
                requests.append(item)
                seen.add(item)

    result: dict[str, Any] = {
        "safe_mode": True,
        "device_opened": False,
        "network_contacted": False,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "selections": {
            "robot_type": args.robot_type,
            "teleop_type": args.teleop_type,
            "camera_type": args.camera_type,
        },
        "packages": [_package_status(package, import_name) for package, import_name in requests],
        "serial_path": _device_path_status(args.serial_path),
        "can_interface": None,
        "notes": [
            "Package checks use importlib metadata/spec lookup only; no backend module is imported.",
            "A present package or path does not prove hardware, firmware, wiring, permissions, or safety.",
            "Unknown device types produce no guessed dependency list; consult the installed config/help contract.",
        ],
    }
    if args.can_interface:
        sysfs_entry = Path("/sys/class/net") / args.can_interface
        result["can_interface"] = {
            "name": args.can_interface,
            "sysfs_entry_exists": sysfs_entry.exists(),
            "sysfs_path": str(sysfs_entry),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("SAFE PROBE: no robot, motor, camera, serial, CAN, SDK, or network device was opened.")
        print(f"Platform: {result['platform']} | Python: {result['python']}")
        for item in result["packages"]:
            state = "available" if item["importable"] else "missing"
            version = f" ({item['version']})" if item["version"] else ""
            print(f"- {item['package']} [{item['import_name']}]: {state}{version}")
        if result["serial_path"]:
            status = result["serial_path"]
            print(f"- serial path {status['path']}: exists={status['exists']} char_device={status['is_char_device']}")
        if result["can_interface"]:
            status = result["can_interface"]
            print(f"- CAN interface {status['name']}: sysfs_entry_exists={status['sysfs_entry_exists']}")
        print("Treat missing packages as a stop condition. Continue to discovery/live gates only after review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
