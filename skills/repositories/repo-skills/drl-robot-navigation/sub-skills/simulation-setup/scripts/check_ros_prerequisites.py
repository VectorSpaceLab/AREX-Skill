#!/usr/bin/env python3
"""Read-only ROS/Gazebo prerequisite and workspace configuration checker.

This checker deliberately never sources shells, starts roscore/roslaunch/Gazebo, invokes
Docker, contacts a ROS master, or imports ROS Python modules. It reports static evidence
only; a passing report is not native simulator verification.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence
from urllib.parse import urlparse


REQUIRED_COMMANDS = ("roscore", "roslaunch", "rospack", "catkin_make_isolated", "gzserver")
DEFAULT_ROS_SETUP = Path("/opt/ros/noetic/setup.bash")


def _result(name: str, status: str, detail: str) -> Dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def _workspace_results(workspace: Optional[Path]) -> List[Dict[str, str]]:
    if workspace is None:
        return [_result("workspace", "WARN", "no --workspace supplied; path checks skipped")]

    workspace = workspace.expanduser()
    results: List[Dict[str, str]] = []
    if workspace.is_dir():
        results.append(_result("workspace directory", "PASS", str(workspace)))
    else:
        return [_result("workspace directory", "FAIL", f"not a directory: {workspace}")]

    src = workspace / "src"
    if src.is_dir():
        results.append(_result("workspace src", "PASS", str(src)))
    else:
        results.append(_result("workspace src", "FAIL", f"missing: {src}"))

    setup_candidates = (
        workspace / "devel_isolated" / "setup.bash",
        workspace / "devel" / "setup.bash",
        workspace / "install_isolated" / "setup.bash",
        workspace / "install" / "setup.bash",
    )
    existing = [str(path) for path in setup_candidates if path.is_file()]
    if existing:
        results.append(_result("workspace setup", "PASS", "; ".join(existing)))
    else:
        results.append(
            _result(
                "workspace setup",
                "WARN",
                "no generated setup.bash found; run the catkin build in a supported ROS environment",
            )
        )
    return results


def _command_results(which=shutil.which) -> List[Dict[str, str]]:
    results = []
    for command in REQUIRED_COMMANDS:
        found = which(command)
        if found:
            results.append(_result(f"command:{command}", "PASS", found))
        else:
            results.append(_result(f"command:{command}", "FAIL", "not found on PATH"))
    return results


def _environment_results(env: Mapping[str, str]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    hostname = env.get("ROS_HOSTNAME", "")
    master = env.get("ROS_MASTER_URI", "")
    sim_port = env.get("ROS_PORT_SIM", "")
    resource_path = env.get("GAZEBO_RESOURCE_PATH", "")

    if hostname:
        results.append(_result("env:ROS_HOSTNAME", "PASS", hostname))
    else:
        results.append(_result("env:ROS_HOSTNAME", "WARN", "unset; required for the documented local setup"))

    if not master:
        results.append(_result("env:ROS_MASTER_URI", "FAIL", "unset; expected a reachable ROS master URI"))
    else:
        parsed = urlparse(master)
        if parsed.scheme in {"http", "https"} and parsed.hostname:
            results.append(_result("env:ROS_MASTER_URI", "PASS", master))
        else:
            results.append(_result("env:ROS_MASTER_URI", "FAIL", f"not an HTTP(S) URI: {master}"))

    if not sim_port:
        results.append(_result("env:ROS_PORT_SIM", "WARN", "unset; documented local default is 11311"))
    elif sim_port.isdigit() and 1 <= int(sim_port) <= 65535:
        results.append(_result("env:ROS_PORT_SIM", "PASS", sim_port))
    else:
        results.append(_result("env:ROS_PORT_SIM", "FAIL", f"not a valid TCP port: {sim_port}"))

    if resource_path:
        entries = [entry for entry in resource_path.split(os.pathsep) if entry]
        results.append(_result("env:GAZEBO_RESOURCE_PATH", "PASS", f"{len(entries)} non-empty path(s)"))
    else:
        results.append(
            _result(
                "env:GAZEBO_RESOURCE_PATH",
                "FAIL",
                "unset; include the scenario launch/resource directory and retain existing entries",
            )
        )

    if master and sim_port and sim_port.isdigit():
        parsed = urlparse(master)
        try:
            master_port = parsed.port
        except ValueError:
            master_port = None
            results.append(_result("ROS master/sim port", "FAIL", f"invalid port in ROS_MASTER_URI: {master}"))
        if master_port is not None and master_port != int(sim_port):
            results.append(
                _result(
                    "ROS master/sim port",
                    "FAIL",
                    f"ROS_MASTER_URI port {master_port} differs from ROS_PORT_SIM {sim_port}",
                )
            )
        elif master_port is None and not any(
            item["name"] == "ROS master/sim port" and item["status"] == "FAIL" for item in results
        ):
            results.append(_result("ROS master/sim port", "PASS", "ports agree or master URI has no explicit port"))
        elif master_port is not None:
            results.append(_result("ROS master/sim port", "PASS", "ports agree"))
    return results


def collect(workspace: Optional[Path], env: Mapping[str, str], ros_setup: Path = DEFAULT_ROS_SETUP,
            which=shutil.which) -> Dict[str, object]:
    results: List[Dict[str, str]] = []
    if ros_setup.is_file():
        results.append(_result("ROS Noetic setup", "PASS", str(ros_setup)))
    else:
        results.append(_result("ROS Noetic setup", "FAIL", f"missing: {ros_setup}"))
    results.extend(_command_results(which))
    results.extend(_workspace_results(workspace))
    results.extend(_environment_results(env))

    failures = sum(item["status"] == "FAIL" for item in results)
    warnings = sum(item["status"] == "WARN" for item in results)
    return {
        "verification_scope": "static presence, paths, and configuration only; no ROS/Gazebo process was started",
        "failures": failures,
        "warnings": warnings,
        "results": results,
    }


def _print_report(report: Mapping[str, object]) -> None:
    print("ROS/Gazebo prerequisite check (read-only)")
    print(report["verification_scope"])
    for item in report["results"]:  # type: ignore[union-attr]
        print(f"[{item['status']}] {item['name']}: {item['detail']}")
    print(f"Summary: {report['failures']} failure(s), {report['warnings']} warning(s)")


def _self_test() -> int:
    """Run parser-independent checks against a temporary, synthetic workspace."""
    with tempfile.TemporaryDirectory(prefix="simulation-setup-check-") as raw:
        workspace = Path(raw)
        (workspace / "src").mkdir()
        (workspace / "devel_isolated").mkdir()
        (workspace / "devel_isolated" / "setup.bash").write_text("# fixture\n", encoding="utf-8")
        fake_bin = {command: f"/fixture/bin/{command}" for command in REQUIRED_COMMANDS}
        report = collect(
            workspace,
            {
                "ROS_HOSTNAME": "localhost",
                "ROS_MASTER_URI": "http://localhost:11311",
                "ROS_PORT_SIM": "11311",
                "GAZEBO_RESOURCE_PATH": str(workspace / "src" / "multi_robot_scenario" / "launch"),
            },
            ros_setup=workspace / "ros-noetic-setup.bash",
            which=lambda command: fake_bin.get(command),
        )
        (workspace / "ros-noetic-setup.bash").write_text("# fixture\n", encoding="utf-8")
        report = collect(
            workspace,
            {
                "ROS_HOSTNAME": "localhost",
                "ROS_MASTER_URI": "http://localhost:11311",
                "ROS_PORT_SIM": "11311",
                "GAZEBO_RESOURCE_PATH": str(workspace / "src"),
            },
            ros_setup=workspace / "ros-noetic-setup.bash",
            which=lambda command: fake_bin.get(command),
        )
        assert report["failures"] == 0, report
        assert any(item["name"] == "workspace setup" and item["status"] == "PASS" for item in report["results"])  # type: ignore[union-attr]
    print("self-test: PASS (synthetic paths and injected command discovery; no external command run)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely check static ROS Noetic/Gazebo prerequisites; never launch a simulator."
    )
    parser.add_argument("--workspace", type=Path, help="catkin workspace to inspect (optional)")
    parser.add_argument("--ros-setup", type=Path, default=DEFAULT_ROS_SETUP,
                        help="ROS setup path to check (default: /opt/ros/noetic/setup.bash)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human-readable output")
    parser.add_argument("--self-test", action="store_true", help="run a synthetic fixture check and exit")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = collect(args.workspace, os.environ, args.ros_setup)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
