#!/usr/bin/env python3
"""Report optional SMARTS integration imports and executables without mutation.

All checks are local and read-only. The script never installs packages,
contacts a service, downloads a dataset, starts a process, or runs a benchmark.
It is safe to invoke from an arbitrary current working directory. Use
``--help`` to inspect the bounded checker options.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class Probe:
    kind: str
    name: str
    available: bool
    detail: str


IMPORTS: tuple[tuple[str, str], ...] = (
    ("core SMARTS Waymo module", "smarts.waymo"),
    ("Envision", "envision"),
    ("Panda3D", "panda3d.core"),
    ("OpenDRIVE", "opendrive2lanelet"),
    ("SUMO Python API", "sumolib"),
    ("SUMO TraCI API", "traci"),
    ("Ray", "ray"),
    ("Ray RLlib", "ray.rllib"),
    ("Torch", "torch"),
    ("TensorFlow", "tensorflow"),
    ("Waymo external package", "waymo_open_dataset"),
    ("Argoverse 2", "av2"),
    ("ROS Python package", "rospkg"),
    ("ROS package metadata", "catkin_pkg"),
    ("Diagnostic runner", "smarts.diagnostic.run"),
    ("Diagnostic CPU info", "cpuinfo"),
    ("Diagnostic report markdown", "mdutils.mdutils"),
    ("Diagnostic plotting", "matplotlib"),
    ("Visdom", "visdom"),
)

EXECUTABLES: tuple[tuple[str, str], ...] = (
    ("SUMO", "sumo"),
    ("SUMO GUI", "sumo-gui"),
    ("ROS master", "roscore"),
    ("ROS visualizer", "rviz"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON records")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero when any optional probe is unavailable",
    )
    return parser.parse_args(argv)


def probe_import(label: str, module_name: str) -> Probe:
    try:
        importlib.import_module(module_name)
    except Exception as error:  # imports can fail from a missing transitive extra
        return Probe("import", module_name, False, f"{label}: {type(error).__name__}: {error}")
    return Probe("import", module_name, True, label)


def probe_executable(label: str, executable: str) -> Probe:
    path = shutil.which(executable)
    if path is None:
        return Probe("executable", executable, False, f"{label}: not on PATH")
    return Probe("executable", executable, True, f"{label}: {path}")


def emit(probes: list[Probe], as_json: bool) -> None:
    if as_json:
        print(json.dumps([asdict(probe) for probe in probes], indent=2, sort_keys=True))
        return
    for probe in probes:
        state = "available" if probe.available else "missing/unverified"
        print(f"{state:18} {probe.kind:10} {probe.name:24} {probe.detail}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    probes = [probe_import(*item) for item in IMPORTS]
    probes.extend(probe_executable(*item) for item in EXECUTABLES)
    emit(probes, args.json)
    unavailable = sum(not probe.available for probe in probes)
    print(
        f"probes={len(probes)} available={len(probes) - unavailable} "
        f"missing_or_unverified={unavailable}",
        file=sys.stderr if args.json else sys.stdout,
    )
    return int(args.strict and unavailable > 0)


if __name__ == "__main__":
    raise SystemExit(main())
