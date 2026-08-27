#!/usr/bin/env python3
"""Inspect real-robot prereqs without commanding hardware.

This checker only inspects Python imports, executables, service status, and an
optional RTDE socket reachability probe. It never starts a robot, camera,
service, demo collection, or policy evaluation, and it never writes data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import socket
import subprocess
import sys
from typing import Any, Dict, List, Sequence, Tuple

REQUIRED_IMPORTS = [
    "numpy",
    "scipy",
    "cv2",
    "click",
    "pyrealsense2",
    "spnav",
    "rtde_control",
    "rtde_receive",
    "atomics",
]
OPTIONAL_IMPORTS = [
    "torch",
    "hydra",
    "dill",
    "skvideo.io",
    "av",
    "zarr",
    "numcodecs",
    "imagecodecs",
]
RECOMMENDED_EXECUTABLES = [
    "realsense-viewer",
]


def check_import(module_name: str) -> Tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        return False, str(exc)
    return True, "ok"


def check_executable(name: str) -> Tuple[bool, str]:
    path = shutil.which(name)
    if path is None:
        return False, "not found on PATH"
    return True, path


def check_spacenavd() -> Tuple[bool, str]:
    if shutil.which("systemctl") is None:
        return False, "systemctl not found; cannot inspect spacenavd"
    proc = subprocess.run(
        ["systemctl", "is-active", "spacenavd"],
        capture_output=True,
        text=True,
        check=False,
    )
    state = proc.stdout.strip() or proc.stderr.strip() or "unknown"
    if proc.returncode == 0:
        return True, f"active ({state})"
    return False, f"not active ({state})"


def check_robot_socket(host: str, port: int = 30004, timeout: float = 2.0) -> Tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"reachable on tcp/{port}"
    except OSError as exc:  # pragma: no cover - network dependent
        return False, f"not reachable on tcp/{port}: {exc}"


def as_check(kind: str, label: str, ok: bool, detail: str, blocking: bool) -> Dict[str, Any]:
    return {"kind": kind, "label": label, "ok": ok, "detail": detail, "blocking": blocking}


def emit(status: str, label: str, detail: str) -> None:
    print(f"[{status}] {label}: {detail}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check real-robot prereqs without commanding hardware.",
    )
    parser.add_argument(
        "--robot-ip",
        help="Optional UR RTDE host to probe on tcp/30004.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Socket timeout in seconds for --robot-ip.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report instead of text")
    args = parser.parse_args(argv)

    checks: List[Dict[str, Any]] = []

    for name in REQUIRED_IMPORTS:
        ok, detail = check_import(name)
        checks.append(as_check("required_import", name, ok, detail, blocking=not ok))

    for name in OPTIONAL_IMPORTS:
        ok, detail = check_import(name)
        checks.append(as_check("optional_import", name, ok, detail, blocking=False))

    for name in RECOMMENDED_EXECUTABLES:
        ok, detail = check_executable(name)
        checks.append(as_check("recommended_executable", name, ok, detail, blocking=False))

    ok, detail = check_spacenavd()
    checks.append(as_check("service", "spacenavd", ok, detail, blocking=not ok))

    if args.robot_ip:
        ok, detail = check_robot_socket(args.robot_ip, timeout=args.timeout)
        checks.append(as_check("rtde_socket", args.robot_ip, ok, detail, blocking=not ok))
    else:
        checks.append(as_check("rtde_socket", "robot-ip", False, "not supplied; socket reachability not checked", blocking=False))

    checks.append(as_check(
        "manual_safety",
        "manual",
        False,
        "emergency stop, camera cabling, workspace clearance, payload/tool state, and SpaceMouse presence still require human confirmation",
        blocking=False,
    ))

    blockers = [c for c in checks if c["blocking"]]
    report = {
        "ok": not blockers,
        "blocker_count": len(blockers),
        "checks": checks,
        "safety_note": "This checker does not start cameras, start services, command UR RTDE motion, or write data.",
    }

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print("== Live-control imports ==")
        for c in [x for x in checks if x["kind"] == "required_import"]:
            emit("OK" if c["ok"] else "FAIL", c["label"], c["detail"])

        print("== Optional eval/conversion imports ==")
        for c in [x for x in checks if x["kind"] == "optional_import"]:
            emit("OK" if c["ok"] else "WARN", c["label"], c["detail"])

        print("== Executables / service ==")
        for c in [x for x in checks if x["kind"] in {"recommended_executable", "service"}]:
            emit("OK" if c["ok"] else ("FAIL" if c["blocking"] else "WARN"), c["label"], c["detail"])

        print("== RTDE socket ==")
        for c in [x for x in checks if x["kind"] == "rtde_socket"]:
            emit("OK" if c["ok"] else ("FAIL" if c["blocking"] else "WARN"), c["label"], c["detail"])

        print("== Manual safety confirmations ==")
        for c in [x for x in checks if x["kind"] == "manual_safety"]:
            emit("WARN", c["label"], c["detail"])

        if blockers:
            print(f"Summary: {len(blockers)} blocker(s) found")
        else:
            print("Summary: no software blockers found")

    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
