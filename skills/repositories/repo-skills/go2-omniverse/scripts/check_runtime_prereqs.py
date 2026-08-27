#!/usr/bin/env python3
"""Read-only prerequisite report for the go2_omniverse runtime.

This helper does not launch Isaac Sim, import the repository, download assets,
change environment variables, or contact a robot. It can be run from any
working directory. Supply --isaac-venv when the Isaac Python executable is not
on PATH.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def command_output(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unavailable ({exc})"
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else f"exit={result.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-venv", type=Path, help="Optional environment root used only for file checks")
    args = parser.parse_args()

    print("go2_omniverse prerequisite report (read-only)")
    python_exe = (args.isaac_venv / "bin" / "python") if args.isaac_venv else Path(shutil.which("python") or "python")
    python_exists = python_exe.exists() if args.isaac_venv else shutil.which("python") is not None
    print(f"python_executable={python_exe}")
    print(f"python_exists={python_exists}")
    for module in ("isaacsim", "isaaclab", "torch", "rclpy"):
        if not python_exists:
            available = False
        else:
            probe = subprocess.run(
                [str(python_exe), "-I", "-c", f"import importlib.util; raise SystemExit(0 if importlib.util.find_spec({module!r}) else 1)"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            available = probe.returncode == 0
        print(f"module_{module}={available}")
    print(f"nvidia_smi={command_output(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'])}")
    for name in ("ISAAC_VENV", "ISAACLAB_PATH", "OMNI_KIT_ACCEPT_EULA", "ROS_DISTRO", "RMW_IMPLEMENTATION"):
        value = os.environ.get(name)
        print(f"{name}={'set' if value else 'unset'}")
    if args.isaac_venv:
        print(f"isaac_venv_root_exists={args.isaac_venv.is_dir()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
