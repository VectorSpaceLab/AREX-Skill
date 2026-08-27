#!/usr/bin/env python3
"""Safe static checks for ASAP sim2sim/sim2real deployment.

This script intentionally does not initialize ROS2, Unitree DDS channels, MuJoCo
viewer, or motor commands. It checks import availability, config consistency,
paths, optional joystick visibility, and network-interface expectations.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Check:
    name: str
    status: str  # OK, WARN, FAIL
    detail: str


def add(checks: list[Check], name: str, status: str, detail: str) -> None:
    checks.append(Check(name=name, status=status, detail=detail))


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def load_yaml(path: Path, checks: list[Check]) -> dict[str, Any] | None:
    if not path.is_file():
        add(checks, "config.exists", "FAIL", f"Config file not found: {path}")
        return None
    if not has_module("yaml"):
        add(checks, "python.yaml", "FAIL", "PyYAML is required to parse deployment config")
        return None
    import yaml  # type: ignore

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:  # pragma: no cover - exact parser errors vary
        add(checks, "config.parse", "FAIL", f"Could not parse YAML: {exc}")
        return None
    if not isinstance(data, dict):
        add(checks, "config.parse", "FAIL", "YAML did not parse to a mapping")
        return None
    add(checks, "config.parse", "OK", f"Parsed {path}")
    return data


def resolve_repo_path(repo_root: Path, maybe_path: str | None, *, cwd: Path | None = None) -> Path | None:
    if not maybe_path:
        return None
    p = Path(maybe_path)
    if p.is_absolute():
        return p
    base = cwd if cwd is not None else repo_root
    return (base / p).resolve()


def list_len(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    return len(value) if isinstance(value, list) else None


def check_lengths(config: dict[str, Any], checks: list[Check]) -> None:
    num_motors = config.get("NUM_MOTORS")
    num_joints = config.get("NUM_JOINTS")
    if num_motors != 29 or num_joints != 29:
        add(checks, "config.dof_count", "WARN", f"Expected G1 29 DOF; got NUM_MOTORS={num_motors}, NUM_JOINTS={num_joints}")
    else:
        add(checks, "config.dof_count", "OK", "NUM_MOTORS and NUM_JOINTS are both 29")

    for key in [
        "MOTOR2JOINT",
        "JOINT2MOTOR",
        "JOINT_KP",
        "JOINT_KD",
        "MOTOR_KP",
        "MOTOR_KD",
        "DEFAULT_DOF_ANGLES",
        "DEFAULT_MOTOR_ANGLES",
        "motor_pos_lower_limit_list",
        "motor_pos_upper_limit_list",
        "motor_vel_limit_list",
        "motor_effort_limit_list",
    ]:
        n = list_len(config, key)
        if n == 29:
            add(checks, f"config.{key}.length", "OK", "length 29")
        else:
            add(checks, f"config.{key}.length", "FAIL", f"expected length 29, got {n}")


def check_required_config(config: dict[str, Any], checks: list[Check]) -> None:
    required = [
        "ROBOT_TYPE",
        "ROBOT_SCENE",
        "ROBOT",
        "ASSET_ROOT",
        "ASSET_FILE",
        "DOMAIN_ID",
        "INTERFACE",
        "USE_JOYSTICK",
        "JOYSTICK_TYPE",
        "SIMULATE_DT",
        "VIEWER_DT",
        "USE_HISTORY",
        "USE_HISTORY_LOCO",
        "USE_HISTORY_MIMIC",
        "history_config",
        "history_loco_config",
        "history_loco_height_config",
        "history_mimic_config",
        "obs_dims",
        "obs_loco_dims",
        "obs_mimic_dims",
        "obs_scales",
        "robot_dofs",
        "mimic_robot_types",
        "mimic_models",
        "start_upper_body_dof_pos",
        "motion_length_s",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        add(checks, "config.required_fields", "FAIL", "Missing: " + ", ".join(missing))
    else:
        add(checks, "config.required_fields", "OK", "All deployment fields used by inspected scripts are present")

    robot_type = config.get("ROBOT_TYPE")
    if robot_type == "g1_29dof":
        add(checks, "config.robot_type", "OK", "ROBOT_TYPE is supported by G1 command/state code")
    elif isinstance(robot_type, str) and "g1" in robot_type:
        add(checks, "config.robot_type", "WARN", f"Bridge may accept {robot_type!r}, but CommandSender/StateProcessor expect exact 'g1_29dof'")
    else:
        add(checks, "config.robot_type", "FAIL", f"Unsupported or unexpected ROBOT_TYPE={robot_type!r}")


def check_paths(repo_root: Path, config_path: Path, config: dict[str, Any], checks: list[Check]) -> None:
    config_dir = config_path.parent.resolve()
    # Config is normally sim2real/config/foo.yaml, so runtime cwd is its parent directory's parent.
    sim2real_root = config_dir.parent if config_dir.name == "config" else repo_root / "sim2real"
    for key in ["ROBOT_SCENE", "ROBOT", "ASSET_ROOT"]:
        p = resolve_repo_path(repo_root, str(config.get(key, "")), cwd=sim2real_root)
        if p and p.exists():
            add(checks, f"path.{key}", "OK", str(p.relative_to(repo_root) if p.is_relative_to(repo_root) else p))
        else:
            status = "WARN" if key == "ROBOT" else "FAIL"
            extra = "; this field is metadata-only in the inspected runtime code" if key == "ROBOT" else ""
            add(checks, f"path.{key}", status, f"Not found from sim2real cwd: {config.get(key)!r}{extra}")


def check_models(repo_root: Path, loco_model_path: str | None, mimic_model_paths: str | None, config: dict[str, Any] | None, checks: list[Check]) -> None:
    if loco_model_path:
        loco = resolve_repo_path(repo_root, loco_model_path)
        if loco and loco.is_file():
            add(checks, "model.loco", "OK", f"Found {loco_model_path}")
        else:
            add(checks, "model.loco", "FAIL", f"Locomotion model not found: {loco_model_path}")
    else:
        add(checks, "model.loco", "WARN", "No --loco-model-path provided; policy startup will require one")

    if not mimic_model_paths:
        add(checks, "model.mimic_root", "WARN", "No --mimic-model-paths provided; deepmimic policy requires it")
        return
    root = resolve_repo_path(repo_root, mimic_model_paths)
    if not root or not root.is_dir():
        add(checks, "model.mimic_root", "FAIL", f"Mimic model root not found: {mimic_model_paths}")
        return
    add(checks, "model.mimic_root", "OK", f"Found {mimic_model_paths}")

    if not config:
        return
    mimic_models = config.get("mimic_models", {})
    if not isinstance(mimic_models, dict) or not mimic_models:
        add(checks, "model.mimic_entries", "FAIL", "config mimic_models is missing or empty")
        return
    missing: list[str] = []
    for policy_name, rel in mimic_models.items():
        candidate = root / str(policy_name) / str(rel)
        if not candidate.is_file():
            missing.append(str(candidate.relative_to(repo_root) if candidate.is_relative_to(repo_root) else candidate))
    if missing:
        add(checks, "model.mimic_entries", "FAIL", "Missing mimic ONNX files: " + "; ".join(missing[:8]) + (" ..." if len(missing) > 8 else ""))
    else:
        add(checks, "model.mimic_entries", "OK", f"Found {len(mimic_models)} configured mimic ONNX files")


def iface_names() -> set[str]:
    sys_class_net = Path("/sys/class/net")
    if sys_class_net.is_dir():
        return {p.name for p in sys_class_net.iterdir()}
    out = subprocess.run(["ifconfig", "-a"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    names = set()
    for line in out.stdout.splitlines():
        if line and not line[0].isspace():
            names.add(line.split(":", 1)[0].split()[0])
    return names


def ipv4_for_iface(iface: str) -> list[str]:
    if not shutil.which("ip"):
        return []
    out = subprocess.run(["ip", "-o", "-4", "addr", "show", "dev", iface], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ips: list[str] = []
    for line in out.stdout.splitlines():
        parts = line.split()
        if "inet" in parts:
            value = parts[parts.index("inet") + 1].split("/", 1)[0]
            ips.append(value)
    return ips


def check_interface(mode: str, interface: str | None, checks: list[Check]) -> None:
    if not interface:
        add(checks, "network.interface", "WARN", "No INTERFACE configured; ChannelFactoryInitialize will use default routing")
        return
    names = iface_names()
    if interface not in names:
        add(checks, "network.interface.exists", "FAIL", f"Interface {interface!r} not found on this host")
        return
    add(checks, "network.interface.exists", "OK", f"Interface {interface!r} exists")
    ips = ipv4_for_iface(interface)
    if mode == "sim2sim":
        expected_loopbacks = {"lo", "lo0"}
        if interface in expected_loopbacks:
            add(checks, "network.sim2sim_interface", "OK", f"Using localhost interface {interface!r}")
        else:
            add(checks, "network.sim2sim_interface", "WARN", f"Sim2sim usually uses lo/lo0, not {interface!r}")
    elif mode == "sim2real":
        if interface in {"lo", "lo0"}:
            add(checks, "network.sim2real_interface", "FAIL", "Real hardware cannot use localhost interface")
        elif any(ip.startswith("192.168.123.") for ip in ips):
            add(checks, "network.sim2real_interface", "OK", f"{interface!r} has Unitree-subnet IPv4 {ips}")
        else:
            add(checks, "network.sim2real_interface", "WARN", f"{interface!r} exists but no 192.168.123.xxx IPv4 was detected: {ips or 'no IPv4 found'}")


def check_python_modules(mode: str, use_joystick: bool, checks: list[Check]) -> None:
    module_expectations = [
        ("mujoco", "required for sim2sim MuJoCo viewer/simulation"),
        ("yaml", "required for config parsing"),
        ("numpy", "required by simulator/policy math"),
        ("scipy", "required by policy mocap/rotation code"),
        ("onnxruntime", "required to load ONNX policy checkpoints"),
        ("sshkeyboard", "required for BasePolicy keyboard listener"),
        ("pygame", "required because BasePolicy imports it unconditionally and joystick mode needs it"),
        ("termcolor", "required by policy logging/debug key paths"),
        ("rclpy", "required by simulator, policy, state publisher, and logger"),
        ("unitree_sdk2py", "required by DDS bridge, low state, low command, and wireless controller"),
        ("pynput", "required by listener_deltaa.py for real-data collection"),
    ]

    for name, why in module_expectations:
        if has_module(name):
            add(checks, f"python.{name}", "OK", why)
        else:
            status = "WARN" if name == "pynput" else "FAIL"
            add(checks, f"python.{name}", status, f"Missing: {why}")


def check_joystick(enabled: bool, device_id: int | None, checks: list[Check]) -> None:
    if not enabled:
        add(checks, "joystick.enabled", "OK", "USE_JOYSTICK is disabled")
        return
    if not has_module("pygame"):
        add(checks, "joystick.pygame", "FAIL", "Cannot inspect joystick because pygame is missing")
        return
    try:
        import pygame  # type: ignore

        pygame.init()
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        if count <= 0:
            add(checks, "joystick.detected", "FAIL", "pygame found no joystick/gamepad")
        elif device_id is not None and device_id >= count:
            add(checks, "joystick.detected", "FAIL", f"JOYSTICK_DEVICE={device_id} but only {count} device(s) detected")
        else:
            add(checks, "joystick.detected", "OK", f"pygame sees {count} joystick/gamepad device(s)")
    except Exception as exc:  # pragma: no cover - host dependent
        add(checks, "joystick.detected", "FAIL", f"pygame joystick check failed: {exc}")


def check_viewer_env(mode: str, checks: list[Check]) -> None:
    if mode != "sim2sim":
        return
    display = os.environ.get("DISPLAY")
    wayland = os.environ.get("WAYLAND_DISPLAY")
    mujoco_gl = os.environ.get("MUJOCO_GL")
    if display or wayland or mujoco_gl:
        details = []
        if display:
            details.append(f"DISPLAY={display}")
        if wayland:
            details.append(f"WAYLAND_DISPLAY={wayland}")
        if mujoco_gl:
            details.append(f"MUJOCO_GL={mujoco_gl}")
        add(checks, "viewer.env", "OK", ", ".join(details))
    else:
        add(checks, "viewer.env", "WARN", "No DISPLAY/WAYLAND_DISPLAY/MUJOCO_GL detected; MuJoCo viewer may not open interactively")


def summarize(checks: Iterable[Check]) -> str:
    counts = {"OK": 0, "WARN": 0, "FAIL": 0}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    if counts["FAIL"]:
        return f"FAIL: {counts['FAIL']} fail, {counts['WARN']} warn, {counts['OK']} ok"
    if counts["WARN"]:
        return f"WARN: {counts['WARN']} warn, {counts['OK']} ok"
    return f"OK: {counts['OK']} ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe static doctor for ASAP sim2sim/sim2real deployment")
    parser.add_argument("--repo-root", default=".", help="ASAP repository root")
    parser.add_argument("--mode", choices=["sim2sim", "sim2real"], default="sim2sim")
    parser.add_argument("--config", default="sim2real/config/g1_29dof_hist.yaml", help="Deployment YAML path, absolute or relative to repo root")
    parser.add_argument("--loco-model-path", default=None, help="Locomotion ONNX path, absolute or relative to repo root")
    parser.add_argument("--mimic-model-paths", default=None, help="Mimic model root, absolute or relative to repo root")
    parser.add_argument("--interface", default=None, help="Override INTERFACE for network checks only")
    parser.add_argument("--check-joystick", action="store_true", help="Attempt pygame joystick enumeration when USE_JOYSTICK is enabled")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    checks: list[Check] = []
    repo_root = Path(args.repo_root).resolve()
    if repo_root.is_dir():
        add(checks, "repo_root.exists", "OK", str(repo_root))
    else:
        add(checks, "repo_root.exists", "FAIL", f"Repo root not found: {repo_root}")

    config_path = resolve_repo_path(repo_root, args.config) or Path(args.config).resolve()
    config = load_yaml(config_path, checks)
    use_joystick = False
    if config:
        use_joystick = bool(config.get("USE_JOYSTICK"))
        check_required_config(config, checks)
        check_lengths(config, checks)
        check_paths(repo_root, config_path, config, checks)
    check_python_modules(args.mode, use_joystick, checks)

    if config:
        interface = args.interface if args.interface is not None else config.get("INTERFACE")
        check_interface(args.mode, str(interface) if interface is not None else None, checks)
        check_viewer_env(args.mode, checks)
        check_models(repo_root, args.loco_model_path, args.mimic_model_paths, config, checks)
        if args.check_joystick or use_joystick:
            try:
                device_id = int(config.get("JOYSTICK_DEVICE", 0))
            except Exception:
                device_id = None
            check_joystick(use_joystick, device_id, checks)
    else:
        check_viewer_env(args.mode, checks)
        check_models(repo_root, args.loco_model_path, args.mimic_model_paths, None, checks)

    summary = summarize(checks)
    result = {
        "summary": summary,
        "mode": args.mode,
        "platform": platform.platform(),
        "checks": [asdict(c) for c in checks],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(summary)
        for c in checks:
            print(f"[{c.status:4}] {c.name}: {c.detail}")

    return 1 if any(c.status == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
